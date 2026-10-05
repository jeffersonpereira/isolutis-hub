-- =============================================================================
-- Parceiro de negócio como cadastro único (hub de papéis)
-- Migração 0003. Unifica `clientes` em `parceiro_negocio`: uma pessoa ou empresa existe uma vez e
-- assume papéis (cliente, fornecedor, funcionário…). Os ids dos clientes são preservados, então
-- negócios, orçamentos, lançamentos, projetos e tarefas continuam apontando para o mesmo registro.
-- DESTRUTIVA: remove a tabela `clientes` (faça backup antes). Não há reversão automática.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Pré-verificação: um cliente e um parceiro com o mesmo CPF/CNPJ precisam ser unificados à mão
--    antes (a fusão automática exigiria reescrever chaves compostas de várias tabelas).
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_conflitos text;
BEGIN
  SELECT string_agg(c.cnpj || ' (' || c.nome || ')', ', ') INTO v_conflitos
  FROM clientes c
  JOIN parceiro_negocio p ON p.cpf_cnpj = c.cnpj
  WHERE c.cnpj IS NOT NULL;
  IF v_conflitos IS NOT NULL THEN
    RAISE EXCEPTION 'Existem clientes com o mesmo CPF/CNPJ de parceiros já cadastrados: %. Unifique-os (ou ajuste o documento) e rode a migração de novo.', v_conflitos
      USING ERRCODE = 'unique_violation';
  END IF;
END
$$;

-- ---------------------------------------------------------------------------
-- 1. Papéis
-- ---------------------------------------------------------------------------
CREATE TABLE papel_parceiro (
  codigo      text        NOT NULL,
  nome        text        NOT NULL,
  ativo       boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pk_papel_parceiro PRIMARY KEY (codigo),
  CONSTRAINT uq_papel_parceiro_nome UNIQUE (nome),
  CONSTRAINT ck_papel_parceiro_codigo CHECK (codigo ~ '^[a-z][a-z_]*$'),
  CONSTRAINT ck_papel_parceiro_nome CHECK (btrim(nome) <> '')
);
COMMENT ON TABLE papel_parceiro IS 'Domínio EDITÁVEL de papéis que um parceiro pode assumir. Novos papéis entram por INSERT, sem mudar o schema.';
INSERT INTO papel_parceiro (codigo, nome) VALUES
  ('cliente', 'Cliente'),
  ('fornecedor', 'Fornecedor'),
  ('funcionario', 'Funcionário');

CREATE TABLE parceiro_papel (
  parceiro_id  uuid        NOT NULL,
  papel        text        NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pk_parceiro_papel PRIMARY KEY (parceiro_id, papel),
  CONSTRAINT fk_parceiro_papel_parceiro FOREIGN KEY (parceiro_id) REFERENCES parceiro_negocio (id) ON DELETE CASCADE,
  CONSTRAINT fk_parceiro_papel_papel FOREIGN KEY (papel) REFERENCES papel_parceiro (codigo) ON DELETE RESTRICT
);
COMMENT ON TABLE parceiro_papel IS 'Papéis assumidos por cada parceiro (N:N). Um parceiro precisa de ao menos um papel (garantido pelo backend).';
CREATE INDEX ix_parceiro_papel_papel ON parceiro_papel (papel, parceiro_id);

-- ---------------------------------------------------------------------------
-- 2. Campos que vinham de `clientes` + auditoria/versão; documento e município passam a ser opcionais
-- ---------------------------------------------------------------------------
ALTER TABLE parceiro_negocio
  ADD COLUMN segmento        text,
  ADD COLUMN contato         text,
  ADD COLUMN cargo           text,
  ADD COLUMN telefone        text,
  ADD COLUMN email           text,
  ADD COLUMN origem          text,
  ADD COLUMN obs             text,
  ADD COLUMN criado_por      uuid,
  ADD COLUMN atualizado_por  uuid,
  ADD COLUMN versao          integer NOT NULL DEFAULT 1,
  ALTER COLUMN cpf_cnpj DROP NOT NULL,
  ALTER COLUMN municipio_id DROP NOT NULL;

ALTER TABLE parceiro_negocio DROP CONSTRAINT ck_parceiro_negocio_documento;
ALTER TABLE parceiro_negocio
  ADD CONSTRAINT ck_parceiro_negocio_documento CHECK (
    cpf_cnpj IS NULL
    OR (tipo_pessoa = 'PF' AND cpf_cnpj ~ '^[0-9]{11}$')
    OR (tipo_pessoa = 'PJ' AND cpf_cnpj ~ '^[0-9]{14}$')),
  ADD CONSTRAINT ck_parceiro_negocio_origem CHECK (origem IN ('Site', 'Indicação', 'LinkedIn', 'Instagram', 'WhatsApp', 'Evento', 'Prospecção ativa', 'Outro')),
  ADD CONSTRAINT fk_parceiro_negocio_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE SET NULL,
  ADD CONSTRAINT fk_parceiro_negocio_atualizado_por FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE SET NULL;
COMMENT ON COLUMN parceiro_negocio.cpf_cnpj IS 'Só dígitos (11 PF, 14 PJ); opcional (clientes de prospecção podem não ter), único por empresa quando informado.';
COMMENT ON COLUMN parceiro_negocio.municipio_id IS 'Opcional. Vindo de clientes: preenchido quando a cidade em texto livre casou com um único município; senão o texto ficou em obs.';
COMMENT ON COLUMN parceiro_negocio.versao IS 'Concorrência otimista (mesmo contrato das demais tabelas): incrementa a cada UPDATE efetivo.';

-- auditoria e versão (mesmo contrato do set_audit, com os nomes created_at/updated_at desta tabela)
DROP TRIGGER tg_parceiro_negocio_updated ON parceiro_negocio;
CREATE FUNCTION tg_parceiro_negocio_audit() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_usuario uuid := app_usuario_id();
  v_chaves  text[] := ARRAY['created_at', 'updated_at', 'criado_por', 'atualizado_por', 'versao'];
BEGIN
  IF coalesce(current_setting('app.preservar_auditoria', true), '') = 'on' THEN
    RETURN NEW;  -- carga de dados legados: mantém os carimbos informados
  END IF;
  IF TG_OP = 'INSERT' THEN
    NEW.versao         := 1;
    NEW.created_at     := now();
    NEW.updated_at     := now();  -- como nas demais entidades, nunca fica vazio
    NEW.criado_por     := coalesce(v_usuario, NEW.criado_por);
    NEW.atualizado_por := coalesce(v_usuario, NEW.atualizado_por);
    RETURN NEW;
  END IF;
  NEW.created_at := OLD.created_at;
  IF NEW.criado_por IS NOT NULL THEN
    NEW.criado_por := OLD.criado_por;
  END IF;
  IF (to_jsonb(NEW) - v_chaves) = (to_jsonb(OLD) - v_chaves) THEN
    NEW.versao     := OLD.versao;
    NEW.updated_at := OLD.updated_at;
    RETURN NEW;
  END IF;
  NEW.versao         := OLD.versao + 1;
  NEW.updated_at     := now();
  NEW.atualizado_por := coalesce(v_usuario, NEW.atualizado_por);
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION tg_parceiro_negocio_audit() IS 'Auditoria + versão de parceiro_negocio a partir de app.usuario_id (equivalente ao set_audit das demais tabelas).';
CREATE TRIGGER tg_parceiro_negocio_audit BEFORE INSERT OR UPDATE ON parceiro_negocio
  FOR EACH ROW EXECUTE FUNCTION tg_parceiro_negocio_audit();

-- ---------------------------------------------------------------------------
-- 3. Copia os clientes (mesmo id) para parceiro_negocio, com o papel "cliente"
-- ---------------------------------------------------------------------------
INSERT INTO parceiro_negocio (
  id, company_id, tipo_pessoa, cpf_cnpj, nome, segmento, contato, cargo, telefone, email, origem, obs,
  municipio_id, created_at, updated_at, criado_por, atualizado_por, versao)
SELECT
  c.id, (SELECT id FROM companies ORDER BY created_at LIMIT 1), 'PJ', c.cnpj, left(c.nome, 150),
  c.segmento, c.contato, c.cargo, c.telefone, c.email, c.origem,
  nullif(concat_ws(E'\n', c.obs,
    CASE WHEN c.cidade IS NOT NULL AND m.municipio_id IS NULL THEN '[cidade informada: ' || c.cidade || ']' END), ''),
  m.municipio_id, c.criado_em, c.atualizado_em, c.criado_por, c.atualizado_por, c.versao
FROM clientes c
LEFT JOIN LATERAL (
  -- "Salvador", "Salvador/BA", "Salvador - BA": casa por nome (sem acento) e, se houver, pela UF; só vale se for único
  SELECT CASE WHEN count(*) = 1 THEN (array_agg(mu.id))[1] END AS municipio_id
  FROM municipio mu
  WHERE c.cidade IS NOT NULL
    AND imm_unaccent(lower(mu.nome)) = imm_unaccent(lower(btrim(regexp_replace(c.cidade, '\s*[/,-]\s*[A-Za-z]{2}\s*$', ''))))
    AND (c.cidade !~ '[/,-]\s*[A-Za-z]{2}\s*$' OR mu.uf = upper(substring(c.cidade from '([A-Za-z]{2})\s*$')))
) m ON true;

INSERT INTO parceiro_papel (parceiro_id, papel) SELECT id, 'cliente' FROM clientes;

-- ---------------------------------------------------------------------------
-- 4. Aponta as chaves estrangeiras para parceiro_negocio (a coluna continua cliente_id: é o parceiro no papel de cliente)
-- ---------------------------------------------------------------------------
ALTER TABLE negocios            DROP CONSTRAINT fk_negocios_cliente,            ADD CONSTRAINT fk_negocios_cliente            FOREIGN KEY (cliente_id) REFERENCES parceiro_negocio (id) ON DELETE RESTRICT;
ALTER TABLE orcamentos          DROP CONSTRAINT fk_orcamentos_cliente,          ADD CONSTRAINT fk_orcamentos_cliente          FOREIGN KEY (cliente_id) REFERENCES parceiro_negocio (id) ON DELETE RESTRICT;
ALTER TABLE lancamentos_receita DROP CONSTRAINT fk_lancamentos_receita_cliente, ADD CONSTRAINT fk_lancamentos_receita_cliente FOREIGN KEY (cliente_id) REFERENCES parceiro_negocio (id) ON DELETE RESTRICT;
ALTER TABLE projetos            DROP CONSTRAINT fk_projetos_cliente,            ADD CONSTRAINT fk_projetos_cliente            FOREIGN KEY (cliente_id) REFERENCES parceiro_negocio (id) ON DELETE RESTRICT;
ALTER TABLE tarefas             DROP CONSTRAINT fk_tarefas_cliente,             ADD CONSTRAINT fk_tarefas_cliente             FOREIGN KEY (cliente_id) REFERENCES parceiro_negocio (id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- 5. Regra: quem aparece como cliente precisa ter o papel "cliente"; e não perde o papel enquanto houver vínculo
-- ---------------------------------------------------------------------------
CREATE FUNCTION tg_exige_papel_cliente() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.cliente_id IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM parceiro_papel WHERE parceiro_id = NEW.cliente_id AND papel = 'cliente') THEN
    RAISE EXCEPTION 'o parceiro escolhido não tem o papel de cliente' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION tg_exige_papel_cliente() IS 'cliente_id só aceita parceiros com o papel cliente (negócios, orçamentos, lançamentos, projetos e tarefas).';
CREATE TRIGGER tg_negocios_papel_cliente            BEFORE INSERT OR UPDATE OF cliente_id ON negocios            FOR EACH ROW EXECUTE FUNCTION tg_exige_papel_cliente();
CREATE TRIGGER tg_orcamentos_papel_cliente          BEFORE INSERT OR UPDATE OF cliente_id ON orcamentos          FOR EACH ROW EXECUTE FUNCTION tg_exige_papel_cliente();
CREATE TRIGGER tg_lancamentos_receita_papel_cliente BEFORE INSERT OR UPDATE OF cliente_id ON lancamentos_receita FOR EACH ROW EXECUTE FUNCTION tg_exige_papel_cliente();
CREATE TRIGGER tg_projetos_papel_cliente            BEFORE INSERT OR UPDATE OF cliente_id ON projetos            FOR EACH ROW EXECUTE FUNCTION tg_exige_papel_cliente();
CREATE TRIGGER tg_tarefas_papel_cliente             BEFORE INSERT OR UPDATE OF cliente_id ON tarefas             FOR EACH ROW EXECUTE FUNCTION tg_exige_papel_cliente();

CREATE FUNCTION tg_protege_papel_cliente() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.papel = 'cliente' AND (
       EXISTS (SELECT 1 FROM negocios WHERE cliente_id = OLD.parceiro_id)
    OR EXISTS (SELECT 1 FROM orcamentos WHERE cliente_id = OLD.parceiro_id)
    OR EXISTS (SELECT 1 FROM lancamentos_receita WHERE cliente_id = OLD.parceiro_id)
    OR EXISTS (SELECT 1 FROM projetos WHERE cliente_id = OLD.parceiro_id)
    OR EXISTS (SELECT 1 FROM tarefas WHERE cliente_id = OLD.parceiro_id)) THEN
    RAISE EXCEPTION 'o parceiro tem negócios, orçamentos, lançamentos, projetos ou tarefas como cliente e não pode deixar de ser cliente' USING ERRCODE = 'restrict_violation';
  END IF;
  RETURN OLD;
END
$$;
CREATE TRIGGER tg_parceiro_papel_protege_cliente BEFORE DELETE ON parceiro_papel
  FOR EACH ROW EXECUTE FUNCTION tg_protege_papel_cliente();

-- ---------------------------------------------------------------------------
-- 6. A view de orçamentos lia o nome em `clientes`; recria sobre parceiro_negocio e remove `clientes`
-- ---------------------------------------------------------------------------
DROP VIEW vw_orcamentos_totais;
DROP TABLE clientes;

CREATE VIEW vw_orcamentos_totais AS
SELECT
  o.id,
  o.numero,
  o.data,
  o.validade_dias,
  (o.data + o.validade_dias)                                   AS validade_ate,
  o.status,
  (o.status = 'enviado' AND o.data + o.validade_dias < current_date) AS vencido,
  o.desconto,
  o.cliente_id,
  c.nome                                                       AS cliente_nome,
  o.negocio_id,
  o.aprovado_em,
  coalesce(t.qtd_itens, 0)::integer                            AS qtd_itens,
  coalesce(t.soma_unicos, 0)::numeric(14,2)                    AS subtotal_projeto,
  greatest(0, coalesce(t.soma_unicos, 0) - o.desconto)::numeric(14,2) AS total_projeto,
  coalesce(t.soma_mensal, 0)::numeric(14,2)                    AS total_mensal
FROM orcamentos o
JOIN parceiro_negocio c ON c.id = o.cliente_id
LEFT JOIN LATERAL (
  SELECT count(*)                                   AS qtd_itens,
         sum(i.subtotal) FILTER (WHERE NOT i.mensal) AS soma_unicos,
         sum(i.subtotal) FILTER (WHERE i.mensal)     AS soma_mensal
  FROM orcamento_itens i
  WHERE i.orcamento_id = o.id
) t ON true;
COMMENT ON VIEW vw_orcamentos_totais IS 'Orcamentos com totais: total_projeto = max(0, soma(itens unicos) - desconto); total_mensal = soma(itens mensais). vencido = enviado e data + validade_dias < current_date (usa o timezone da sessao).';

COMMENT ON TABLE parceiro_negocio IS 'Cadastro único de pessoas e empresas (hub): cada parceiro assume papéis em parceiro_papel (cliente, fornecedor, funcionário…). Substitui a antiga tabela clientes.';
