-- Reverte a 0011 para o estado das migrações originais: natureza continua char(1) com R/D.
-- (Não restaura as seis categorias de bancos que foram alterados à mão: o repositório nunca as definiu.)
-- Nada a desfazer além do que o schema 0002 já define; a regra RN04 do trigger também já é a original.
SELECT 1;
