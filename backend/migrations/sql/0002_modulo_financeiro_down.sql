-- Reverte SOMENTE os objetos criados pela migração 0002 (nenhuma tabela anterior é tocada).
DROP TABLE IF EXISTS titulo_financeiro;
DROP TABLE IF EXISTS parceiro_negocio;
DROP TABLE IF EXISTS conta_bancaria;
DROP TABLE IF EXISTS plano_contas;
DROP TABLE IF EXISTS instituicao_financeira;
DROP TABLE IF EXISTS municipio;
DROP TABLE IF EXISTS companies;
DROP FUNCTION IF EXISTS tg_titulo_financeiro_regras();
DROP FUNCTION IF EXISTS tg_plano_contas_regras();
DROP FUNCTION IF EXISTS fin_touch_updated_at();
