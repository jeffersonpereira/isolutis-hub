-- Onda 2: onboarding, TOTP/2FA e rastreamento de notificações.
-- Executado transacionalmente pelo Alembic.

-- 1. Flag de onboarding na empresa
ALTER TABLE empresa ADD COLUMN onboarding_concluido boolean NOT NULL DEFAULT false;

-- 2. Campos TOTP no usuário
ALTER TABLE usuarios ADD COLUMN totp_secret text;
ALTER TABLE usuarios ADD COLUMN totp_ativo boolean NOT NULL DEFAULT false;

-- 3. Tabela de backup codes TOTP
CREATE TABLE totp_backup_codes (
  id serial PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  codigo_hash text NOT NULL,
  usado_em timestamptz
);
CREATE INDEX ix_totp_backup_codes_usuario_id ON totp_backup_codes(usuario_id);

-- 4. Campos de rastreamento de notificações
ALTER TABLE lancamentos_receita ADD COLUMN notificado_em timestamptz;
ALTER TABLE orcamentos ADD COLUMN notificado_em timestamptz;

-- 5. Seed: marcar empresas existentes como já tendo feito onboarding
UPDATE empresa SET onboarding_concluido = true;
