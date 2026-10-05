-- =============================================================================
-- Hub Comercial iSolutis - schema inicial (PostgreSQL 16+)
-- Migração 0001. Executar DENTRO de uma transação (Alembic transactional_ddl,
-- ou psql --single-transaction / -1). O script NÃO contém BEGIN/COMMIT nem
-- comandos psql. Também evita o caractere de percentual e dois-pontos seguido
-- de nome (bind do SQLAlchemy text()) - execute via exec_driver_sql se preferir.
-- Requer PG15+ (ON DELETE SET NULL (coluna)). Vide docs/banco-de-dados.md.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Extensões (todas "trusted" no PG13+: o dono do banco consegue criar)
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS citext;    -- e-mail case-insensitive, nomes únicos
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- busca textual parcial (tarefas)
CREATE EXTENSION IF NOT EXISTS unaccent;  -- busca sem acento

-- ---------------------------------------------------------------------------
-- 1. Funções utilitárias
-- ---------------------------------------------------------------------------

-- Usuário da requisição, informado pelo backend via
--   SELECT set_config('app.usuario_id', '<uuid>', true);   -- equivale a SET LOCAL
CREATE FUNCTION app_usuario_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.usuario_id', true), '')::uuid
$$;
COMMENT ON FUNCTION app_usuario_id() IS
  'Usuario da transacao corrente (GUC app.usuario_id, definido pelo backend com set_config(..., true)). NULL se nao informado.';

-- unaccent() e STABLE; esta versao e IMMUTABLE (dicionario fixo) para poder
-- ser usada em coluna gerada e em indice.
CREATE FUNCTION imm_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS $$
  SELECT public.unaccent('public.unaccent'::regdictionary, $1)
$$;
COMMENT ON FUNCTION imm_unaccent(text) IS
  'unaccent IMMUTABLE (dicionario fixo) para colunas geradas e indices de busca.';

-- Trigger genérico de auditoria + concorrência otimista.
-- Argumentos opcionais (TG_ARGV): colunas "não-negócio" cuja mudança isolada
-- NÃO conta como edição (ex.: usuarios.ultimo_acesso) e não incrementa versao.
-- Colunas geradas são ignoradas automaticamente na comparação.
CREATE FUNCTION set_audit() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_usuario uuid := app_usuario_id();
  v_chaves  text[];
BEGIN
  v_chaves := ARRAY['criado_em', 'atualizado_em', 'criado_por', 'atualizado_por', 'versao'];
  FOR i IN 0 .. TG_NARGS - 1 LOOP
    v_chaves := v_chaves || TG_ARGV[i];
  END LOOP;
  -- colunas geradas ainda não foram recalculadas em NEW dentro de um trigger BEFORE: ignorá-las
  v_chaves := v_chaves || coalesce(
    (SELECT array_agg(a.attname::text) FROM pg_attribute a
      WHERE a.attrelid = TG_RELID AND a.attgenerated <> '' AND NOT a.attisdropped),
    ARRAY[]::text[]);

  -- Modo carga de dados legados: preserva carimbos fornecidos (app.preservar_auditoria = 'on').
  IF coalesce(current_setting('app.preservar_auditoria', true), '') = 'on' THEN
    RETURN NEW;
  END IF;

  IF TG_OP = 'INSERT' THEN
    NEW.versao         := 1;
    NEW.criado_em      := now();
    NEW.atualizado_em  := now();
    NEW.criado_por     := coalesce(v_usuario, NEW.criado_por);
    NEW.atualizado_por := coalesce(v_usuario, NEW.atualizado_por);
    RETURN NEW;
  END IF;

  -- UPDATE: criado_em imutável; criado_por imutável (só aceita virar NULL,
  -- o que acontece na ação referencial ON DELETE SET NULL de usuarios).
  NEW.criado_em := OLD.criado_em;
  IF NEW.criado_por IS NOT NULL THEN
    NEW.criado_por := OLD.criado_por;
  END IF;

  -- Nada de negócio mudou (ex.: ação referencial zerando criado_por/atualizado_por,
  -- ou UPDATE de coluna ignorada): não conta como edição.
  IF (to_jsonb(NEW) - v_chaves) = (to_jsonb(OLD) - v_chaves) THEN
    NEW.versao        := OLD.versao;
    NEW.atualizado_em := OLD.atualizado_em;
    RETURN NEW;
  END IF;

  NEW.versao         := OLD.versao + 1;
  NEW.atualizado_em  := now();
  NEW.atualizado_por := coalesce(v_usuario, NEW.atualizado_por);
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION set_audit() IS
  'Trigger BEFORE INSERT/UPDATE: mantem criado_em/atualizado_em/criado_por/atualizado_por/versao a partir de app.usuario_id. versao = OLD.versao + 1 a cada UPDATE efetivo.';

-- ---------------------------------------------------------------------------
-- 2. Equipe
-- ---------------------------------------------------------------------------
CREATE TABLE usuarios (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  email           citext      NOT NULL,
  nome            text        NOT NULL,
  senha_hash      text,
  senha_definida  boolean     GENERATED ALWAYS AS (senha_hash IS NOT NULL) STORED,
  admin           boolean     NOT NULL DEFAULT false,
  ativo           boolean     NOT NULL DEFAULT true,
  ultimo_acesso   timestamptz,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_usuarios PRIMARY KEY (id),
  CONSTRAINT uq_usuarios_email UNIQUE (email),
  CONSTRAINT ck_usuarios_email CHECK (email ~ '^[^@\s]+@[^@\s]+$'),
  CONSTRAINT ck_usuarios_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_usuarios_senha_hash CHECK (senha_hash IS NULL OR senha_hash <> '')
);
COMMENT ON TABLE usuarios IS 'Equipe/login. Unico lugar onde pessoas da equipe existem. Membro = usuario ativo. Nao se exclui usuario com historico: desative (ativo=false).';
COMMENT ON COLUMN usuarios.email IS 'citext: unico sem diferenciar maiusculas/minusculas.';
COMMENT ON COLUMN usuarios.senha_hash IS 'Hash (argon2/bcrypt) gerado pelo backend. NULL = convite ainda sem senha.';
COMMENT ON COLUMN usuarios.senha_definida IS 'Derivada: senha_hash IS NOT NULL.';
COMMENT ON COLUMN usuarios.ultimo_acesso IS 'Atualizado no login. Mudanca isolada desta coluna NAO incrementa versao nem atualizado_em.';

CREATE TABLE categorias_despesa (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  nome            citext      NOT NULL,
  ordem           integer     NOT NULL DEFAULT 0,
  ativo           boolean     NOT NULL DEFAULT true,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_categorias_despesa PRIMARY KEY (id),
  CONSTRAINT uq_categorias_despesa_nome UNIQUE (nome),
  CONSTRAINT ck_categorias_despesa_nome CHECK (btrim(nome) <> '')
);
COMMENT ON TABLE categorias_despesa IS 'Dominio EDITAVEL de categorias de despesa. Semeada com as 10 categorias do legado.';
COMMENT ON COLUMN categorias_despesa.ativo IS 'Categoria inativa some das listas de escolha, mas despesas antigas continuam referenciando-a.';

INSERT INTO categorias_despesa (nome, ordem) VALUES
  ('Servidores e infraestrutura', 1),
  ('Softwares e assinaturas',     2),
  ('Pessoal e terceiros',         3),
  ('Impostos e taxas',            4),
  ('Contabilidade',               5),
  ('Marketing e anúncios',        6),
  ('Escritório',                  7),
  ('Equipamentos',                8),
  ('Deslocamento',                9),
  ('Outros',                      10);

CREATE TABLE investidores (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  nome            citext      NOT NULL,
  usuario_id      uuid,
  ativo           boolean     NOT NULL DEFAULT true,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_investidores PRIMARY KEY (id),
  CONSTRAINT uq_investidores_nome UNIQUE (nome),
  CONSTRAINT uq_investidores_usuario UNIQUE (usuario_id),
  CONSTRAINT ck_investidores_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT fk_investidores_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);
COMMENT ON TABLE investidores IS 'Quem aporta capital: socios (ligados a um usuario) ou pessoas/entidades externas (usuario_id NULL). Evita nome livre que diverge ("Jeff"/"Jefferson").';
COMMENT ON COLUMN investidores.usuario_id IS 'Vinculo opcional com a equipe; no maximo 1 investidor por usuario.';

-- ---------------------------------------------------------------------------
-- 3. Comercial
-- ---------------------------------------------------------------------------
CREATE TABLE clientes (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  nome            text        NOT NULL,
  cnpj            text,
  segmento        text,
  contato         text,
  cargo           text,
  telefone        text,
  email           text,
  cidade          text,
  origem          text,
  obs             text,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_clientes PRIMARY KEY (id),
  CONSTRAINT ck_clientes_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_clientes_cnpj CHECK (cnpj ~ '^[0-9]{14}$'),
  CONSTRAINT ck_clientes_origem CHECK (origem IN ('Site', 'Indicação', 'LinkedIn', 'Instagram', 'WhatsApp', 'Evento', 'Prospecção ativa', 'Outro'))
);
COMMENT ON TABLE clientes IS 'Cadastro de clientes. Nao pode ser excluido se houver negocios, orcamentos, projetos ou lancamentos (FK RESTRICT).';
COMMENT ON COLUMN clientes.cnpj IS 'Somente 14 digitos (sem mascara); NULL se desconhecido. Unico quando informado.';
COMMENT ON COLUMN clientes.telefone IS 'WhatsApp/telefone em texto livre.';
CREATE UNIQUE INDEX uq_clientes_cnpj ON clientes (cnpj) WHERE cnpj IS NOT NULL;

CREATE TABLE produtos (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  nome            text          NOT NULL,
  tipo            text          NOT NULL,
  unidade         text          NOT NULL DEFAULT 'projeto',
  preco           numeric(14,2) NOT NULL DEFAULT 0,
  ativo           boolean       NOT NULL DEFAULT true,
  descricao       text,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_produtos PRIMARY KEY (id),
  CONSTRAINT ck_produtos_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_produtos_tipo CHECK (tipo IN ('projeto', 'mensal', 'consultoria', 'outro')),
  CONSTRAINT ck_produtos_unidade CHECK (btrim(unidade) <> ''),
  CONSTRAINT ck_produtos_preco CHECK (preco >= 0)
);
COMMENT ON TABLE produtos IS 'Catalogo de produtos/servicos (referencia para itens de orcamento).';
COMMENT ON COLUMN produtos.unidade IS 'Texto livre; sugestoes: projeto, mes, hora, unidade.';
COMMENT ON COLUMN produtos.preco IS 'Preco de referencia (pode ser 0); o preco efetivo fica no item do orcamento.';

CREATE TABLE negocios (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  titulo          text          NOT NULL,
  cliente_id      uuid          NOT NULL,
  etapa           text          NOT NULL DEFAULT 'lead',
  valor           numeric(14,2) NOT NULL DEFAULT 0,
  mensal          numeric(14,2) NOT NULL DEFAULT 0,
  previsao        date,
  responsavel_id  uuid,
  origem          text,
  motivo_perda    text,
  obs             text,
  fechado_em      date,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_negocios PRIMARY KEY (id),
  CONSTRAINT uq_negocios_id_cliente UNIQUE (id, cliente_id),
  CONSTRAINT ck_negocios_titulo CHECK (btrim(titulo) <> ''),
  CONSTRAINT ck_negocios_etapa CHECK (etapa IN ('lead', 'diag_agendado', 'diag_feito', 'proposta', 'negociacao', 'ganho', 'perdido')),
  CONSTRAINT ck_negocios_valor CHECK (valor >= 0),
  CONSTRAINT ck_negocios_mensal CHECK (mensal >= 0),
  CONSTRAINT ck_negocios_origem CHECK (origem IN ('Site', 'Indicação', 'LinkedIn', 'Instagram', 'WhatsApp', 'Evento', 'Prospecção ativa', 'Outro')),
  CONSTRAINT ck_negocios_motivo_perda_dominio CHECK (motivo_perda IN ('Preço', 'Prazo', 'Escolheu concorrente', 'Adiou o projeto', 'Sem resposta', 'Fora do perfil')),
  CONSTRAINT ck_negocios_motivo_perda CHECK ((etapa = 'perdido') = (motivo_perda IS NOT NULL)),
  CONSTRAINT ck_negocios_fechado_em CHECK (fechado_em IS NULL OR etapa = 'ganho'),
  CONSTRAINT fk_negocios_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT,
  CONSTRAINT fk_negocios_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios (id) ON DELETE SET NULL
);
COMMENT ON TABLE negocios IS 'Funil comercial (kanban). "faturado" do legado NAO e coluna: derivado de EXISTS(lancamentos_receita.negocio_id).';
COMMENT ON COLUMN negocios.valor IS 'Valor do projeto (unico).';
COMMENT ON COLUMN negocios.mensal IS 'Valor da manutencao mensal.';
COMMENT ON COLUMN negocios.previsao IS 'Previsao de fechamento.';
COMMENT ON COLUMN negocios.motivo_perda IS 'Obrigatorio se, e somente se, etapa = perdido.';
COMMENT ON COLUMN negocios.fechado_em IS 'Data em que virou ganho; so pode existir com etapa = ganho. O backend zera ao sair de ganho.';
COMMENT ON CONSTRAINT uq_negocios_id_cliente ON negocios IS 'Redundante com a PK; existe para as FKs compostas (negocio_id, cliente_id) que garantem negocio e filhos do mesmo cliente.';
CREATE INDEX ix_negocios_etapa_previsao ON negocios (etapa, previsao);
CREATE INDEX ix_negocios_cliente ON negocios (cliente_id);
CREATE INDEX ix_negocios_abertos_previsao ON negocios (previsao) WHERE etapa NOT IN ('ganho', 'perdido');

CREATE TABLE orcamento_sequencias (
  ano     integer NOT NULL,
  ultimo  integer NOT NULL DEFAULT 0,
  CONSTRAINT pk_orcamento_sequencias PRIMARY KEY (ano),
  CONSTRAINT ck_orcamento_sequencias_ano CHECK (ano BETWEEN 1000 AND 9999),
  CONSTRAINT ck_orcamento_sequencias_ultimo CHECK (ultimo >= 0)
);
COMMENT ON TABLE orcamento_sequencias IS 'Contador de numeracao de orcamentos por ano. Use proximo_numero_orcamento(ano); nunca escreva direto.';

CREATE FUNCTION proximo_numero_orcamento(p_ano integer DEFAULT (extract(year FROM current_date))::integer)
RETURNS text
LANGUAGE plpgsql AS $$
DECLARE
  v_ultimo integer;
BEGIN
  -- UPSERT atômico: o lock da linha serializa concorrentes até o COMMIT/ROLLBACK
  -- da transação chamadora; rollback devolve o número (sem buracos).
  INSERT INTO orcamento_sequencias AS s (ano, ultimo)
  VALUES (p_ano, 1)
  ON CONFLICT (ano) DO UPDATE SET ultimo = s.ultimo + 1
  RETURNING s.ultimo INTO v_ultimo;
  RETURN p_ano::text || '-' || lpad(v_ultimo::text, 3, '0');
END
$$;
COMMENT ON FUNCTION proximo_numero_orcamento(integer) IS
  'Gera o proximo numero AAAA-NNN do ano informado, de forma atomica (upsert com lock de linha). Chamar na MESMA transacao do INSERT do orcamento.';

CREATE TABLE orcamentos (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  numero          text          NOT NULL,
  data            date          NOT NULL DEFAULT current_date,
  validade_dias   integer       NOT NULL DEFAULT 15,
  status          text          NOT NULL DEFAULT 'rascunho',
  desconto        numeric(14,2) NOT NULL DEFAULT 0,
  obs             text,
  cliente_id      uuid          NOT NULL,
  negocio_id      uuid,
  aprovado_em     date,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_orcamentos PRIMARY KEY (id),
  CONSTRAINT uq_orcamentos_numero UNIQUE (numero),
  CONSTRAINT uq_orcamentos_id_cliente UNIQUE (id, cliente_id),
  CONSTRAINT ck_orcamentos_numero CHECK (numero ~ '^[0-9]{4}-[0-9]{3,}$'),
  CONSTRAINT ck_orcamentos_validade CHECK (validade_dias > 0),
  CONSTRAINT ck_orcamentos_status CHECK (status IN ('rascunho', 'enviado', 'aprovado', 'recusado')),
  CONSTRAINT ck_orcamentos_desconto CHECK (desconto >= 0),
  CONSTRAINT ck_orcamentos_aprovado_em CHECK (aprovado_em IS NULL OR status = 'aprovado'),
  CONSTRAINT fk_orcamentos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT,
  CONSTRAINT fk_orcamentos_negocio FOREIGN KEY (negocio_id, cliente_id) REFERENCES negocios (id, cliente_id) ON DELETE SET NULL (negocio_id)
);
COMMENT ON TABLE orcamentos IS 'Propostas comerciais. "Vencido" e derivado (vw_orcamentos_totais.vencido), nunca armazenado.';
COMMENT ON COLUMN orcamentos.numero IS 'AAAA-NNN, unico e imutavel. Se vier NULL no INSERT, o trigger gera a partir do ano de "data". Numeros informados (migracao) avancam a sequencia.';
COMMENT ON COLUMN orcamentos.desconto IS 'Desconto sobre o total do projeto (itens nao mensais). Nao afeta o total mensal.';
COMMENT ON COLUMN orcamentos.aprovado_em IS 'So existe com status = aprovado (backend zera ao sair de aprovado).';
COMMENT ON CONSTRAINT fk_orcamentos_negocio ON orcamentos IS 'FK composta: o negocio precisa ser do mesmo cliente. SET NULL apenas em negocio_id.';
CREATE INDEX ix_orcamentos_cliente ON orcamentos (cliente_id);
CREATE INDEX ix_orcamentos_negocio ON orcamentos (negocio_id) WHERE negocio_id IS NOT NULL;
CREATE INDEX ix_orcamentos_enviados ON orcamentos (data) WHERE status = 'enviado';

CREATE FUNCTION tg_orcamentos_numero() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF NEW.numero IS DISTINCT FROM OLD.numero THEN
      RAISE EXCEPTION 'numero do orcamento e imutavel' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
  END IF;

  IF NEW.numero IS NULL THEN
    NEW.numero := proximo_numero_orcamento((extract(year FROM NEW.data))::integer);
  ELSIF NEW.numero ~ '^[0-9]{4}-[0-9]+$' THEN
    -- número informado (carga legada): a sequência nunca fica atrás do maior número usado
    INSERT INTO orcamento_sequencias AS s (ano, ultimo)
    VALUES (substr(NEW.numero, 1, 4)::integer, split_part(NEW.numero, '-', 2)::integer)
    ON CONFLICT (ano) DO UPDATE SET ultimo = greatest(s.ultimo, excluded.ultimo);
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER tg_orcamentos_numero BEFORE INSERT OR UPDATE OF numero ON orcamentos
  FOR EACH ROW EXECUTE FUNCTION tg_orcamentos_numero();

CREATE TABLE orcamento_itens (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  orcamento_id    uuid          NOT NULL,
  ordem           integer       NOT NULL,
  produto_id      uuid,
  descricao       text          NOT NULL,
  qtd             numeric(12,3) NOT NULL DEFAULT 1,
  preco_unitario  numeric(14,2) NOT NULL DEFAULT 0,
  mensal          boolean       NOT NULL DEFAULT false,
  subtotal        numeric(14,2) GENERATED ALWAYS AS (round(qtd * preco_unitario, 2)) STORED,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_orcamento_itens PRIMARY KEY (id),
  CONSTRAINT uq_orcamento_itens_ordem UNIQUE (orcamento_id, ordem) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT ck_orcamento_itens_descricao CHECK (btrim(descricao) <> ''),
  CONSTRAINT ck_orcamento_itens_qtd CHECK (qtd > 0),
  CONSTRAINT ck_orcamento_itens_preco CHECK (preco_unitario >= 0),
  CONSTRAINT fk_orcamento_itens_orcamento FOREIGN KEY (orcamento_id) REFERENCES orcamentos (id) ON DELETE CASCADE,
  CONSTRAINT fk_orcamento_itens_produto FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE SET NULL
);
COMMENT ON TABLE orcamento_itens IS 'Itens do orcamento. mensal=true soma no total mensal; senao no total do projeto.';
COMMENT ON COLUMN orcamento_itens.ordem IS 'Posicao (reordenavel). UNIQUE DEFERRABLE INITIALLY DEFERRED: pode-se reordenar com varios UPDATEs na mesma transacao.';
COMMENT ON COLUMN orcamento_itens.subtotal IS 'Gerada: round(qtd * preco_unitario, 2). O arredondamento e por item; totais = soma dos subtotais.';
COMMENT ON COLUMN orcamento_itens.descricao IS 'Copia da descricao no momento do orcamento (produto_id vira NULL se o produto for excluido).';

-- ---------------------------------------------------------------------------
-- 4. Financeiro
-- ---------------------------------------------------------------------------
CREATE TABLE lancamentos_receita (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  cliente_id      uuid          NOT NULL,
  tipo            text          NOT NULL,
  descricao       text          NOT NULL,
  valor           numeric(14,2) NOT NULL,
  vencimento      date          NOT NULL,
  status          text          NOT NULL DEFAULT 'previsto',
  recebido_em     date,
  nf              text,
  negocio_id      uuid,
  orcamento_id    uuid,
  grupo_id        uuid,
  parcela         integer,
  total_parcelas  integer,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_lancamentos_receita PRIMARY KEY (id),
  CONSTRAINT uq_lancamentos_receita_grupo_parcela UNIQUE (grupo_id, parcela),
  CONSTRAINT ck_lancamentos_receita_tipo CHECK (tipo IN ('projeto', 'mensal', 'consultoria', 'outro')),
  CONSTRAINT ck_lancamentos_receita_descricao CHECK (btrim(descricao) <> ''),
  CONSTRAINT ck_lancamentos_receita_valor CHECK (valor >= 0),
  CONSTRAINT ck_lancamentos_receita_status CHECK (status IN ('previsto', 'recebido')),
  CONSTRAINT ck_lancamentos_receita_recebido CHECK ((status = 'recebido') = (recebido_em IS NOT NULL)),
  CONSTRAINT ck_lancamentos_receita_parcelas CHECK (
    (grupo_id IS NULL AND parcela IS NULL AND total_parcelas IS NULL)
    OR (grupo_id IS NOT NULL AND parcela IS NOT NULL AND total_parcelas IS NOT NULL
        AND parcela >= 1 AND parcela <= total_parcelas)),
  CONSTRAINT fk_lancamentos_receita_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT,
  CONSTRAINT fk_lancamentos_receita_negocio FOREIGN KEY (negocio_id, cliente_id) REFERENCES negocios (id, cliente_id) ON DELETE SET NULL (negocio_id),
  CONSTRAINT fk_lancamentos_receita_orcamento FOREIGN KEY (orcamento_id, cliente_id) REFERENCES orcamentos (id, cliente_id) ON DELETE SET NULL (orcamento_id)
);
COMMENT ON TABLE lancamentos_receita IS 'Contas a receber/recebidas (legado: faturamento). "Lancamento" = linha de livro-caixa com ciclo previsto -> recebido; "faturamento" seria o ato de faturar.';
COMMENT ON COLUMN lancamentos_receita.vencimento IS 'Data de vencimento/competencia (legado: data).';
COMMENT ON COLUMN lancamentos_receita.recebido_em IS 'Obrigatorio se, e somente se, status = recebido.';
COMMENT ON COLUMN lancamentos_receita.nf IS 'Numero da nota fiscal / observacao fiscal.';
COMMENT ON COLUMN lancamentos_receita.grupo_id IS 'Identifica uma SERIE gerada em lote (ex.: 12 mensalidades). UUID gerado pelo backend, um por serie e por tipo; sem tabela propria.';
COMMENT ON COLUMN lancamentos_receita.parcela IS 'Posicao na serie (1..total_parcelas). Parcela, total_parcelas e grupo_id sao todos NULL ou todos preenchidos.';
CREATE INDEX ix_lancamentos_receita_vencimento ON lancamentos_receita (vencimento);
CREATE INDEX ix_lancamentos_receita_cliente ON lancamentos_receita (cliente_id);
CREATE INDEX ix_lancamentos_receita_negocio ON lancamentos_receita (negocio_id) WHERE negocio_id IS NOT NULL;

CREATE TABLE despesas (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  data            date          NOT NULL,
  descricao       text          NOT NULL,
  valor           numeric(14,2) NOT NULL,
  categoria_id    uuid          NOT NULL,
  status          text          NOT NULL DEFAULT 'a_pagar',
  pago_em         date,
  fornecedor      text,
  obs             text,
  grupo_id        uuid,
  parcela         integer,
  total_parcelas  integer,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_despesas PRIMARY KEY (id),
  CONSTRAINT uq_despesas_grupo_parcela UNIQUE (grupo_id, parcela),
  CONSTRAINT ck_despesas_descricao CHECK (btrim(descricao) <> ''),
  CONSTRAINT ck_despesas_valor CHECK (valor >= 0),
  CONSTRAINT ck_despesas_status CHECK (status IN ('pago', 'a_pagar')),
  CONSTRAINT ck_despesas_pago CHECK ((status = 'pago') = (pago_em IS NOT NULL)),
  CONSTRAINT ck_despesas_parcelas CHECK (
    (grupo_id IS NULL AND parcela IS NULL AND total_parcelas IS NULL)
    OR (grupo_id IS NOT NULL AND parcela IS NOT NULL AND total_parcelas IS NOT NULL
        AND parcela >= 1 AND parcela <= total_parcelas)),
  CONSTRAINT fk_despesas_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_despesa (id) ON DELETE RESTRICT
);
COMMENT ON TABLE despesas IS 'Saidas da empresa (legado: hub_despesas com tipo=despesa). Investimentos ficam em investimentos.';
COMMENT ON COLUMN despesas.data IS 'Data da despesa / vencimento (quando a_pagar).';
COMMENT ON COLUMN despesas.pago_em IS 'Obrigatorio se, e somente se, status = pago.';
COMMENT ON COLUMN despesas.fornecedor IS 'Texto livre (autocomplete via SELECT DISTINCT).';
COMMENT ON COLUMN despesas.grupo_id IS 'Serie de despesas recorrentes criada em lote ("repetir todo mes por N meses").';
CREATE INDEX ix_despesas_data ON despesas (data);
CREATE INDEX ix_despesas_a_pagar ON despesas (data) WHERE status = 'a_pagar';

CREATE TABLE investimentos (
  id              uuid          NOT NULL DEFAULT gen_random_uuid(),
  data            date          NOT NULL,
  descricao       text          NOT NULL,
  valor           numeric(14,2) NOT NULL,
  investidor_id   uuid          NOT NULL,
  forma           text          NOT NULL,
  obs             text,
  criado_em       timestamptz   NOT NULL DEFAULT now(),
  atualizado_em   timestamptz   NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer       NOT NULL DEFAULT 1,
  CONSTRAINT pk_investimentos PRIMARY KEY (id),
  CONSTRAINT ck_investimentos_descricao CHECK (btrim(descricao) <> ''),
  CONSTRAINT ck_investimentos_valor CHECK (valor >= 0),
  CONSTRAINT ck_investimentos_forma CHECK (forma IN ('Dinheiro (aporte)', 'Equipamento', 'Pagamento de despesa da empresa', 'Outro')),
  CONSTRAINT fk_investimentos_investidor FOREIGN KEY (investidor_id) REFERENCES investidores (id) ON DELETE RESTRICT
);
COMMENT ON TABLE investimentos IS 'Aportes de capital dos investidores (legado: hub_despesas com tipo=investimento). Nao entram no resultado como despesa.';
CREATE INDEX ix_investimentos_data ON investimentos (data);
CREATE INDEX ix_investimentos_investidor_data ON investimentos (investidor_id, data);

-- ---------------------------------------------------------------------------
-- 5. Pós-venda
-- ---------------------------------------------------------------------------
CREATE TABLE projetos (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  titulo          text        NOT NULL,
  cliente_id      uuid        NOT NULL,
  negocio_id      uuid,
  orcamento_id    uuid,
  status          text        NOT NULL DEFAULT 'planejamento',
  responsavel_id  uuid,
  inicio          date,
  entrega         date,
  objetivo        text,
  escopo          text,
  fora_escopo     text,
  pos_entrega     text,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_projetos PRIMARY KEY (id),
  CONSTRAINT uq_projetos_negocio UNIQUE (negocio_id),
  CONSTRAINT ck_projetos_titulo CHECK (btrim(titulo) <> ''),
  CONSTRAINT ck_projetos_status CHECK (status IN ('planejamento', 'construcao', 'validacao', 'entregue', 'pausado')),
  CONSTRAINT ck_projetos_datas CHECK (inicio IS NULL OR entrega IS NULL OR entrega >= inicio),
  CONSTRAINT fk_projetos_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT,
  CONSTRAINT fk_projetos_negocio FOREIGN KEY (negocio_id, cliente_id) REFERENCES negocios (id, cliente_id) ON DELETE SET NULL (negocio_id),
  CONSTRAINT fk_projetos_orcamento FOREIGN KEY (orcamento_id, cliente_id) REFERENCES orcamentos (id, cliente_id) ON DELETE SET NULL (orcamento_id),
  CONSTRAINT fk_projetos_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios (id) ON DELETE SET NULL
);
COMMENT ON TABLE projetos IS 'Projetos de pos-venda. No maximo 1 projeto por negocio (UNIQUE; NULLs nao colidem).';
COMMENT ON COLUMN projetos.escopo IS 'Texto, 1 item por linha (edicao em textarea; sem estado por item, por isso nao normalizado).';
COMMENT ON COLUMN projetos.fora_escopo IS 'Texto livre.';
COMMENT ON COLUMN projetos.pos_entrega IS 'Texto livre. O texto padrao longo e responsabilidade do backend, sem DEFAULT no banco.';
CREATE INDEX ix_projetos_cliente ON projetos (cliente_id);

CREATE TABLE projeto_etapas (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  projeto_id      uuid        NOT NULL,
  ordem           integer     NOT NULL,
  titulo          text        NOT NULL,
  status          text        NOT NULL DEFAULT 'a_fazer',
  responsavel_id  uuid,
  inicio          date,
  fim             date,
  descricao       text,
  entregaveis     text,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_projeto_etapas PRIMARY KEY (id),
  CONSTRAINT uq_projeto_etapas_ordem UNIQUE (projeto_id, ordem) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT ck_projeto_etapas_titulo CHECK (btrim(titulo) <> ''),
  CONSTRAINT ck_projeto_etapas_status CHECK (status IN ('a_fazer', 'andamento', 'concluida')),
  CONSTRAINT ck_projeto_etapas_datas CHECK (inicio IS NULL OR fim IS NULL OR fim >= inicio),
  CONSTRAINT fk_projeto_etapas_projeto FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE CASCADE,
  CONSTRAINT fk_projeto_etapas_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios (id) ON DELETE SET NULL
);
COMMENT ON TABLE projeto_etapas IS 'Etapas (cronograma) do projeto. Progresso em vw_projetos_progresso.';
COMMENT ON COLUMN projeto_etapas.ordem IS 'Posicao reordenavel. UNIQUE DEFERRABLE INITIALLY DEFERRED (reordenar em varios UPDATEs na mesma transacao).';
COMMENT ON COLUMN projeto_etapas.entregaveis IS 'Texto, 1 entregavel por linha.';

-- ---------------------------------------------------------------------------
-- 6. Tarefas
-- ---------------------------------------------------------------------------
CREATE TABLE tarefas (
  id               uuid        NOT NULL DEFAULT gen_random_uuid(),
  titulo           text        NOT NULL,
  coluna           text        NOT NULL DEFAULT 'a_fazer',
  responsavel_id   uuid,
  prazo            date,
  prioridade       text        NOT NULL DEFAULT 'media',
  prioridade_ordem smallint    GENERATED ALWAYS AS (
                     CASE prioridade WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END) STORED,
  cliente_id       uuid,
  projeto_id       uuid,
  descricao        text,
  concluida_em     timestamptz,
  busca            text        GENERATED ALWAYS AS (
                     imm_unaccent(lower(titulo || ' ' || coalesce(descricao, '')))) STORED,
  criado_em        timestamptz NOT NULL DEFAULT now(),
  atualizado_em    timestamptz NOT NULL DEFAULT now(),
  criado_por       uuid,
  atualizado_por   uuid,
  versao           integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_tarefas PRIMARY KEY (id),
  CONSTRAINT ck_tarefas_titulo CHECK (btrim(titulo) <> ''),
  CONSTRAINT ck_tarefas_coluna CHECK (coluna IN ('a_fazer', 'fazendo', 'revisao', 'concluido')),
  CONSTRAINT ck_tarefas_prioridade CHECK (prioridade IN ('alta', 'media', 'baixa')),
  CONSTRAINT ck_tarefas_concluida CHECK ((coluna = 'concluido') = (concluida_em IS NOT NULL)),
  CONSTRAINT fk_tarefas_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios (id) ON DELETE SET NULL,
  CONSTRAINT fk_tarefas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE SET NULL,
  CONSTRAINT fk_tarefas_projeto FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE SET NULL
);
COMMENT ON TABLE tarefas IS 'Kanban da equipe.';
COMMENT ON COLUMN tarefas.concluida_em IS 'Obrigatorio se, e somente se, coluna = concluido (backend preenche ao mover e zera ao reabrir).';
COMMENT ON COLUMN tarefas.prioridade_ordem IS 'Gerada: alta=1, media=2, baixa=3. Use em ORDER BY (a ordem alfabetica do texto estaria errada).';
COMMENT ON COLUMN tarefas.busca IS 'Gerada: titulo + descricao, minusculo e sem acento, para ILIKE com indice trigram. Consulta: busca ILIKE (curinga || imm_unaccent(lower(termo)) || curinga), com o curinga de LIKE nas pontas.';
CREATE INDEX ix_tarefas_kanban ON tarefas (coluna, prioridade_ordem, prazo, criado_em);
CREATE INDEX ix_tarefas_abertas_responsavel ON tarefas (responsavel_id, prazo) WHERE coluna <> 'concluido';
CREATE INDEX ix_tarefas_abertas_prazo ON tarefas (prazo) WHERE coluna <> 'concluido' AND prazo IS NOT NULL;
CREATE INDEX ix_tarefas_concluidas_recentes ON tarefas (concluida_em DESC) WHERE coluna = 'concluido';
CREATE INDEX ix_tarefas_busca ON tarefas USING gin (busca gin_trgm_ops);

CREATE TABLE tarefa_checklist (
  id              uuid        NOT NULL DEFAULT gen_random_uuid(),
  tarefa_id       uuid        NOT NULL,
  ordem           integer     NOT NULL,
  texto           text        NOT NULL,
  feito           boolean     NOT NULL DEFAULT false,
  criado_em       timestamptz NOT NULL DEFAULT now(),
  atualizado_em   timestamptz NOT NULL DEFAULT now(),
  criado_por      uuid,
  atualizado_por  uuid,
  versao          integer     NOT NULL DEFAULT 1,
  CONSTRAINT pk_tarefa_checklist PRIMARY KEY (id),
  CONSTRAINT uq_tarefa_checklist_ordem UNIQUE (tarefa_id, ordem) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT ck_tarefa_checklist_texto CHECK (btrim(texto) <> ''),
  CONSTRAINT fk_tarefa_checklist_tarefa FOREIGN KEY (tarefa_id) REFERENCES tarefas (id) ON DELETE CASCADE
);
COMMENT ON TABLE tarefa_checklist IS 'Itens de checklist da tarefa (normalizado porque cada item tem estado: feito).';

-- ---------------------------------------------------------------------------
-- 7. Mapeamento de ids do legado (TEMPORÁRIO - remover na migração 0002 após validação)
-- ---------------------------------------------------------------------------
CREATE TABLE legado_ids (
  colecao    text        NOT NULL,
  legacy_id  text        NOT NULL,
  novo_id    uuid        NOT NULL,
  criado_em  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pk_legado_ids PRIMARY KEY (colecao, legacy_id),
  CONSTRAINT uq_legado_ids_novo UNIQUE (colecao, novo_id)
);
COMMENT ON TABLE legado_ids IS 'TEMPORARIA. Mapeia (colecao hub_*, id texto antigo) -> uuid novo para reconstruir FKs na carga. Sem FK de proposito (cobre varias tabelas). Dropar quando a migracao for validada.';

-- ---------------------------------------------------------------------------
-- 8. Auditoria: FKs criado_por/atualizado_por -> usuarios e triggers
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'usuarios', 'categorias_despesa', 'investidores', 'clientes', 'produtos', 'negocios',
    'orcamentos', 'orcamento_itens', 'lancamentos_receita', 'despesas', 'investimentos',
    'projetos', 'projeto_etapas', 'tarefas', 'tarefa_checklist'
  ] LOOP
    EXECUTE 'ALTER TABLE ' || quote_ident(t) || ' ADD CONSTRAINT ' || quote_ident('fk_' || t || '_criado_por')
         || ' FOREIGN KEY (criado_por) REFERENCES usuarios (id) ON DELETE SET NULL';
    EXECUTE 'ALTER TABLE ' || quote_ident(t) || ' ADD CONSTRAINT ' || quote_ident('fk_' || t || '_atualizado_por')
         || ' FOREIGN KEY (atualizado_por) REFERENCES usuarios (id) ON DELETE SET NULL';
    EXECUTE 'CREATE TRIGGER ' || quote_ident('tg_' || t || '_audit')
         || ' BEFORE INSERT OR UPDATE ON ' || quote_ident(t)
         || ' FOR EACH ROW EXECUTE FUNCTION set_audit()';
    EXECUTE 'COMMENT ON COLUMN ' || quote_ident(t) || '.criado_em IS ''Carimbo de criacao (imutavel; trigger set_audit).''';
    EXECUTE 'COMMENT ON COLUMN ' || quote_ident(t) || '.atualizado_em IS ''Carimbo da ultima edicao efetiva (trigger set_audit).''';
    EXECUTE 'COMMENT ON COLUMN ' || quote_ident(t) || '.criado_por IS ''Usuario criador (app.usuario_id). Imutavel; vira NULL se o usuario for excluido.''';
    EXECUTE 'COMMENT ON COLUMN ' || quote_ident(t) || '.atualizado_por IS ''Usuario da ultima edicao (app.usuario_id).''';
    EXECUTE 'COMMENT ON COLUMN ' || quote_ident(t) || '.versao IS ''Concorrencia otimista: UPDATE ... WHERE id = x AND versao = v; o trigger incrementa a cada UPDATE efetivo.''';
  END LOOP;
END
$$;

-- usuarios.ultimo_acesso não conta como edição (login não deve gerar conflito de versão)
DROP TRIGGER tg_usuarios_audit ON usuarios;
CREATE TRIGGER tg_usuarios_audit BEFORE INSERT OR UPDATE ON usuarios
  FOR EACH ROW EXECUTE FUNCTION set_audit('ultimo_acesso');

-- ---------------------------------------------------------------------------
-- 9. Views
-- ---------------------------------------------------------------------------
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
JOIN clientes c ON c.id = o.cliente_id
LEFT JOIN LATERAL (
  SELECT count(*)                                   AS qtd_itens,
         sum(i.subtotal) FILTER (WHERE NOT i.mensal) AS soma_unicos,
         sum(i.subtotal) FILTER (WHERE i.mensal)     AS soma_mensal
  FROM orcamento_itens i
  WHERE i.orcamento_id = o.id
) t ON true;
COMMENT ON VIEW vw_orcamentos_totais IS 'Orcamentos com totais: total_projeto = max(0, soma(itens unicos) - desconto); total_mensal = soma(itens mensais). vencido = enviado e data + validade_dias < current_date (usa o timezone da sessao).';

CREATE VIEW vw_projetos_progresso AS
SELECT
  p.id AS projeto_id,
  count(e.id)::integer AS total_etapas,
  (count(e.id) FILTER (WHERE e.status = 'concluida'))::integer AS etapas_concluidas,
  CASE WHEN count(e.id) = 0 THEN 0
       ELSE round(100.0 * (count(e.id) FILTER (WHERE e.status = 'concluida')) / count(e.id))::integer
  END AS progresso_pct
FROM projetos p
LEFT JOIN projeto_etapas e ON e.projeto_id = p.id
GROUP BY p.id;
COMMENT ON VIEW vw_projetos_progresso IS 'Progresso do projeto = etapas concluidas / total (0 se nao ha etapas), inteiro 0..100.';
