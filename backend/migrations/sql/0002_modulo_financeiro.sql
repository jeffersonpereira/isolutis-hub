-- =============================================================================
-- Módulo financeiro (spec: plano de contas, contas bancárias, parceiros, títulos)
-- Migração 0002. Somente ACRESCENTA objetos; não altera nem remove nada existente.
-- Nomes de tabelas/colunas seguem o plan.md do módulo. Sem BEGIN/COMMIT (roda na
-- transação do Alembic) e sem percentual / dois-pontos+nome (execução direta no driver).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Empresa (o plano referencia companies.id; o sistema é de uma empresa só: a iSolutis)
-- ---------------------------------------------------------------------------
CREATE TABLE companies (
  id          uuid         NOT NULL DEFAULT gen_random_uuid(),
  nome        varchar(150) NOT NULL,
  created_at  timestamptz  NOT NULL DEFAULT now(),
  updated_at  timestamptz,
  CONSTRAINT pk_companies PRIMARY KEY (id),
  CONSTRAINT ck_companies_nome CHECK (btrim(nome) <> '')
);
COMMENT ON TABLE companies IS 'Empresas proprietárias dos dados financeiros. Hoje há uma só (iSolutis); as FKs company_id já deixam o módulo pronto para mais de uma.';
INSERT INTO companies (nome) VALUES ('iSolutis');

CREATE FUNCTION fin_touch_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION fin_touch_updated_at() IS 'BEFORE UPDATE: carimba updated_at (UTC absoluto, timestamptz).';

CREATE TRIGGER tg_companies_updated BEFORE UPDATE ON companies
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();

-- ---------------------------------------------------------------------------
-- Referências globais: municípios e instituições financeiras
-- ---------------------------------------------------------------------------
CREATE TABLE municipio (
  id          uuid         NOT NULL DEFAULT gen_random_uuid(),
  nome        varchar(150) NOT NULL,
  uf          varchar(2)   NOT NULL,
  created_at  timestamptz  NOT NULL DEFAULT now(),
  updated_at  timestamptz,
  CONSTRAINT pk_municipio PRIMARY KEY (id),
  CONSTRAINT uq_municipio_nome_uf UNIQUE (nome, uf),
  CONSTRAINT ck_municipio_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_municipio_uf CHECK (uf IN ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'))
);
COMMENT ON TABLE municipio IS 'Municípios do Brasil (carga: app.financeiro.popular). Coluna uf (no plano: "UF"; o Postgres normaliza para minúsculas).';
CREATE INDEX ix_municipio_uf_nome ON municipio (uf, nome);

CREATE TABLE instituicao_financeira (
  id          uuid         NOT NULL DEFAULT gen_random_uuid(),
  codigo      varchar(5)   NOT NULL,
  nome        varchar(150) NOT NULL,
  created_at  timestamptz  NOT NULL DEFAULT now(),
  updated_at  timestamptz,
  CONSTRAINT pk_instituicao_financeira PRIMARY KEY (id),
  CONSTRAINT uq_instituicao_financeira_codigo UNIQUE (codigo),
  CONSTRAINT ck_instituicao_financeira_codigo CHECK (codigo ~ '^[0-9]{3,5}$'),
  CONSTRAINT ck_instituicao_financeira_nome CHECK (btrim(nome) <> '')
);
COMMENT ON TABLE instituicao_financeira IS 'Bancos e instituições (código COMPE/FEBRABAN). Carga: app.financeiro.popular.';

-- ---------------------------------------------------------------------------
-- Plano de contas (RN01): hierarquia de até 3 níveis, por empresa
-- ---------------------------------------------------------------------------
CREATE TABLE plano_contas (
  id            uuid         NOT NULL DEFAULT gen_random_uuid(),
  company_id    uuid         NOT NULL,
  plano_pai_id  uuid,
  codigo        varchar(20)  NOT NULL,
  nome          varchar(150) NOT NULL,
  tipo_conta    char(1)      NOT NULL,
  natureza      char(1)      NOT NULL,
  nivel         integer      NOT NULL DEFAULT 1,
  created_at    timestamptz  NOT NULL DEFAULT now(),
  updated_at    timestamptz,
  CONSTRAINT pk_plano_contas PRIMARY KEY (id),
  CONSTRAINT uq_plano_contas_id_company UNIQUE (id, company_id),
  CONSTRAINT uq_plano_contas_company_codigo UNIQUE (company_id, codigo),
  CONSTRAINT ck_plano_contas_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_plano_contas_tipo CHECK (tipo_conta IN ('A', 'S')),
  CONSTRAINT ck_plano_contas_natureza CHECK (natureza IN ('R', 'D')),
  CONSTRAINT ck_plano_contas_nivel CHECK (nivel BETWEEN 1 AND 3),
  CONSTRAINT ck_plano_contas_raiz CHECK ((nivel = 1) = (plano_pai_id IS NULL)),
  CONSTRAINT ck_plano_contas_codigo CHECK (
    (nivel = 1 AND codigo ~ '^[0-9]+$')
    OR (nivel = 2 AND codigo ~ '^[0-9]+[.][0-9]{2}$')
    OR (nivel = 3 AND codigo ~ '^[0-9]+[.][0-9]{2}[.][0-9]{3}$')),
  CONSTRAINT ck_plano_contas_nivel3_analitico CHECK (nivel < 3 OR tipo_conta = 'A'),
  CONSTRAINT fk_plano_contas_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
  -- o pai precisa ser da mesma empresa
  CONSTRAINT fk_plano_contas_pai FOREIGN KEY (plano_pai_id, company_id) REFERENCES plano_contas (id, company_id) ON DELETE RESTRICT
);
COMMENT ON TABLE plano_contas IS 'Plano de contas contábil. plano_pai_id é NULL nas contas de nível 1 (o plano marcava NOT NULL, o que impediria criar a raiz). codigo foi acrescentado (RN01: 1, 1.01, 1.01.001) e é único por empresa.';
COMMENT ON COLUMN plano_contas.tipo_conta IS 'A = analítica (recebe lançamentos); S = sintética (agrupa, nunca recebe lançamentos).';
COMMENT ON COLUMN plano_contas.natureza IS 'R = receita; D = despesa. Herdada da conta pai.';
COMMENT ON COLUMN plano_contas.nivel IS 'Calculado pelo trigger a partir do pai (1 a 3). Nível 3 é sempre analítico.';
CREATE INDEX ix_plano_contas_pai ON plano_contas (plano_pai_id) WHERE plano_pai_id IS NOT NULL;
CREATE INDEX ix_plano_contas_company_analiticas ON plano_contas (company_id, natureza) WHERE tipo_conta = 'A';

-- ---------------------------------------------------------------------------
-- Contas bancárias (RN02)
-- ---------------------------------------------------------------------------
CREATE TABLE conta_bancaria (
  id                         uuid          NOT NULL DEFAULT gen_random_uuid(),
  company_id                 uuid          NOT NULL,
  instituicao_financeira_id  uuid          NOT NULL,
  nome                       varchar(150)  NOT NULL,
  saldo_inicial              numeric(13,2) NOT NULL DEFAULT 0.00,
  created_at                 timestamptz   NOT NULL DEFAULT now(),
  updated_at                 timestamptz,
  CONSTRAINT pk_conta_bancaria PRIMARY KEY (id),
  CONSTRAINT uq_conta_bancaria_id_company UNIQUE (id, company_id),
  CONSTRAINT ck_conta_bancaria_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT fk_conta_bancaria_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
  CONSTRAINT fk_conta_bancaria_instituicao FOREIGN KEY (instituicao_financeira_id) REFERENCES instituicao_financeira (id) ON DELETE RESTRICT
);
COMMENT ON TABLE conta_bancaria IS 'Contas bancárias da empresa. Não pode haver duas com a mesma instituição e o mesmo nome na empresa (índice abaixo, sem diferenciar maiúsculas).';
CREATE UNIQUE INDEX uq_conta_bancaria_empresa_instituicao_nome
  ON conta_bancaria (company_id, instituicao_financeira_id, lower(btrim(nome)));

-- ---------------------------------------------------------------------------
-- Parceiros de negócio
-- ---------------------------------------------------------------------------
CREATE TABLE parceiro_negocio (
  id            uuid         NOT NULL DEFAULT gen_random_uuid(),
  company_id    uuid         NOT NULL,
  tipo_pessoa   char(2)      NOT NULL DEFAULT 'PJ',
  cpf_cnpj      varchar(14)  NOT NULL,
  nome          varchar(150) NOT NULL,
  endereco      varchar(150),
  cep           varchar(8),
  municipio_id  uuid         NOT NULL,
  created_at    timestamptz  NOT NULL DEFAULT now(),
  updated_at    timestamptz,
  CONSTRAINT pk_parceiro_negocio PRIMARY KEY (id),
  CONSTRAINT uq_parceiro_negocio_id_company UNIQUE (id, company_id),
  CONSTRAINT uq_parceiro_negocio_company_documento UNIQUE (company_id, cpf_cnpj),
  CONSTRAINT ck_parceiro_negocio_tipo CHECK (tipo_pessoa IN ('PJ', 'PF')),
  CONSTRAINT ck_parceiro_negocio_documento CHECK (
    (tipo_pessoa = 'PF' AND cpf_cnpj ~ '^[0-9]{11}$') OR (tipo_pessoa = 'PJ' AND cpf_cnpj ~ '^[0-9]{14}$')),
  CONSTRAINT ck_parceiro_negocio_nome CHECK (btrim(nome) <> ''),
  CONSTRAINT ck_parceiro_negocio_cep CHECK (cep IS NULL OR cep ~ '^[0-9]{8}$'),
  CONSTRAINT fk_parceiro_negocio_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
  CONSTRAINT fk_parceiro_negocio_municipio FOREIGN KEY (municipio_id) REFERENCES municipio (id) ON DELETE RESTRICT
);
COMMENT ON TABLE parceiro_negocio IS 'Clientes, fornecedores e demais parceiros. cpf_cnpj só dígitos (11 para PF, 14 para PJ), único por empresa; os dígitos verificadores são conferidos pelo backend.';
CREATE INDEX ix_parceiro_negocio_municipio ON parceiro_negocio (municipio_id);

-- ---------------------------------------------------------------------------
-- Títulos financeiros: contas a pagar e a receber (RN03, RN04)
-- ---------------------------------------------------------------------------
CREATE TABLE titulo_financeiro (
  id                 uuid          NOT NULL DEFAULT gen_random_uuid(),
  company_id         uuid          NOT NULL,
  conta_bancaria_id  uuid          NOT NULL,
  plano_conta_id     uuid          NOT NULL,
  parceiro_id        uuid          NOT NULL,
  tipo_conta         char(1)       NOT NULL,
  data_emissao       date,
  data_vencimento    date          NOT NULL,
  valor_titulo       numeric(13,2) NOT NULL DEFAULT 0.00,
  valor_desconto     numeric(13,2) NOT NULL DEFAULT 0.00,
  valor_multa        numeric(13,2) NOT NULL DEFAULT 0.00,
  valor_juros        numeric(13,2) NOT NULL DEFAULT 0.00,
  status             char(1)       NOT NULL DEFAULT 'A',
  data_pagamento     date,
  valor_quitacao     numeric(13,2) NOT NULL DEFAULT 0.00,
  anotacao           text,
  created_at         timestamptz   NOT NULL DEFAULT now(),
  updated_at         timestamptz,
  CONSTRAINT pk_titulo_financeiro PRIMARY KEY (id),
  CONSTRAINT ck_titulo_financeiro_tipo CHECK (tipo_conta IN ('P', 'R')),
  CONSTRAINT ck_titulo_financeiro_status CHECK (status IN ('A', 'Q', 'C')),
  CONSTRAINT ck_titulo_financeiro_valores CHECK (
    valor_titulo > 0 AND valor_desconto >= 0 AND valor_multa >= 0 AND valor_juros >= 0 AND valor_quitacao >= 0),
  CONSTRAINT ck_titulo_financeiro_emissao CHECK (data_emissao IS NULL OR data_emissao <= data_vencimento),
  -- quitado <=> tem data e valor pagos
  CONSTRAINT ck_titulo_financeiro_quitacao CHECK (
    (status = 'Q' AND data_pagamento IS NOT NULL AND valor_quitacao > 0)
    OR (status <> 'Q' AND data_pagamento IS NULL AND valor_quitacao = 0)),
  CONSTRAINT fk_titulo_financeiro_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
  -- conta bancária, conta do plano e parceiro precisam ser da mesma empresa do título
  CONSTRAINT fk_titulo_financeiro_conta_bancaria FOREIGN KEY (conta_bancaria_id, company_id) REFERENCES conta_bancaria (id, company_id) ON DELETE RESTRICT,
  CONSTRAINT fk_titulo_financeiro_plano_conta FOREIGN KEY (plano_conta_id, company_id) REFERENCES plano_contas (id, company_id) ON DELETE RESTRICT,
  CONSTRAINT fk_titulo_financeiro_parceiro FOREIGN KEY (parceiro_id, company_id) REFERENCES parceiro_negocio (id, company_id) ON DELETE RESTRICT
);
COMMENT ON TABLE titulo_financeiro IS 'Contas a pagar (P) e a receber (R). Valor devido = valor_titulo - valor_desconto + valor_multa + valor_juros. Cancelado (C) não entra no fluxo de caixa.';
COMMENT ON COLUMN titulo_financeiro.tipo_conta IS 'P = a pagar; R = a receber (o plano descrevia por engano como sintética/analítica).';
COMMENT ON COLUMN titulo_financeiro.data_emissao IS 'date: o plano indicava DATETIME, que não existe no PostgreSQL; datas de negócio (emissão, vencimento, pagamento) não precisam de horário.';
CREATE INDEX ix_titulo_financeiro_vencimento ON titulo_financeiro (company_id, data_vencimento);
CREATE INDEX ix_titulo_financeiro_abertos ON titulo_financeiro (company_id, data_vencimento) WHERE status = 'A';
CREATE INDEX ix_titulo_financeiro_pagamento ON titulo_financeiro (company_id, data_pagamento) WHERE status = 'Q';
CREATE INDEX ix_titulo_financeiro_conta_bancaria ON titulo_financeiro (conta_bancaria_id);
CREATE INDEX ix_titulo_financeiro_plano_conta ON titulo_financeiro (plano_conta_id);
CREATE INDEX ix_titulo_financeiro_parceiro ON titulo_financeiro (parceiro_id);

-- ---------------------------------------------------------------------------
-- Regras que atravessam linhas (triggers)
-- ---------------------------------------------------------------------------

-- RN01: hierarquia coerente. Deriva nivel e natureza do pai e impede alterações que quebrariam os filhos
-- ou os títulos já lançados.
CREATE FUNCTION tg_plano_contas_regras() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_pai plano_contas%ROWTYPE;
BEGIN
  IF NEW.plano_pai_id IS NULL THEN
    NEW.nivel := 1;
  ELSE
    SELECT * INTO v_pai FROM plano_contas WHERE id = NEW.plano_pai_id AND company_id = NEW.company_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'conta pai inexistente nesta empresa' USING ERRCODE = 'foreign_key_violation';
    END IF;
    IF v_pai.tipo_conta <> 'S' THEN
      RAISE EXCEPTION 'conta analítica não pode ter contas filhas' USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.codigo NOT LIKE v_pai.codigo || '.%' THEN
      RAISE EXCEPTION 'o código da conta filha deve começar com o código do pai (%)', v_pai.codigo USING ERRCODE = 'check_violation';
    END IF;
    NEW.nivel    := v_pai.nivel + 1;
    NEW.natureza := v_pai.natureza;  -- herança das características da conta pai
  END IF;

  IF TG_OP = 'UPDATE' THEN
    IF EXISTS (SELECT 1 FROM plano_contas f WHERE f.plano_pai_id = OLD.id)
       AND (NEW.codigo IS DISTINCT FROM OLD.codigo OR NEW.natureza IS DISTINCT FROM OLD.natureza
            OR NEW.plano_pai_id IS DISTINCT FROM OLD.plano_pai_id) THEN
      RAISE EXCEPTION 'conta com filhas não pode mudar de código, natureza ou posição' USING ERRCODE = 'check_violation';
    END IF;
    IF NEW.tipo_conta = 'A' AND EXISTS (SELECT 1 FROM plano_contas f WHERE f.plano_pai_id = OLD.id) THEN
      RAISE EXCEPTION 'conta com filhas deve ser sintética' USING ERRCODE = 'check_violation';
    END IF;
    IF EXISTS (SELECT 1 FROM titulo_financeiro t WHERE t.plano_conta_id = OLD.id)
       AND (NEW.tipo_conta = 'S' OR NEW.natureza IS DISTINCT FROM OLD.natureza) THEN
      RAISE EXCEPTION 'conta com títulos lançados deve continuar analítica e com a mesma natureza' USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION tg_plano_contas_regras() IS 'RN01: nivel/natureza herdados do pai, código com prefixo do pai, pai sintético, filhos e títulos protegidos.';
CREATE TRIGGER tg_plano_contas_regras BEFORE INSERT OR UPDATE ON plano_contas
  FOR EACH ROW EXECUTE FUNCTION tg_plano_contas_regras();
CREATE TRIGGER tg_plano_contas_updated BEFORE UPDATE ON plano_contas
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();

-- RN03 e RN04: o título só vai para conta analítica, e a natureza combina com o tipo (P -> despesa, R -> receita).
CREATE FUNCTION tg_titulo_financeiro_regras() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_conta plano_contas%ROWTYPE;
BEGIN
  SELECT * INTO v_conta FROM plano_contas WHERE id = NEW.plano_conta_id;
  IF v_conta.tipo_conta <> 'A' THEN
    RAISE EXCEPTION 'títulos só podem ser lançados em conta analítica do plano de contas' USING ERRCODE = 'check_violation';
  END IF;
  IF (NEW.tipo_conta = 'P' AND v_conta.natureza <> 'D') OR (NEW.tipo_conta = 'R' AND v_conta.natureza <> 'R') THEN
    RAISE EXCEPTION 'conta a pagar exige conta de despesa; conta a receber exige conta de receita' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
COMMENT ON FUNCTION tg_titulo_financeiro_regras() IS 'RN03 (conta analítica) e RN04 (natureza compatível com o tipo do título).';
CREATE TRIGGER tg_titulo_financeiro_regras BEFORE INSERT OR UPDATE OF plano_conta_id, tipo_conta ON titulo_financeiro
  FOR EACH ROW EXECUTE FUNCTION tg_titulo_financeiro_regras();
CREATE TRIGGER tg_titulo_financeiro_updated BEFORE UPDATE ON titulo_financeiro
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();

CREATE TRIGGER tg_conta_bancaria_updated BEFORE UPDATE ON conta_bancaria
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();
CREATE TRIGGER tg_parceiro_negocio_updated BEFORE UPDATE ON parceiro_negocio
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();
CREATE TRIGGER tg_municipio_updated BEFORE UPDATE ON municipio
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();
CREATE TRIGGER tg_instituicao_financeira_updated BEFORE UPDATE ON instituicao_financeira
  FOR EACH ROW EXECUTE FUNCTION fin_touch_updated_at();
