-- Empresa como proprietária de todo o domínio operacional (PostgreSQL 16+).
-- Executado transacionalmente pelo Alembic. Não possui downgrade seguro depois de habilitar tenants.

-- Rename preserva a identidade da empresa existente e as FKs do módulo financeiro.
ALTER TABLE companies RENAME TO empresa;
ALTER TABLE empresa RENAME CONSTRAINT pk_companies TO pk_empresa;
ALTER TABLE empresa RENAME CONSTRAINT ck_companies_nome TO ck_empresa_nome;
ALTER TABLE plano_contas RENAME COLUMN company_id TO empresa_id;
ALTER TABLE conta_bancaria RENAME COLUMN company_id TO empresa_id;
ALTER TABLE parceiro_negocio RENAME COLUMN company_id TO empresa_id;
ALTER TABLE titulo_financeiro RENAME COLUMN company_id TO empresa_id;
ALTER TABLE plano_contas RENAME CONSTRAINT uq_plano_contas_id_company TO uq_plano_contas_id_empresa;
ALTER TABLE plano_contas RENAME CONSTRAINT uq_plano_contas_company_codigo TO uq_plano_contas_empresa_codigo;
ALTER TABLE plano_contas RENAME CONSTRAINT fk_plano_contas_company TO fk_plano_contas_empresa;
ALTER TABLE plano_contas RENAME CONSTRAINT fk_plano_contas_pai TO fk_plano_contas_pai_empresa;
ALTER TABLE conta_bancaria RENAME CONSTRAINT uq_conta_bancaria_id_company TO uq_conta_bancaria_id_empresa;
ALTER TABLE conta_bancaria RENAME CONSTRAINT fk_conta_bancaria_company TO fk_conta_bancaria_empresa;
ALTER TABLE parceiro_negocio RENAME CONSTRAINT uq_parceiro_negocio_id_company TO uq_parceiro_negocio_id_empresa;
ALTER TABLE parceiro_negocio RENAME CONSTRAINT uq_parceiro_negocio_company_documento TO uq_parceiro_negocio_empresa_documento;
ALTER TABLE parceiro_negocio RENAME CONSTRAINT fk_parceiro_negocio_company TO fk_parceiro_negocio_empresa;
ALTER TABLE titulo_financeiro RENAME CONSTRAINT fk_titulo_financeiro_company TO fk_titulo_financeiro_empresa;
ALTER TABLE titulo_financeiro RENAME CONSTRAINT fk_titulo_financeiro_conta_bancaria TO fk_titulo_financeiro_conta_empresa;
ALTER TABLE titulo_financeiro RENAME CONSTRAINT fk_titulo_financeiro_plano_conta TO fk_titulo_financeiro_plano_empresa;
ALTER TABLE titulo_financeiro RENAME CONSTRAINT fk_titulo_financeiro_parceiro TO fk_titulo_financeiro_parceiro_empresa;

CREATE FUNCTION app_empresa_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.empresa_id', true), '')::uuid
$$;
COMMENT ON FUNCTION app_empresa_id() IS
  'Empresa ativa da transação (GUC app.empresa_id, definida depois da validação de membership). NULL quando não há contexto.';

CREATE TABLE usuario_empresa (
  empresa_id uuid NOT NULL REFERENCES empresa(id) ON DELETE RESTRICT,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  papel text NOT NULL,
  ativo boolean NOT NULL DEFAULT true,
  criado_em timestamptz NOT NULL DEFAULT now(),
  criado_por uuid REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT pk_usuario_empresa PRIMARY KEY (empresa_id, usuario_id),
  CONSTRAINT ck_usuario_empresa_papel CHECK (papel IN ('admin', 'membro'))
);
CREATE INDEX ix_usuario_empresa_usuario_ativo ON usuario_empresa (usuario_id, ativo, empresa_id);
INSERT INTO usuario_empresa (empresa_id, usuario_id, papel, ativo)
SELECT e.id, u.id, CASE WHEN u.admin THEN 'admin' ELSE 'membro' END, u.ativo
FROM empresa e CROSS JOIN usuarios u
WHERE e.nome = 'iSolutis';
UPDATE usuarios SET admin = false;
ALTER TABLE usuarios ALTER COLUMN admin SET DEFAULT false;

-- As relações operacionais existentes pertencem à iSolutis. As quatro tabelas financeiras
-- já tinham empresa_id (renomeado acima); as demais recebem a coluna antes do backfill.
DO $$
DECLARE
  t text;
  e uuid;
BEGIN
  SELECT id INTO STRICT e FROM empresa WHERE nome = 'iSolutis';
  FOREACH t IN ARRAY ARRAY[
    'categorias_despesa', 'investidores', 'produtos', 'negocios', 'orcamento_sequencias',
    'orcamentos', 'orcamento_itens', 'lancamentos_receita', 'despesas', 'investimentos',
    'projetos', 'projeto_etapas', 'tarefas', 'tarefa_checklist', 'parceiro_papel'
  ] LOOP
    EXECUTE format('ALTER TABLE %I ADD COLUMN empresa_id uuid', t);
    EXECUTE format('UPDATE %I SET empresa_id = %L::uuid', t, e);
    EXECUTE format('ALTER TABLE %I ALTER COLUMN empresa_id SET NOT NULL', t);
    EXECUTE format('ALTER TABLE %I ALTER COLUMN empresa_id SET DEFAULT app_empresa_id()', t);
    EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (empresa_id) REFERENCES empresa(id) ON DELETE RESTRICT', t, 'fk_' || t || '_empresa');
  END LOOP;
END
$$;

-- Existing tenant columns were non-null already; make new writes require a validated tenant context.
ALTER TABLE plano_contas ALTER COLUMN empresa_id SET DEFAULT app_empresa_id();
ALTER TABLE conta_bancaria ALTER COLUMN empresa_id SET DEFAULT app_empresa_id();
ALTER TABLE parceiro_negocio ALTER COLUMN empresa_id SET DEFAULT app_empresa_id();
ALTER TABLE titulo_financeiro ALTER COLUMN empresa_id SET DEFAULT app_empresa_id();

-- Keys needed as targets by the tenant-composite foreign keys.
ALTER TABLE categorias_despesa DROP CONSTRAINT uq_categorias_despesa_nome;
ALTER TABLE categorias_despesa ADD CONSTRAINT uq_categorias_despesa_empresa_nome UNIQUE (empresa_id, nome);
ALTER TABLE investidores DROP CONSTRAINT uq_investidores_nome;
ALTER TABLE investidores DROP CONSTRAINT uq_investidores_usuario;
ALTER TABLE investidores ADD CONSTRAINT uq_investidores_empresa_nome UNIQUE (empresa_id, nome);
CREATE UNIQUE INDEX uq_investidores_empresa_usuario ON investidores (empresa_id, usuario_id) WHERE usuario_id IS NOT NULL;
ALTER TABLE orcamento_sequencias DROP CONSTRAINT pk_orcamento_sequencias;
ALTER TABLE orcamento_sequencias ADD CONSTRAINT pk_orcamento_sequencias PRIMARY KEY (empresa_id, ano);
ALTER TABLE orcamentos DROP CONSTRAINT uq_orcamentos_numero;
ALTER TABLE orcamentos ADD CONSTRAINT uq_orcamentos_empresa_numero UNIQUE (empresa_id, numero);
ALTER TABLE projetos DROP CONSTRAINT uq_projetos_negocio;
CREATE UNIQUE INDEX uq_projetos_empresa_negocio ON projetos (empresa_id, negocio_id) WHERE negocio_id IS NOT NULL;

-- Composite keys enforce the tenant on all relationships. Keep legacy single-column FKs
-- where they encode delete behavior; the composite FKs add the tenant boundary.
ALTER TABLE categorias_despesa ADD CONSTRAINT uq_categorias_despesa_id_empresa UNIQUE (id, empresa_id);
ALTER TABLE investidores ADD CONSTRAINT uq_investidores_id_empresa UNIQUE (id, empresa_id);
ALTER TABLE produtos ADD CONSTRAINT uq_produtos_id_empresa UNIQUE (id, empresa_id);
ALTER TABLE orcamentos ADD CONSTRAINT uq_orcamentos_id_empresa UNIQUE (id, empresa_id);
ALTER TABLE orcamentos ADD CONSTRAINT uq_orcamentos_id_empresa_cliente UNIQUE (id, empresa_id, cliente_id);
ALTER TABLE negocios ADD CONSTRAINT uq_negocios_id_empresa_cliente UNIQUE (id, empresa_id, cliente_id);
ALTER TABLE projetos ADD CONSTRAINT uq_projetos_id_empresa UNIQUE (id, empresa_id);
ALTER TABLE tarefas ADD CONSTRAINT uq_tarefas_id_empresa UNIQUE (id, empresa_id);

ALTER TABLE negocios ADD CONSTRAINT fk_negocios_cliente_empresa FOREIGN KEY (cliente_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE orcamentos ADD CONSTRAINT fk_orcamentos_cliente_empresa FOREIGN KEY (cliente_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE orcamentos ADD CONSTRAINT fk_orcamentos_negocio_empresa FOREIGN KEY (negocio_id, empresa_id, cliente_id) REFERENCES negocios(id, empresa_id, cliente_id) ON DELETE SET NULL (negocio_id);
ALTER TABLE lancamentos_receita ADD CONSTRAINT fk_lancamentos_receita_cliente_empresa FOREIGN KEY (cliente_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE lancamentos_receita ADD CONSTRAINT fk_lancamentos_receita_negocio_empresa FOREIGN KEY (negocio_id, empresa_id, cliente_id) REFERENCES negocios(id, empresa_id, cliente_id) ON DELETE SET NULL (negocio_id);
ALTER TABLE lancamentos_receita ADD CONSTRAINT fk_lancamentos_receita_orcamento_empresa FOREIGN KEY (orcamento_id, empresa_id, cliente_id) REFERENCES orcamentos(id, empresa_id, cliente_id) ON DELETE SET NULL (orcamento_id);
ALTER TABLE orcamento_itens ADD CONSTRAINT fk_orcamento_itens_orcamento_empresa FOREIGN KEY (orcamento_id, empresa_id) REFERENCES orcamentos(id, empresa_id) ON DELETE CASCADE;
ALTER TABLE orcamento_itens ADD CONSTRAINT fk_orcamento_itens_produto_empresa FOREIGN KEY (produto_id, empresa_id) REFERENCES produtos(id, empresa_id) ON DELETE SET NULL (produto_id);
ALTER TABLE despesas ADD CONSTRAINT fk_despesas_categoria_empresa FOREIGN KEY (categoria_id, empresa_id) REFERENCES categorias_despesa(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE investimentos ADD CONSTRAINT fk_investimentos_investidor_empresa FOREIGN KEY (investidor_id, empresa_id) REFERENCES investidores(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE projetos ADD CONSTRAINT fk_projetos_cliente_empresa FOREIGN KEY (cliente_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE RESTRICT;
ALTER TABLE projetos ADD CONSTRAINT fk_projetos_negocio_empresa FOREIGN KEY (negocio_id, empresa_id, cliente_id) REFERENCES negocios(id, empresa_id, cliente_id) ON DELETE SET NULL (negocio_id);
ALTER TABLE projetos ADD CONSTRAINT fk_projetos_orcamento_empresa FOREIGN KEY (orcamento_id, empresa_id, cliente_id) REFERENCES orcamentos(id, empresa_id, cliente_id) ON DELETE SET NULL (orcamento_id);
ALTER TABLE projeto_etapas ADD CONSTRAINT fk_projeto_etapas_projeto_empresa FOREIGN KEY (projeto_id, empresa_id) REFERENCES projetos(id, empresa_id) ON DELETE CASCADE;
ALTER TABLE tarefas ADD CONSTRAINT fk_tarefas_cliente_empresa FOREIGN KEY (cliente_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE SET NULL (cliente_id);
ALTER TABLE tarefas ADD CONSTRAINT fk_tarefas_projeto_empresa FOREIGN KEY (projeto_id, empresa_id) REFERENCES projetos(id, empresa_id) ON DELETE SET NULL (projeto_id);
ALTER TABLE tarefa_checklist ADD CONSTRAINT fk_tarefa_checklist_tarefa_empresa FOREIGN KEY (tarefa_id, empresa_id) REFERENCES tarefas(id, empresa_id) ON DELETE CASCADE;

-- Membership is retained when deactivated so historical assignments remain valid.
ALTER TABLE negocios ADD CONSTRAINT fk_negocios_responsavel_empresa FOREIGN KEY (empresa_id, responsavel_id) REFERENCES usuario_empresa(empresa_id, usuario_id) ON DELETE SET NULL (responsavel_id);
ALTER TABLE projetos ADD CONSTRAINT fk_projetos_responsavel_empresa FOREIGN KEY (empresa_id, responsavel_id) REFERENCES usuario_empresa(empresa_id, usuario_id) ON DELETE SET NULL (responsavel_id);
ALTER TABLE projeto_etapas ADD CONSTRAINT fk_projeto_etapas_responsavel_empresa FOREIGN KEY (empresa_id, responsavel_id) REFERENCES usuario_empresa(empresa_id, usuario_id) ON DELETE SET NULL (responsavel_id);
ALTER TABLE tarefas ADD CONSTRAINT fk_tarefas_responsavel_empresa FOREIGN KEY (empresa_id, responsavel_id) REFERENCES usuario_empresa(empresa_id, usuario_id) ON DELETE SET NULL (responsavel_id);

-- Tenant-scoped partner roles and flexible partner tags.
ALTER TABLE parceiro_papel DROP CONSTRAINT pk_parceiro_papel;
ALTER TABLE parceiro_papel ADD CONSTRAINT pk_parceiro_papel PRIMARY KEY (empresa_id, parceiro_id, papel);
ALTER TABLE parceiro_papel ADD CONSTRAINT fk_parceiro_papel_parceiro_empresa FOREIGN KEY (parceiro_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE CASCADE;
CREATE INDEX ix_parceiro_papel_empresa_papel ON parceiro_papel (empresa_id, papel, parceiro_id);
CREATE TABLE tag_parceiro (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  empresa_id uuid NOT NULL DEFAULT app_empresa_id() REFERENCES empresa(id) ON DELETE RESTRICT,
  nome text NOT NULL,
  nome_normalizado text GENERATED ALWAYS AS (lower(btrim(nome))) STORED,
  ativo boolean NOT NULL DEFAULT true,
  criado_em timestamptz NOT NULL DEFAULT now(),
  atualizado_em timestamptz NOT NULL DEFAULT now(),
  criado_por uuid REFERENCES usuarios(id) ON DELETE SET NULL,
  atualizado_por uuid REFERENCES usuarios(id) ON DELETE SET NULL,
  versao integer NOT NULL DEFAULT 1,
  CONSTRAINT pk_tag_parceiro PRIMARY KEY (id),
  CONSTRAINT uq_tag_parceiro_id_empresa UNIQUE (id, empresa_id),
  CONSTRAINT uq_tag_parceiro_empresa_nome UNIQUE (empresa_id, nome_normalizado),
  CONSTRAINT ck_tag_parceiro_nome CHECK (btrim(nome) <> '' AND char_length(btrim(nome)) <= 80),
  CONSTRAINT ck_tag_parceiro_versao CHECK (versao >= 1)
);
CREATE INDEX ix_tag_parceiro_empresa_ativa_nome ON tag_parceiro (empresa_id, ativo, nome_normalizado);
CREATE TRIGGER tg_tag_parceiro_audit BEFORE INSERT OR UPDATE ON tag_parceiro
  FOR EACH ROW EXECUTE FUNCTION set_audit();
CREATE TABLE parceiro_tag (
  empresa_id uuid NOT NULL DEFAULT app_empresa_id(),
  parceiro_id uuid NOT NULL,
  tag_id uuid NOT NULL,
  criado_em timestamptz NOT NULL DEFAULT now(),
  criado_por uuid REFERENCES usuarios(id) ON DELETE SET NULL,
  CONSTRAINT pk_parceiro_tag PRIMARY KEY (empresa_id, parceiro_id, tag_id),
  CONSTRAINT fk_parceiro_tag_parceiro FOREIGN KEY (parceiro_id, empresa_id) REFERENCES parceiro_negocio(id, empresa_id) ON DELETE CASCADE,
  CONSTRAINT fk_parceiro_tag_tag FOREIGN KEY (tag_id, empresa_id) REFERENCES tag_parceiro(id, empresa_id) ON DELETE RESTRICT
);
CREATE INDEX ix_parceiro_tag_empresa_tag_parceiro ON parceiro_tag (empresa_id, tag_id, parceiro_id);

-- Replace globally unique business keys with tenant-local keys.
ALTER TABLE lancamentos_receita DROP CONSTRAINT uq_lancamentos_receita_grupo_parcela;
ALTER TABLE lancamentos_receita ADD CONSTRAINT uq_lancamentos_receita_empresa_grupo_parcela UNIQUE (empresa_id, grupo_id, parcela);
ALTER TABLE despesas DROP CONSTRAINT uq_despesas_grupo_parcela;
ALTER TABLE despesas ADD CONSTRAINT uq_despesas_empresa_grupo_parcela UNIQUE (empresa_id, grupo_id, parcela);

-- Tenant/year counter retains transactional, gap-free-on-rollback semantics.
DROP TRIGGER tg_orcamentos_numero ON orcamentos;
DROP FUNCTION tg_orcamentos_numero();
DROP FUNCTION proximo_numero_orcamento(integer);
CREATE FUNCTION proximo_numero_orcamento(p_empresa_id uuid, p_ano integer DEFAULT (extract(year FROM current_date))::integer)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE v_ultimo integer;
BEGIN
  IF p_empresa_id IS DISTINCT FROM app_empresa_id() THEN
    RAISE EXCEPTION 'empresa da numeração difere do contexto da transação' USING ERRCODE = 'insufficient_privilege';
  END IF;
  INSERT INTO orcamento_sequencias AS s (empresa_id, ano, ultimo) VALUES (p_empresa_id, p_ano, 1)
  ON CONFLICT (empresa_id, ano) DO UPDATE SET ultimo = s.ultimo + 1
  RETURNING s.ultimo INTO v_ultimo;
  RETURN p_ano::text || '-' || lpad(v_ultimo::text, 3, '0');
END
$$;
CREATE FUNCTION tg_orcamentos_numero() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF NEW.numero IS DISTINCT FROM OLD.numero THEN
      RAISE EXCEPTION 'numero do orcamento e imutavel' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.numero IS NULL THEN
    NEW.numero := proximo_numero_orcamento(NEW.empresa_id, extract(year FROM NEW.data)::integer);
  ELSIF NEW.numero ~ '^[0-9]{4}-[0-9]+$' THEN
    IF substr(NEW.numero, 1, 4)::integer <> extract(year FROM NEW.data)::integer THEN
      RAISE EXCEPTION 'ano do numero do orcamento difere da data' USING ERRCODE = 'check_violation';
    END IF;
    INSERT INTO orcamento_sequencias AS s (empresa_id, ano, ultimo)
    VALUES (NEW.empresa_id, substr(NEW.numero, 1, 4)::integer, split_part(NEW.numero, '-', 2)::integer)
    ON CONFLICT (empresa_id, ano) DO UPDATE SET ultimo = greatest(s.ultimo, excluded.ultimo);
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER tg_orcamentos_numero BEFORE INSERT OR UPDATE OF numero ON orcamentos
  FOR EACH ROW EXECUTE FUNCTION tg_orcamentos_numero();

-- Tenant-first access paths; replace old single-tenant indexes instead of duplicating them.
DROP INDEX ix_negocios_etapa_previsao;
DROP INDEX ix_negocios_cliente;
DROP INDEX ix_negocios_abertos_previsao;
CREATE INDEX ix_negocios_empresa_etapa_previsao ON negocios (empresa_id, etapa, previsao, id);
CREATE INDEX ix_negocios_empresa_abertos_previsao ON negocios (empresa_id, previsao, id) WHERE etapa NOT IN ('ganho', 'perdido');
CREATE INDEX ix_negocios_empresa_cliente ON negocios (empresa_id, cliente_id);
DROP INDEX ix_orcamentos_cliente;
DROP INDEX ix_orcamentos_negocio;
DROP INDEX ix_orcamentos_enviados;
CREATE INDEX ix_orcamentos_empresa_cliente ON orcamentos (empresa_id, cliente_id, numero DESC);
CREATE INDEX ix_orcamentos_empresa_negocio ON orcamentos (empresa_id, negocio_id) WHERE negocio_id IS NOT NULL;
CREATE INDEX ix_orcamentos_empresa_enviados ON orcamentos (empresa_id, data, id) WHERE status = 'enviado';
DROP INDEX ix_lancamentos_receita_vencimento;
DROP INDEX ix_lancamentos_receita_cliente;
DROP INDEX ix_lancamentos_receita_negocio;
CREATE INDEX ix_lancamentos_receita_empresa_vencimento ON lancamentos_receita (empresa_id, vencimento, criado_em, id);
CREATE INDEX ix_lancamentos_receita_empresa_cliente ON lancamentos_receita (empresa_id, cliente_id, vencimento);
CREATE INDEX ix_lancamentos_receita_empresa_negocio ON lancamentos_receita (empresa_id, negocio_id) WHERE negocio_id IS NOT NULL;
DROP INDEX ix_despesas_data;
DROP INDEX ix_despesas_a_pagar;
CREATE INDEX ix_despesas_empresa_data ON despesas (empresa_id, data, criado_em, id);
CREATE INDEX ix_despesas_empresa_a_pagar ON despesas (empresa_id, data) WHERE status = 'a_pagar';
DROP INDEX ix_investimentos_data;
DROP INDEX ix_investimentos_investidor_data;
CREATE INDEX ix_investimentos_empresa_data ON investimentos (empresa_id, data, id);
CREATE INDEX ix_investimentos_empresa_investidor_data ON investimentos (empresa_id, investidor_id, data);
DROP INDEX ix_projetos_cliente;
CREATE INDEX ix_projetos_empresa_entrega ON projetos (empresa_id, entrega, id);
CREATE INDEX ix_projetos_empresa_cliente ON projetos (empresa_id, cliente_id);
DROP INDEX ix_tarefas_kanban;
DROP INDEX ix_tarefas_abertas_responsavel;
DROP INDEX ix_tarefas_abertas_prazo;
DROP INDEX ix_tarefas_concluidas_recentes;
CREATE INDEX ix_tarefas_empresa_kanban ON tarefas (empresa_id, coluna, prioridade_ordem, prazo, criado_em, id);
CREATE INDEX ix_tarefas_empresa_abertas_responsavel ON tarefas (empresa_id, responsavel_id, prazo) WHERE coluna <> 'concluido';
CREATE INDEX ix_tarefas_empresa_abertas_prazo ON tarefas (empresa_id, prazo) WHERE coluna <> 'concluido' AND prazo IS NOT NULL;
CREATE INDEX ix_tarefas_empresa_concluidas_recentes ON tarefas (empresa_id, concluida_em DESC) WHERE coluna = 'concluido';

-- FK child-side indexes not created by PostgreSQL.
CREATE INDEX ix_orcamento_itens_empresa_orcamento_ordem ON orcamento_itens (empresa_id, orcamento_id, ordem);
CREATE INDEX ix_projeto_etapas_empresa_projeto_ordem ON projeto_etapas (empresa_id, projeto_id, ordem);
CREATE INDEX ix_tarefa_checklist_empresa_tarefa_ordem ON tarefa_checklist (empresa_id, tarefa_id, ordem);
CREATE INDEX ix_orcamento_itens_empresa_produto ON orcamento_itens (empresa_id, produto_id) WHERE produto_id IS NOT NULL;
CREATE INDEX ix_projetos_empresa_orcamento ON projetos (empresa_id, orcamento_id) WHERE orcamento_id IS NOT NULL;
CREATE INDEX ix_tarefas_empresa_projeto ON tarefas (empresa_id, projeto_id) WHERE projeto_id IS NOT NULL;
CREATE INDEX ix_despesas_empresa_categoria ON despesas (empresa_id, categoria_id);
CREATE INDEX ix_investimentos_empresa_investidor ON investimentos (empresa_id, investidor_id);
CREATE INDEX ix_titulo_empresa_conta ON titulo_financeiro (empresa_id, conta_bancaria_id);
CREATE INDEX ix_titulo_empresa_plano ON titulo_financeiro (empresa_id, plano_conta_id);
CREATE INDEX ix_titulo_empresa_parceiro ON titulo_financeiro (empresa_id, parceiro_id);
CREATE INDEX ix_negocios_empresa_responsavel ON negocios (empresa_id, responsavel_id) WHERE responsavel_id IS NOT NULL;
CREATE INDEX ix_projetos_empresa_responsavel ON projetos (empresa_id, responsavel_id) WHERE responsavel_id IS NOT NULL;
CREATE INDEX ix_projeto_etapas_empresa_responsavel ON projeto_etapas (empresa_id, responsavel_id) WHERE responsavel_id IS NOT NULL;
CREATE INDEX ix_tarefas_empresa_responsavel_fk ON tarefas (empresa_id, responsavel_id) WHERE responsavel_id IS NOT NULL;
CREATE INDEX ix_parceiro_empresa_nome ON parceiro_negocio (empresa_id, nome, id);

-- RLS: tenant GUC must be set for each transaction; membership lookup is scoped to identity or active tenant.
ALTER TABLE empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresa FORCE ROW LEVEL SECURITY;
CREATE POLICY empresa_membro ON empresa FOR SELECT USING (
  EXISTS (SELECT 1 FROM usuario_empresa ue WHERE ue.empresa_id = empresa.id AND ue.usuario_id = app_usuario_id() AND ue.ativo)
);
CREATE FUNCTION app_empresa_admin(p_empresa_id uuid DEFAULT app_empresa_id()) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.usuario_empresa ue
    WHERE ue.empresa_id = p_empresa_id
      AND ue.usuario_id = public.app_usuario_id()
      AND ue.ativo AND ue.papel = 'admin'
  )
$$;
REVOKE ALL ON FUNCTION app_empresa_admin(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app_empresa_admin(uuid) TO hub_runtime;
CREATE FUNCTION criar_empresa(p_nome text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_empresa uuid;
  v_usuario uuid := public.app_usuario_id();
BEGIN
  IF v_usuario IS NULL THEN
    RAISE EXCEPTION 'identidade autenticada obrigatoria' USING ERRCODE = 'insufficient_privilege';
  END IF;
  IF btrim(p_nome) = '' OR char_length(btrim(p_nome)) > 150 THEN
    RAISE EXCEPTION 'nome da empresa invalido' USING ERRCODE = 'check_violation';
  END IF;
  INSERT INTO public.empresa (nome) VALUES (btrim(p_nome)) RETURNING id INTO v_empresa;
  INSERT INTO public.usuario_empresa (empresa_id, usuario_id, papel, ativo)
  VALUES (v_empresa, v_usuario, 'admin', true);
  RETURN v_empresa;
END
$$;
REVOKE ALL ON FUNCTION criar_empresa(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION criar_empresa(text) TO hub_runtime;
CREATE POLICY empresa_admin_atualiza ON empresa FOR UPDATE
  USING (app_empresa_admin(id)) WITH CHECK (app_empresa_admin(id));
ALTER TABLE usuario_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario_empresa FORCE ROW LEVEL SECURITY;
CREATE POLICY usuario_empresa_propria_leitura ON usuario_empresa FOR SELECT
  USING (usuario_id = app_usuario_id() OR empresa_id = app_empresa_id());
CREATE POLICY usuario_empresa_admin_insere ON usuario_empresa FOR INSERT
  WITH CHECK (empresa_id = app_empresa_id() AND app_empresa_admin(empresa_id));
CREATE POLICY usuario_empresa_admin_atualiza ON usuario_empresa FOR UPDATE
  USING (empresa_id = app_empresa_id() AND app_empresa_admin(empresa_id))
  WITH CHECK (empresa_id = app_empresa_id() AND app_empresa_admin(empresa_id));
CREATE POLICY usuario_empresa_admin_remove ON usuario_empresa FOR DELETE
  USING (empresa_id = app_empresa_id() AND app_empresa_admin(empresa_id));

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'categorias_despesa', 'investidores', 'produtos', 'negocios', 'orcamento_sequencias', 'orcamentos',
    'orcamento_itens', 'lancamentos_receita', 'despesas', 'investimentos', 'projetos', 'projeto_etapas',
    'tarefas', 'tarefa_checklist', 'plano_contas', 'conta_bancaria', 'parceiro_negocio', 'parceiro_papel',
    'titulo_financeiro', 'tag_parceiro', 'parceiro_tag'
  ] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY %I ON %I USING (empresa_id = app_empresa_id()) WITH CHECK (empresa_id = app_empresa_id())', 'tenant_' || t, t);
  END LOOP;
END
$$;

-- PostgreSQL 16 views run with invoker privileges so tenant RLS is applied to underlying rows.
ALTER VIEW vw_orcamentos_totais SET (security_invoker = true);
DO $$
BEGIN
  IF to_regclass('public.vw_projetos_progresso') IS NOT NULL THEN
    EXECUTE 'ALTER VIEW vw_projetos_progresso SET (security_invoker = true)';
  END IF;
END
$$;

-- A API usa papel sem ownership/BYPASSRLS. Em produção, provisionar o mesmo papel
-- por DBA antes da migração; no Compose ele é criado pelo init script do banco.
GRANT USAGE ON SCHEMA public TO hub_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hub_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hub_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO hub_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO hub_runtime;
