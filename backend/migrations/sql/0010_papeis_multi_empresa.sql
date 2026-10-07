-- 0010 · Quatro papéis por empresa, fim do flag global usuarios.admin e criação de empresa só pelo operador.
--
-- 1. Quem era 'membro' tinha acesso comercial completo (a API não exigia papel); passa a 'comercial' para
--    ninguém perder o acesso que já usa. 'admin' permanece. Convites pendentes seguem a mesma regra.
-- 2. ck_usuario_empresa_papel aceita admin, financeiro, comercial e membro.
-- 3. usuarios.admin (sempre falso desde a 0005) é removida: a autorização usa usuario_empresa.papel.
-- 4. criar_empresa(text) deixa de ser executável pelo papel de runtime: empresas só nascem pelo script do
--    operador (credencial migradora). As políticas RLS com app_empresa_admin seguem válidas ('admin' é literal).

UPDATE usuario_empresa SET papel = 'comercial' WHERE papel = 'membro';
UPDATE convites SET papel = 'comercial' WHERE papel = 'membro' AND usado_em IS NULL;

ALTER TABLE usuario_empresa DROP CONSTRAINT ck_usuario_empresa_papel;
ALTER TABLE usuario_empresa ADD CONSTRAINT ck_usuario_empresa_papel
  CHECK (papel IN ('admin', 'financeiro', 'comercial', 'membro'));

ALTER TABLE usuarios DROP COLUMN admin;

REVOKE EXECUTE ON FUNCTION criar_empresa(text) FROM hub_runtime;
