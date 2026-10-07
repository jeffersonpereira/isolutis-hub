-- Migração 0006: tabela de convites por e-mail para ingresso na equipe.
CREATE TABLE convites (
    id          serial      PRIMARY KEY,
    token       uuid        NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    email       citext      NOT NULL,
    empresa_id  uuid        NOT NULL REFERENCES empresa(id),
    papel       varchar(16) NOT NULL,
    criado_por  uuid        NOT NULL REFERENCES usuarios(id),
    expira_em   timestamptz NOT NULL,
    usado_em    timestamptz,
    criado_em   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_convites_empresa_id ON convites(empresa_id);
CREATE INDEX ix_convites_token      ON convites(token);
