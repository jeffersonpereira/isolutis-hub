-- =============================================================================
-- Testes do schema 0001 (psql). Uso, em base VAZIA:
--   psql -h localhost -U hub -d hub_dba -f backend/tests_sql/test_schema.sql
-- Carrega o schema via \ir (caminho relativo a ESTE arquivo), insere dados de
-- exemplo e prova constraints, triggers, numeração e views.
-- Qualquer falha aborta com erro (ON_ERROR_STOP). Sucesso termina com
-- NOTICE: TODOS OS TESTES PASSARAM.
-- =============================================================================
\set ON_ERROR_STOP on
\set QUIET on
SET client_min_messages = notice;

-- 0. precondição: base vazia ---------------------------------------------------
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v')) THEN
    RAISE EXCEPTION 'a base precisa estar vazia (recrie o banco antes de rodar)';
  END IF;
END $$;

BEGIN;
\ir ../migrations/sql/0001_schema_inicial.sql
COMMIT;

-- helper: executa SQL que DEVE falhar com o SQLSTATE esperado -------------------
CREATE FUNCTION pg_temp.deve_falhar(p_sql text, p_estado text, p_desc text) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  BEGIN
    EXECUTE p_sql;
  EXCEPTION WHEN OTHERS THEN
    IF SQLSTATE <> p_estado THEN
      RAISE EXCEPTION 'TESTE FALHOU [%]: esperado SQLSTATE %, veio % (%)', p_desc, p_estado, SQLSTATE, SQLERRM;
    END IF;
    RAISE NOTICE 'ok - %', p_desc;
    RETURN;
  END;
  RAISE EXCEPTION 'TESTE FALHOU [%]: o comando deveria ter falhado', p_desc;
END $$;

-- 1. fixtures -----------------------------------------------------------------
INSERT INTO usuarios (id, email, nome, senha_hash, admin) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Ana@Isolutis.com', 'Ana', 'hash', true),
  ('a0000000-0000-0000-0000-000000000002', 'bruno@isolutis.com', 'Bruno', NULL, false),
  ('a0000000-0000-0000-0000-000000000003', 'carla@isolutis.com', 'Carla', 'hash', false);

SELECT set_config('app.usuario_id', 'a0000000-0000-0000-0000-000000000001', false) AS _ \gset

INSERT INTO clientes (id, nome, cnpj, origem) VALUES
  ('c0000000-0000-0000-0000-000000000001', 'Acme Ltda', '12345678000199', 'Indicação'),
  ('c0000000-0000-0000-0000-000000000002', 'Beta SA', NULL, 'Site'),
  ('c0000000-0000-0000-0000-000000000003', 'Gama ME', NULL, NULL);

INSERT INTO negocios (id, titulo, cliente_id, etapa, valor, mensal, previsao, responsavel_id) VALUES
  ('d0000000-0000-0000-0000-000000000001', 'Portal Acme', 'c0000000-0000-0000-0000-000000000001', 'proposta', 10000, 500, '2026-11-15', 'a0000000-0000-0000-0000-000000000002'),
  ('d0000000-0000-0000-0000-000000000002', 'App Beta', 'c0000000-0000-0000-0000-000000000002', 'lead', 5000, 0, NULL, NULL),
  ('d0000000-0000-0000-0000-000000000003', 'Site Beta', 'c0000000-0000-0000-0000-000000000002', 'negociacao', 3000, 200, '2026-10-20', NULL);
INSERT INTO negocios (id, titulo, cliente_id, etapa, valor, motivo_perda)
  VALUES ('d0000000-0000-0000-0000-000000000004', 'Perdido', 'c0000000-0000-0000-0000-000000000001', 'perdido', 1000, 'Preço');
INSERT INTO negocios (id, titulo, cliente_id, etapa, valor, fechado_em)
  VALUES ('d0000000-0000-0000-0000-000000000005', 'Ganho', 'c0000000-0000-0000-0000-000000000001', 'ganho', 2000, '2026-09-01');

-- 2. usuarios / citext -----------------------------------------------------------
DO $$
BEGIN
  PERFORM pg_temp.deve_falhar($q$INSERT INTO usuarios (email, nome) VALUES ('ANA@isolutis.com', 'Dup')$q$, '23505', 'email duplicado ignorando caixa');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO usuarios (email, nome) VALUES ('sem-arroba', 'X')$q$, '23514', 'email invalido');
  ASSERT (SELECT senha_definida FROM usuarios WHERE nome = 'Ana') = true, 'senha_definida true';
  ASSERT (SELECT senha_definida FROM usuarios WHERE nome = 'Bruno') = false, 'senha_definida false';
  ASSERT (SELECT count(*) FROM categorias_despesa) = 10, 'categorias semeadas';
END $$;

-- 3. constraints de domínio --------------------------------------------------------
DO $$
DECLARE
  c1 constant text := 'c0000000-0000-0000-0000-000000000001';
BEGIN
  -- clientes
  PERFORM pg_temp.deve_falhar($q$INSERT INTO clientes (nome) VALUES ('  ')$q$, '23514', 'cliente sem nome');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO clientes (nome, cnpj) VALUES ('X', '123')$q$, '23514', 'cnpj invalido');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO clientes (nome, cnpj) VALUES ('X', '12345678000199')$q$, '23505', 'cnpj duplicado');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO clientes (nome, origem) VALUES ('X', 'Orkut')$q$, '23514', 'origem invalida (enum)');
  -- produtos
  PERFORM pg_temp.deve_falhar($q$INSERT INTO produtos (nome, tipo) VALUES ('P', 'assinatura')$q$, '23514', 'produto tipo invalido');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO produtos (nome, tipo, preco) VALUES ('P', 'projeto', -1)$q$, '23514', 'produto preco negativo');
  -- negocios
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, etapa) VALUES ('N', %L, 'fechando')$q$, c1), '23514', 'etapa invalida');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, valor) VALUES ('N', %L, -10)$q$, c1), '23514', 'valor negativo');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, mensal) VALUES ('N', %L, -10)$q$, c1), '23514', 'mensal negativo');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, etapa) VALUES ('N', %L, 'perdido')$q$, c1), '23514', 'perdido sem motivo');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, etapa, motivo_perda) VALUES ('N', %L, 'lead', 'Preço')$q$, c1), '23514', 'motivo sem perdido');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, etapa, motivo_perda) VALUES ('N', %L, 'perdido', 'Chuva')$q$, c1), '23514', 'motivo fora do dominio');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO negocios (titulo, cliente_id, etapa, fechado_em) VALUES ('N', %L, 'lead', '2026-01-01')$q$, c1), '23514', 'fechado_em fora de ganho');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO negocios (titulo, cliente_id) VALUES ('N', 'c0000000-0000-0000-0000-0000000000ff')$q$, '23503', 'negocio com cliente inexistente');
  -- orcamentos
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, status) VALUES (%L, 'vencido')$q$, c1), '23514', 'status orcamento invalido (vencido nao e armazenado)');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, desconto) VALUES (%L, -1)$q$, c1), '23514', 'desconto negativo');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, validade_dias) VALUES (%L, 0)$q$, c1), '23514', 'validade 0');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, numero) VALUES (%L, '26-1')$q$, c1), '23514', 'formato de numero');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, aprovado_em) VALUES (%L, '2026-01-01')$q$, c1), '23514', 'aprovado_em sem status aprovado');
  -- negocio de outro cliente (FK composta)
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO orcamentos (cliente_id, negocio_id) VALUES (%L, 'd0000000-0000-0000-0000-000000000002')$q$, c1), '23503', 'orcamento com negocio de outro cliente');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, negocio_id) VALUES (%L, 'projeto', 'x', 1, '2026-01-01', 'd0000000-0000-0000-0000-000000000002')$q$, c1), '23503', 'lancamento com negocio de outro cliente');
END $$;

-- 4. numeração de orçamentos -----------------------------------------------------
INSERT INTO orcamentos (id, data, cliente_id, negocio_id, status, desconto, obs) VALUES
  ('e0000000-0000-0000-0000-000000000001', '2026-03-01', 'c0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'enviado', 500, NULL);
INSERT INTO orcamentos (id, data, cliente_id, status, desconto) VALUES
  ('e0000000-0000-0000-0000-000000000002', '2026-04-01', 'c0000000-0000-0000-0000-000000000002', 'rascunho', 9999),
  ('e0000000-0000-0000-0000-000000000003', current_date, 'c0000000-0000-0000-0000-000000000002', 'enviado', 0);
INSERT INTO orcamentos (id, data, cliente_id) VALUES
  ('e0000000-0000-0000-0000-000000000004', '2027-01-10', 'c0000000-0000-0000-0000-000000000001');

DO $$
BEGIN
  ASSERT (SELECT numero FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-000000000001') = '2026-001', 'primeiro 2026-001';
  ASSERT (SELECT numero FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-000000000002') = '2026-002', 'segundo 2026-002';
  ASSERT (SELECT numero FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-000000000003') = to_char(current_date, 'YYYY') || '-00' || (CASE WHEN extract(year FROM current_date) = 2026 THEN '3' ELSE '1' END), 'terceiro do ano corrente';
  ASSERT (SELECT numero FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-000000000004') = '2027-001', 'sequencia reinicia por ano';
  -- funcao direta
  ASSERT proximo_numero_orcamento(2030) = '2030-001', 'funcao direta ano novo';
  ASSERT proximo_numero_orcamento(2030) = '2030-002', 'funcao direta incrementa';
  -- unicidade
  PERFORM pg_temp.deve_falhar($q$INSERT INTO orcamentos (cliente_id, numero) VALUES ('c0000000-0000-0000-0000-000000000001', '2026-001')$q$, '23505', 'numero duplicado');
  -- imutavel
  PERFORM pg_temp.deve_falhar($q$UPDATE orcamentos SET numero = '2026-099' WHERE id = 'e0000000-0000-0000-0000-000000000001'$q$, '23514', 'numero imutavel');
  -- numero informado (legado) avanca a sequencia
  INSERT INTO orcamentos (numero, data, cliente_id) VALUES ('2025-040', '2025-06-01', 'c0000000-0000-0000-0000-000000000001');
  INSERT INTO orcamentos (data, cliente_id) VALUES ('2025-07-01', 'c0000000-0000-0000-0000-000000000001');
  ASSERT EXISTS (SELECT 1 FROM orcamentos WHERE numero = '2025-041'), 'sequencia apos numero legado';
  ASSERT (SELECT ultimo FROM orcamento_sequencias WHERE ano = 2026) >= 3, 'sequencia 2026';
END $$;

-- 5. itens + view de totais ---------------------------------------------------------
INSERT INTO produtos (id, nome, tipo, preco) VALUES ('f0000000-0000-0000-0000-000000000001', 'Site institucional', 'projeto', 0);
INSERT INTO orcamento_itens (orcamento_id, ordem, produto_id, descricao, qtd, preco_unitario, mensal) VALUES
  ('e0000000-0000-0000-0000-000000000001', 1, 'f0000000-0000-0000-0000-000000000001', 'Site', 2, 1500.00, false),
  ('e0000000-0000-0000-0000-000000000001', 2, NULL, 'Hospedagem', 1, 250.00, false),
  ('e0000000-0000-0000-0000-000000000001', 3, NULL, 'Manutencao', 1, 300.00, true),
  ('e0000000-0000-0000-0000-000000000001', 4, NULL, 'Suporte horas', 0.5, 200.00, true),
  ('e0000000-0000-0000-0000-000000000002', 1, NULL, 'Item pequeno', 1, 100.00, false);

DO $$
DECLARE r record;
BEGIN
  SELECT * INTO r FROM vw_orcamentos_totais WHERE numero = '2026-001';
  ASSERT r.qtd_itens = 4, 'qtd itens';
  ASSERT r.subtotal_projeto = 3250.00, 'subtotal projeto ' || r.subtotal_projeto;
  ASSERT r.total_projeto = 2750.00, 'total projeto (3250 - 500 desconto)';
  ASSERT r.total_mensal = 400.00, 'total mensal';
  ASSERT r.cliente_nome = 'Acme Ltda', 'cliente_nome';
  SELECT * INTO r FROM vw_orcamentos_totais WHERE numero = '2026-002';
  ASSERT r.total_projeto = 0, 'desconto maior que soma => 0';
  ASSERT r.total_mensal = 0, 'sem itens mensais => 0';
  SELECT * INTO r FROM vw_orcamentos_totais WHERE id = 'e0000000-0000-0000-0000-000000000003';
  ASSERT r.qtd_itens = 0 AND r.total_projeto = 0, 'orcamento sem itens';
  -- vencido derivado: enviado de 2026-03-01 com 15 dias esta vencido; rascunho nunca; enviado de hoje nao
  ASSERT (SELECT vencido FROM vw_orcamentos_totais WHERE numero = '2026-001') = true, 'enviado antigo vencido';
  ASSERT (SELECT vencido FROM vw_orcamentos_totais WHERE numero = '2026-002') = false, 'rascunho nao vence';
  ASSERT (SELECT vencido FROM vw_orcamentos_totais WHERE id = 'e0000000-0000-0000-0000-000000000003') = false, 'enviado hoje nao vencido';
  ASSERT (SELECT validade_ate FROM vw_orcamentos_totais WHERE numero = '2026-001') = date '2026-03-16', 'validade_ate';
  -- itens
  PERFORM pg_temp.deve_falhar($q$INSERT INTO orcamento_itens (orcamento_id, ordem, descricao, qtd) VALUES ('e0000000-0000-0000-0000-000000000001', 9, 'x', 0)$q$, '23514', 'qtd zero');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO orcamento_itens (orcamento_id, ordem, descricao, preco_unitario) VALUES ('e0000000-0000-0000-0000-000000000001', 9, 'x', -5)$q$, '23514', 'preco negativo');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO orcamento_itens (orcamento_id, ordem, descricao) VALUES ('e0000000-0000-0000-0000-000000000001', 1, 'dup'); SET CONSTRAINTS uq_orcamento_itens_ordem IMMEDIATE$q$, '23505', 'ordem duplicada no orcamento');
  -- reordenar trocando posicoes (DEFERRABLE)
  UPDATE orcamento_itens SET ordem = 3 - ordem WHERE orcamento_id = 'e0000000-0000-0000-0000-000000000001' AND ordem IN (1, 2);
  ASSERT (SELECT descricao FROM orcamento_itens WHERE orcamento_id = 'e0000000-0000-0000-0000-000000000001' AND ordem = 1) = 'Hospedagem', 'troca de ordem deferrable';
END $$;

-- 6. lançamentos de receita --------------------------------------------------------
DO $$
DECLARE c1 constant text := 'c0000000-0000-0000-0000-000000000001';
BEGIN
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, status) VALUES (%L, 'projeto', 'x', 1, '2026-01-01', 'recebido')$q$, c1), '23514', 'recebido sem recebido_em');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, recebido_em) VALUES (%L, 'projeto', 'x', 1, '2026-01-01', '2026-01-02')$q$, c1), '23514', 'previsto com recebido_em');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento) VALUES (%L, 'projeto', 'x', -1, '2026-01-01')$q$, c1), '23514', 'receita valor negativo');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento) VALUES (%L, 'venda', 'x', 1, '2026-01-01')$q$, c1), '23514', 'tipo invalido');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, parcela) VALUES (%L, 'projeto', 'x', 1, '2026-01-01', 1)$q$, c1), '23514', 'parcela sem grupo/total');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, grupo_id, parcela, total_parcelas) VALUES (%L, 'projeto', 'x', 1, '2026-01-01', gen_random_uuid(), 4, 3)$q$, c1), '23514', 'parcela maior que total');
END $$;

-- lote atômico: 3 parcelas de projeto + 3 mensalidades (séries distintas)
DO $$
DECLARE g1 uuid := gen_random_uuid(); g2 uuid := gen_random_uuid();
BEGIN
  INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, grupo_id, parcela, total_parcelas, negocio_id, status, recebido_em)
  SELECT 'c0000000-0000-0000-0000-000000000001', 'projeto', 'Portal - parcela ' || n, 3333.33, date '2026-10-10' + (n - 1) * 30, g1, n, 3,
         'd0000000-0000-0000-0000-000000000001', CASE WHEN n = 1 THEN 'recebido' ELSE 'previsto' END, CASE WHEN n = 1 THEN date '2026-10-10' END
  FROM generate_series(1, 3) n;
  INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, grupo_id, parcela, total_parcelas)
  SELECT 'c0000000-0000-0000-0000-000000000001', 'mensal', 'Manutencao ' || n || '/3', 500, date '2026-11-05' + (n - 1) * 30, g2, n, 3
  FROM generate_series(1, 3) n;
  ASSERT (SELECT count(*) FROM lancamentos_receita WHERE grupo_id = g1) = 3, 'serie de projeto';
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento, grupo_id, parcela, total_parcelas) VALUES ('c0000000-0000-0000-0000-000000000001', 'mensal', 'dup', 1, '2026-01-01', %L, 2, 3)$q$, g2), '23505', 'parcela duplicada na serie');
  -- consultas de relatorio
  ASSERT (SELECT sum(valor) FROM lancamentos_receita WHERE status = 'recebido') = 3333.33, 'recebido';
  ASSERT (SELECT sum(valor) FROM lancamentos_receita WHERE tipo = 'mensal') = 1500, 'recorrente';
  -- negocio "faturado" derivado
  ASSERT EXISTS (SELECT 1 FROM lancamentos_receita WHERE negocio_id = 'd0000000-0000-0000-0000-000000000001'), 'faturado derivado';
END $$;

-- 7. despesas e investimentos -------------------------------------------------------
INSERT INTO investidores (id, nome, usuario_id) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'Ana', 'a0000000-0000-0000-0000-000000000001'),
  ('b0000000-0000-0000-0000-000000000002', 'Tio Investidor', NULL);

DO $$
DECLARE cat uuid := (SELECT id FROM categorias_despesa WHERE nome = 'servidores e infraestrutura');
BEGIN
  ASSERT cat IS NOT NULL, 'categoria citext';
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO despesas (data, descricao, valor, categoria_id, status) VALUES ('2026-01-01', 'x', 10, %L, 'pago')$q$, cat), '23514', 'despesa paga sem pago_em');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO despesas (data, descricao, valor, categoria_id, pago_em) VALUES ('2026-01-01', 'x', 10, %L, '2026-01-01')$q$, cat), '23514', 'a_pagar com pago_em');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO despesas (data, descricao, valor, categoria_id) VALUES ('2026-01-01', 'x', -10, %L)$q$, cat), '23514', 'despesa valor negativo');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO despesas (data, descricao, valor, categoria_id) VALUES ('2026-01-01', 'x', 10, gen_random_uuid())$q$, '23503', 'categoria inexistente');
  PERFORM pg_temp.deve_falhar(format($q$INSERT INTO despesas (data, descricao, valor, categoria_id, status) VALUES ('2026-01-01', 'x', 10, %L, 'cancelado')$q$, cat), '23514', 'status despesa invalido');

  INSERT INTO despesas (data, descricao, valor, categoria_id, status, pago_em, fornecedor) VALUES
    ('2026-10-01', 'VPS', 100.50, cat, 'pago', '2026-10-02', 'Hetzner'),
    ('2026-10-15', 'Dominio', 40, cat, 'a_pagar', NULL, 'Registro.br');
  INSERT INTO despesas (data, descricao, valor, categoria_id, grupo_id, parcela, total_parcelas)
  SELECT date '2026-11-01' + (n - 1) * 30, 'Contabilidade ' || n || '/3', 300, (SELECT id FROM categorias_despesa WHERE nome = 'Contabilidade'), 'aaaaaaaa-0000-0000-0000-000000000001', n, 3
  FROM generate_series(1, 3) n;
  ASSERT (SELECT sum(valor) FROM despesas WHERE status = 'pago') = 100.50, 'despesas pagas';
  ASSERT (SELECT count(*) FROM despesas WHERE status = 'a_pagar') = 4, 'a pagar';

  PERFORM pg_temp.deve_falhar($q$INSERT INTO investimentos (data, descricao, valor, investidor_id, forma) VALUES ('2026-01-01', 'x', 1, 'b0000000-0000-0000-0000-000000000001', 'Cripto')$q$, '23514', 'forma invalida');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO investimentos (data, descricao, valor, investidor_id, forma) VALUES ('2026-01-01', 'x', -1, 'b0000000-0000-0000-0000-000000000001', 'Outro')$q$, '23514', 'investimento negativo');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO investimentos (data, descricao, valor, investidor_id, forma) VALUES ('2026-01-01', 'x', 1, gen_random_uuid(), 'Outro')$q$, '23503', 'investidor inexistente');
  INSERT INTO investimentos (data, descricao, valor, investidor_id, forma) VALUES
    ('2025-12-01', 'Aporte inicial', 5000, 'b0000000-0000-0000-0000-000000000001', 'Dinheiro (aporte)'),
    ('2026-02-01', 'Notebook', 4000, 'b0000000-0000-0000-0000-000000000001', 'Equipamento'),
    ('2026-03-01', 'Aporte externo', 1000, 'b0000000-0000-0000-0000-000000000002', 'Dinheiro (aporte)');
  ASSERT (SELECT sum(valor) FROM investimentos WHERE investidor_id = 'b0000000-0000-0000-0000-000000000001') = 9000, 'total investido desde o inicio';
  ASSERT (SELECT sum(valor) FROM investimentos WHERE investidor_id = 'b0000000-0000-0000-0000-000000000001' AND data >= '2026-01-01') = 4000, 'total investido no ano';
  PERFORM pg_temp.deve_falhar($q$DELETE FROM investidores WHERE id = 'b0000000-0000-0000-0000-000000000002'$q$, '23503', 'excluir investidor com investimentos');
  PERFORM pg_temp.deve_falhar($q$DELETE FROM categorias_despesa WHERE nome = 'Contabilidade'$q$, '23503', 'excluir categoria em uso');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO investidores (nome) VALUES ('ana')$q$, '23505', 'investidor nome duplicado (citext)');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO investidores (nome, usuario_id) VALUES ('Outra Ana', 'a0000000-0000-0000-0000-000000000001')$q$, '23505', 'usuario com 2 investidores');
END $$;

-- 8. projetos e etapas ---------------------------------------------------------------
INSERT INTO projetos (id, titulo, cliente_id, negocio_id, orcamento_id, status, responsavel_id, inicio, entrega) VALUES
  ('90000000-0000-0000-0000-000000000001', 'Portal Acme', 'c0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', 'construcao', 'a0000000-0000-0000-0000-000000000002', '2026-10-01', '2026-12-01');
INSERT INTO projetos (id, titulo, cliente_id) VALUES ('90000000-0000-0000-0000-000000000002', 'Projeto vazio', 'c0000000-0000-0000-0000-000000000002');

DO $$
DECLARE r record;
BEGIN
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projetos (titulo, cliente_id, negocio_id) VALUES ('Dup', 'c0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001')$q$, '23505', '2 projetos no mesmo negocio');
  INSERT INTO projetos (titulo, cliente_id) VALUES ('Sem negocio A', 'c0000000-0000-0000-0000-000000000001'), ('Sem negocio B', 'c0000000-0000-0000-0000-000000000001');
  RAISE NOTICE 'ok - varios projetos sem negocio permitidos';
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projetos (titulo, cliente_id, inicio, entrega) VALUES ('X', 'c0000000-0000-0000-0000-000000000001', '2026-02-01', '2026-01-01')$q$, '23514', 'projeto entrega antes do inicio');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projetos (titulo, cliente_id, status) VALUES ('X', 'c0000000-0000-0000-0000-000000000001', 'cancelado')$q$, '23514', 'status projeto invalido');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projetos (titulo, cliente_id, negocio_id) VALUES ('X', 'c0000000-0000-0000-0000-000000000003', 'd0000000-0000-0000-0000-000000000002')$q$, '23503', 'projeto com negocio de outro cliente');

  INSERT INTO projeto_etapas (projeto_id, ordem, titulo, status, inicio, fim) VALUES
    ('90000000-0000-0000-0000-000000000001', 1, 'Descoberta', 'concluida', '2026-10-01', '2026-10-10'),
    ('90000000-0000-0000-0000-000000000001', 2, 'Design', 'concluida', '2026-10-11', '2026-10-20'),
    ('90000000-0000-0000-0000-000000000001', 3, 'Build', 'andamento', '2026-10-21', NULL),
    ('90000000-0000-0000-0000-000000000001', 4, 'Entrega', 'a_fazer', NULL, NULL);
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projeto_etapas (projeto_id, ordem, titulo, inicio, fim) VALUES ('90000000-0000-0000-0000-000000000001', 5, 'X', '2026-02-01', '2026-01-01')$q$, '23514', 'etapa fim < inicio');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projeto_etapas (projeto_id, ordem, titulo, status) VALUES ('90000000-0000-0000-0000-000000000001', 5, 'X', 'feito')$q$, '23514', 'status etapa invalido');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO projeto_etapas (projeto_id, ordem, titulo) VALUES ('90000000-0000-0000-0000-000000000001', 4, 'Dup'); SET CONSTRAINTS uq_projeto_etapas_ordem IMMEDIATE$q$, '23505', 'ordem duplicada na etapa');
  -- reordenar (swap) em uma transacao: deferrable
  UPDATE projeto_etapas SET ordem = 7 - ordem WHERE projeto_id = '90000000-0000-0000-0000-000000000001' AND ordem IN (3, 4);
  ASSERT (SELECT titulo FROM projeto_etapas WHERE projeto_id = '90000000-0000-0000-0000-000000000001' AND ordem = 3) = 'Entrega', 'swap de etapas';

  SELECT * INTO r FROM vw_projetos_progresso WHERE projeto_id = '90000000-0000-0000-0000-000000000001';
  ASSERT r.total_etapas = 4 AND r.etapas_concluidas = 2 AND r.progresso_pct = 50, 'progresso 2/4 = 50';
  SELECT * INTO r FROM vw_projetos_progresso WHERE projeto_id = '90000000-0000-0000-0000-000000000002';
  ASSERT r.total_etapas = 0 AND r.progresso_pct = 0, 'projeto sem etapas = 0';
  UPDATE projeto_etapas SET status = 'concluida' WHERE projeto_id = '90000000-0000-0000-0000-000000000001' AND ordem IN (3, 4);
  ASSERT (SELECT progresso_pct FROM vw_projetos_progresso WHERE projeto_id = '90000000-0000-0000-0000-000000000001') = 100, 'progresso 100';
END $$;

-- 9. tarefas -------------------------------------------------------------------------
DO $$
BEGIN
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefas (titulo, coluna) VALUES ('T', 'doing')$q$, '23514', 'coluna invalida');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefas (titulo, prioridade) VALUES ('T', 'urgente')$q$, '23514', 'prioridade invalida');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefas (titulo, coluna) VALUES ('T', 'concluido')$q$, '23514', 'concluido sem concluida_em');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefas (titulo, coluna, concluida_em) VALUES ('T', 'fazendo', now())$q$, '23514', 'concluida_em com coluna aberta');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefas (titulo) VALUES ('')$q$, '23514', 'tarefa sem titulo');

  INSERT INTO tarefas (id, titulo, coluna, prioridade, prazo, responsavel_id, descricao, cliente_id, projeto_id) VALUES
    ('70000000-0000-0000-0000-000000000001', 'Reunião de diagnóstico', 'a_fazer', 'baixa', current_date - 3, 'a0000000-0000-0000-0000-000000000002', 'Levantar requisitos', 'c0000000-0000-0000-0000-000000000001', '90000000-0000-0000-0000-000000000001'),
    ('70000000-0000-0000-0000-000000000002', 'Subir servidor', 'a_fazer', 'alta', current_date + 5, 'a0000000-0000-0000-0000-000000000002', NULL, NULL, NULL),
    ('70000000-0000-0000-0000-000000000003', 'Proposta final', 'a_fazer', 'media', NULL, NULL, NULL, NULL, NULL);
  INSERT INTO tarefas (id, titulo, coluna, concluida_em, prazo) VALUES
    ('70000000-0000-0000-0000-000000000004', 'Atrasada mas concluida', 'concluido', now(), current_date - 10);

  -- ordem do kanban: alta, media, baixa (e nao alfabetica)
  ASSERT (SELECT array_agg(titulo ORDER BY prioridade_ordem, prazo, criado_em) FROM tarefas WHERE coluna = 'a_fazer')
         = ARRAY['Subir servidor', 'Proposta final', 'Reunião de diagnóstico'], 'ordenacao por prioridade_ordem';
  -- atrasadas
  ASSERT (SELECT array_agg(titulo) FROM tarefas WHERE prazo < current_date AND coluna <> 'concluido') = ARRAY['Reunião de diagnóstico'], 'atrasadas';
  -- minhas abertas
  ASSERT (SELECT count(*) FROM tarefas WHERE responsavel_id = 'a0000000-0000-0000-0000-000000000002' AND coluna <> 'concluido') = 2, 'minhas abertas';
  -- busca sem acento / parcial
  ASSERT (SELECT count(*) FROM tarefas WHERE busca ILIKE '%' || imm_unaccent(lower('REUNIAO')) || '%') = 1, 'busca sem acento no titulo';
  ASSERT (SELECT count(*) FROM tarefas WHERE busca ILIKE '%' || imm_unaccent(lower('requisitos')) || '%') = 1, 'busca na descricao';

  INSERT INTO tarefa_checklist (tarefa_id, ordem, texto) VALUES
    ('70000000-0000-0000-0000-000000000001', 1, 'Agendar'), ('70000000-0000-0000-0000-000000000001', 2, 'Enviar pauta');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefa_checklist (tarefa_id, ordem, texto) VALUES ('70000000-0000-0000-0000-000000000001', 2, 'dup'); SET CONSTRAINTS uq_tarefa_checklist_ordem IMMEDIATE$q$, '23505', 'ordem duplicada no checklist');
  PERFORM pg_temp.deve_falhar($q$INSERT INTO tarefa_checklist (tarefa_id, ordem, texto) VALUES (gen_random_uuid(), 1, 'x')$q$, '23503', 'checklist sem tarefa');
END $$;

-- 10. auditoria / concorrência otimista ---------------------------------------------
SELECT set_config('app.usuario_id', 'a0000000-0000-0000-0000-000000000002', false) AS _ \gset
SELECT pg_sleep(0.05);
UPDATE clientes SET cidade = 'Recife' WHERE id = 'c0000000-0000-0000-0000-000000000001';

DO $$
DECLARE r clientes;
BEGIN
  SELECT * INTO r FROM clientes WHERE id = 'c0000000-0000-0000-0000-000000000001';
  ASSERT r.versao = 2, 'versao incrementa no update: ' || r.versao;
  ASSERT r.criado_por = 'a0000000-0000-0000-0000-000000000001', 'criado_por preservado';
  ASSERT r.atualizado_por = 'a0000000-0000-0000-0000-000000000002', 'atualizado_por = usuario da sessao';
  ASSERT r.atualizado_em > r.criado_em, 'atualizado_em avanca';
END $$;

-- tentativa de adulterar campos de auditoria
UPDATE clientes SET criado_em = '2000-01-01', criado_por = 'a0000000-0000-0000-0000-000000000003', versao = 99, atualizado_em = '2000-01-01', nome = 'Acme Ltda 2'
 WHERE id = 'c0000000-0000-0000-0000-000000000001';

DO $$
DECLARE r clientes;
BEGIN
  SELECT * INTO r FROM clientes WHERE id = 'c0000000-0000-0000-0000-000000000001';
  ASSERT r.versao = 3, 'versao nao pode ser forjada: ' || r.versao;
  ASSERT r.criado_em > '2020-01-01', 'criado_em imutavel';
  ASSERT r.criado_por = 'a0000000-0000-0000-0000-000000000001', 'criado_por imutavel';
  ASSERT r.atualizado_em > '2020-01-01', 'atualizado_em controlado pelo trigger';
END $$;

-- UPDATE sem mudança real não conta como edição
UPDATE clientes SET nome = nome WHERE id = 'c0000000-0000-0000-0000-000000000001';
DO $$
BEGIN
  ASSERT (SELECT versao FROM clientes WHERE id = 'c0000000-0000-0000-0000-000000000001') = 3, 'no-op nao incrementa';
END $$;

-- concorrência otimista (padrão do backend: WHERE versao = lida)
DO $$
DECLARE n integer;
BEGIN
  UPDATE clientes SET cidade = 'Olinda' WHERE id = 'c0000000-0000-0000-0000-000000000001' AND versao = 3;
  GET DIAGNOSTICS n = ROW_COUNT;
  ASSERT n = 1, 'primeiro escritor com versao correta atualiza';
  UPDATE clientes SET cidade = 'Outro' WHERE id = 'c0000000-0000-0000-0000-000000000001' AND versao = 3;
  GET DIAGNOSTICS n = ROW_COUNT;
  ASSERT n = 0, 'segundo escritor com versao velha nao atualiza (conflito)';
END $$;

-- SET LOCAL via set_config(..., true) vale só na transação
SELECT set_config('app.usuario_id', '', false) AS _ \gset
BEGIN;
SELECT set_config('app.usuario_id', 'a0000000-0000-0000-0000-000000000003', true) AS _ \gset
INSERT INTO clientes (id, nome) VALUES ('c0000000-0000-0000-0000-0000000000a1', 'Criado por Carla');
COMMIT;
DO $$
BEGIN
  ASSERT app_usuario_id() IS NULL, 'GUC local expirou no COMMIT';
  ASSERT (SELECT criado_por FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000a1') = 'a0000000-0000-0000-0000-000000000003', 'criado_por via set_config local';
END $$;

-- ultimo_acesso não gera conflito de versão
SELECT set_config('app.usuario_id', 'a0000000-0000-0000-0000-000000000001', false) AS _ \gset
UPDATE usuarios SET ultimo_acesso = now() WHERE nome = 'Bruno';
DO $$
BEGIN
  ASSERT (SELECT versao FROM usuarios WHERE nome = 'Bruno') = 1, 'ultimo_acesso nao incrementa versao';
END $$;
UPDATE usuarios SET nome = 'Bruno S.' WHERE nome = 'Bruno';
DO $$
BEGIN
  ASSERT (SELECT versao FROM usuarios WHERE nome = 'Bruno S.') = 2, 'edicao de nome incrementa versao de usuarios';
END $$;

-- modo carga legada preserva carimbos
SELECT set_config('app.preservar_auditoria', 'on', false) AS _ \gset
INSERT INTO clientes (id, nome, criado_em, atualizado_em, criado_por, atualizado_por, versao)
VALUES ('c0000000-0000-0000-0000-0000000000a2', 'Legado', '2023-05-01 10:00+00', '2024-01-01 10:00+00', 'a0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000003', 1);
SELECT set_config('app.preservar_auditoria', 'off', false) AS _ \gset
DO $$
BEGIN
  ASSERT (SELECT criado_em FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000a2') = '2023-05-01 10:00+00', 'carga legada preserva criado_em';
  ASSERT (SELECT atualizado_por FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000a2') = 'a0000000-0000-0000-0000-000000000003', 'carga legada preserva atualizado_por';
END $$;

-- 11. políticas de FK --------------------------------------------------------------------
DO $$
BEGIN
  -- cliente com negocio / orcamento / lancamento nao exclui
  PERFORM pg_temp.deve_falhar($q$DELETE FROM clientes WHERE id = 'c0000000-0000-0000-0000-000000000001'$q$, '23503', 'excluir cliente com negocios');
  PERFORM pg_temp.deve_falhar($q$DELETE FROM clientes WHERE id = 'c0000000-0000-0000-0000-000000000002'$q$, '23503', 'excluir cliente com negocios/orcamentos');
  -- cliente so com orcamento
  INSERT INTO clientes (id, nome) VALUES ('c0000000-0000-0000-0000-0000000000b1', 'So orcamento');
  INSERT INTO orcamentos (cliente_id) VALUES ('c0000000-0000-0000-0000-0000000000b1');
  PERFORM pg_temp.deve_falhar($q$DELETE FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000b1'$q$, '23503', 'excluir cliente so com orcamento');
  -- cliente so com faturamento
  INSERT INTO clientes (id, nome) VALUES ('c0000000-0000-0000-0000-0000000000b2', 'So faturamento');
  INSERT INTO lancamentos_receita (cliente_id, tipo, descricao, valor, vencimento) VALUES ('c0000000-0000-0000-0000-0000000000b2', 'outro', 'x', 1, '2026-01-01');
  PERFORM pg_temp.deve_falhar($q$DELETE FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000b2'$q$, '23503', 'excluir cliente com faturamento');
  -- cliente livre exclui; tarefa vinculada fica sem cliente
  INSERT INTO clientes (id, nome) VALUES ('c0000000-0000-0000-0000-0000000000b3', 'Livre');
  INSERT INTO tarefas (id, titulo, cliente_id) VALUES ('70000000-0000-0000-0000-0000000000b3', 'ligada', 'c0000000-0000-0000-0000-0000000000b3');
  DELETE FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000b3';
  ASSERT (SELECT cliente_id FROM tarefas WHERE id = '70000000-0000-0000-0000-0000000000b3') IS NULL, 'tarefa.cliente_id SET NULL';
  RAISE NOTICE 'ok - cliente sem vinculos exclui';

  -- CASCADE: orcamento -> itens
  INSERT INTO orcamentos (id, cliente_id) VALUES ('e0000000-0000-0000-0000-0000000000c1', 'c0000000-0000-0000-0000-000000000003');
  INSERT INTO orcamento_itens (orcamento_id, ordem, descricao) VALUES ('e0000000-0000-0000-0000-0000000000c1', 1, 'i');
  DELETE FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-0000000000c1';
  ASSERT NOT EXISTS (SELECT 1 FROM orcamento_itens WHERE orcamento_id = 'e0000000-0000-0000-0000-0000000000c1'), 'cascade itens';
  -- SET NULL: produto -> item
  DELETE FROM produtos WHERE id = 'f0000000-0000-0000-0000-000000000001';
  ASSERT (SELECT produto_id FROM orcamento_itens WHERE descricao = 'Site') IS NULL, 'item.produto_id SET NULL';
  ASSERT (SELECT versao FROM orcamento_itens WHERE descricao = 'Site') >= 2, 'SET NULL de negocio conta como edicao (versao sobe)';
  -- SET NULL composto: excluir negocio mantem cliente_id do orcamento/projeto/lancamento
  DELETE FROM negocios WHERE id = 'd0000000-0000-0000-0000-000000000001';
  ASSERT (SELECT negocio_id IS NULL AND cliente_id IS NOT NULL FROM orcamentos WHERE id = 'e0000000-0000-0000-0000-000000000001'), 'orcamento.negocio_id SET NULL sem perder cliente';
  ASSERT (SELECT negocio_id IS NULL AND cliente_id IS NOT NULL FROM projetos WHERE id = '90000000-0000-0000-0000-000000000001'), 'projeto.negocio_id SET NULL sem perder cliente';
  ASSERT (SELECT count(*) FROM lancamentos_receita WHERE negocio_id IS NULL AND grupo_id IS NOT NULL AND tipo = 'projeto') = 3, 'lancamentos.negocio_id SET NULL';
  -- CASCADE projeto -> etapas ; SET NULL tarefa.projeto_id
  DELETE FROM projetos WHERE id = '90000000-0000-0000-0000-000000000001';
  ASSERT NOT EXISTS (SELECT 1 FROM projeto_etapas WHERE projeto_id = '90000000-0000-0000-0000-000000000001'), 'cascade etapas';
  ASSERT (SELECT projeto_id FROM tarefas WHERE id = '70000000-0000-0000-0000-000000000001') IS NULL, 'tarefa.projeto_id SET NULL';
  -- CASCADE tarefa -> checklist
  DELETE FROM tarefas WHERE id = '70000000-0000-0000-0000-000000000001';
  ASSERT NOT EXISTS (SELECT 1 FROM tarefa_checklist WHERE tarefa_id = '70000000-0000-0000-0000-000000000001'), 'cascade checklist';
END $$;

-- excluir usuário: SET NULL em auditoria/responsáveis, sem violar a imutabilidade de criado_por
DELETE FROM usuarios WHERE id = 'a0000000-0000-0000-0000-000000000003';
DO $$
DECLARE r clientes;
BEGIN
  SELECT * INTO r FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000a1';
  ASSERT r.criado_por IS NULL, 'criado_por SET NULL ao excluir usuario';
  ASSERT r.versao = 1, 'acao referencial em auditoria nao incrementa versao';
  ASSERT (SELECT atualizado_por FROM clientes WHERE id = 'c0000000-0000-0000-0000-0000000000a2') IS NULL, 'atualizado_por SET NULL';
  -- responsavel vira NULL e conta como edicao feita pelo usuario da sessao
  DELETE FROM usuarios WHERE id = 'a0000000-0000-0000-0000-000000000002';
  ASSERT (SELECT responsavel_id FROM tarefas WHERE id = '70000000-0000-0000-0000-000000000002') IS NULL, 'tarefa.responsavel_id SET NULL';
  ASSERT (SELECT atualizado_por FROM tarefas WHERE id = '70000000-0000-0000-0000-000000000002') = 'a0000000-0000-0000-0000-000000000001', 'atualizado_por = quem excluiu';
END $$;

-- 12. resultado ----------------------------------------------------------------------
DO $$ BEGIN RAISE NOTICE 'TODOS OS TESTES PASSARAM'; END $$;
