-- O papel hub_plataforma é do cluster e não é removido aqui.
DROP FUNCTION IF EXISTS plataforma_definir_membro(uuid, uuid, text, boolean);
DROP FUNCTION IF EXISTS plataforma_cancelar_convite(uuid, integer);
DROP FUNCTION IF EXISTS plataforma_convidar(uuid, text, text);
DROP FUNCTION IF EXISTS plataforma_listar_convites(uuid);
DROP FUNCTION IF EXISTS plataforma_listar_membros(uuid);
DROP FUNCTION IF EXISTS plataforma_definir_status(uuid, text);
DROP FUNCTION IF EXISTS plataforma_criar_empresa(text, text, text);
DROP FUNCTION IF EXISTS plataforma_listar_empresas(text, uuid);
DROP FUNCTION IF EXISTS plataforma_operador_atual();
DROP FUNCTION IF EXISTS eh_operador_plataforma();
GRANT EXECUTE ON FUNCTION criar_empresa(text) TO hub_runtime;
DROP TABLE IF EXISTS auditoria_plataforma;
DROP FUNCTION IF EXISTS tg_auditoria_plataforma_imutavel();
DROP TRIGGER IF EXISTS empresa_status_so_plataforma ON empresa;
DROP FUNCTION IF EXISTS tg_empresa_status_so_plataforma();
ALTER TABLE empresa DROP CONSTRAINT IF EXISTS ck_empresa_status;
ALTER TABLE empresa DROP COLUMN IF EXISTS status;
DROP TABLE IF EXISTS operador_plataforma;
