-- Reverter Onda 2 (ordem inversa da migração).

-- 4. Remover campos de rastreamento de notificações
ALTER TABLE orcamentos DROP COLUMN IF EXISTS notificado_em;
ALTER TABLE lancamentos_receita DROP COLUMN IF EXISTS notificado_em;

-- 3. Remover tabela de backup codes TOTP
DROP INDEX IF EXISTS ix_totp_backup_codes_usuario_id;
DROP TABLE IF EXISTS totp_backup_codes;

-- 2. Remover campos TOTP do usuário
ALTER TABLE usuarios DROP COLUMN IF EXISTS totp_ativo;
ALTER TABLE usuarios DROP COLUMN IF EXISTS totp_secret;

-- 1. Remover flag de onboarding da empresa
ALTER TABLE empresa DROP COLUMN IF EXISTS onboarding_concluido;
