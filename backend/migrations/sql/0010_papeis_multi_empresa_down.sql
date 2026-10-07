-- Reverte a 0010.
-- PERDA DE INFORMAÇÃO: 'financeiro' e 'comercial' voltam a 'membro' (o modelo antigo só tinha admin/membro);
-- a distinção entre os dois papéis não pode ser recuperada. Convites pendentes seguem a mesma regra.

GRANT EXECUTE ON FUNCTION criar_empresa(text) TO hub_runtime;

ALTER TABLE usuarios ADD COLUMN admin boolean NOT NULL DEFAULT false;

UPDATE usuario_empresa SET papel = 'membro' WHERE papel IN ('financeiro', 'comercial');
UPDATE convites SET papel = 'membro' WHERE papel IN ('financeiro', 'comercial') AND usado_em IS NULL;

ALTER TABLE usuario_empresa DROP CONSTRAINT ck_usuario_empresa_papel;
ALTER TABLE usuario_empresa ADD CONSTRAINT ck_usuario_empresa_papel CHECK (papel IN ('admin', 'membro'));
