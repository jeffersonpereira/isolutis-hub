-- Reverte 0001_schema_inicial.sql (executar em transação).
DROP VIEW IF EXISTS vw_projetos_progresso;
DROP VIEW IF EXISTS vw_orcamentos_totais;

DROP TABLE IF EXISTS legado_ids;
DROP TABLE IF EXISTS tarefa_checklist;
DROP TABLE IF EXISTS tarefas;
DROP TABLE IF EXISTS projeto_etapas;
DROP TABLE IF EXISTS projetos;
DROP TABLE IF EXISTS investimentos;
DROP TABLE IF EXISTS despesas;
DROP TABLE IF EXISTS lancamentos_receita;
DROP TABLE IF EXISTS orcamento_itens;
DROP TABLE IF EXISTS orcamentos;
DROP TABLE IF EXISTS orcamento_sequencias;
DROP TABLE IF EXISTS negocios;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS investidores;
DROP TABLE IF EXISTS categorias_despesa;
DROP TABLE IF EXISTS usuarios;

DROP FUNCTION IF EXISTS tg_orcamentos_numero();
DROP FUNCTION IF EXISTS proximo_numero_orcamento(integer);
DROP FUNCTION IF EXISTS set_audit();
DROP FUNCTION IF EXISTS imm_unaccent(text);
DROP FUNCTION IF EXISTS app_usuario_id();

DROP EXTENSION IF EXISTS unaccent;
DROP EXTENSION IF EXISTS pg_trgm;
DROP EXTENSION IF EXISTS citext;
