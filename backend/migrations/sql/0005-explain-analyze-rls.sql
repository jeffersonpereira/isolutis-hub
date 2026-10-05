-- EXPLAIN ANALYZE para consultas críticas com RLS ativa
-- Executar APÓS backfill e ANALYZE; compara planos com índices candidatos
-- Usar com tenants pequenos (poucos registros) e tenants grandes (muitos registros)

\echo '=== EXPLAIN ANALYZE COM RLS ATIVA ==='
\echo 'Data/hora:' :now
\echo 'Nota: Substituir UUID-EMPRESA-PEQUENA e UUID-EMPRESA-GRANDE pelos IDs reais'
\echo ''

-- Preparação: definir contexto para empresa pequena
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid;

\echo '=== EMPRESA PEQUENA ==='
\echo ''

-- Consulta 1: Lista de parceiros por empresa e nome (índice: empresa_id, nome, id)
\echo '--- Lista de parceiros por nome (empresa_id, nome, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, nome, email, criado_em
FROM parceiro
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
ORDER BY nome, id
LIMIT 50;

\echo ''
\echo '--- Lista de negócios por etapa e previsão (empresa_id, etapa, previsao, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, cliente_id, etapa, previsao, valor
FROM negocio
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
ORDER BY etapa, previsao, id
LIMIT 50;

\echo ''
\echo '--- Orçamentos por número único (empresa_id, numero) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, numero, cliente_id, valor, data_emissao
FROM orcamento
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND numero = 1  -- Substituir com número real
LIMIT 1;

\echo ''
\echo '--- Receitas por período (empresa_id, vencimento, criado_em, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, cliente_id, valor, vencimento, status
FROM lancamento_receita
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND vencimento >= '2024-01-01'::date
  AND vencimento < '2024-02-01'::date
ORDER BY vencimento, criado_em, id
LIMIT 50;

\echo ''
\echo '--- Despesas por período (empresa_id, data, criado_em, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, fornecedor, categoria_id, valor, data, status
FROM despesa
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND data >= '2024-01-01'::date
  AND data < '2024-02-01'::date
ORDER BY data, criado_em, id
LIMIT 50;

\echo ''
\echo '--- Tarefas com prioridade (empresa_id, coluna, prioridade_ordem, prazo, criado_em, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, projeto_id, coluna, prioridade_ordem, prazo, criado_em
FROM tarefa
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND coluna = 'a_fazer'
ORDER BY prioridade_ordem, prazo, criado_em, id
LIMIT 50;

\echo ''
\echo '--- Filtro de parceiros por tags (OR semântica) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT DISTINCT p.id, p.nome
FROM parceiro p
WHERE p.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND EXISTS (
    SELECT 1 FROM parceiro_tag pt
    WHERE pt.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
      AND pt.parceiro_id = p.id
      AND pt.tag_id IN ('UUID-TAG-1'::uuid, 'UUID-TAG-2'::uuid)
  )
ORDER BY p.nome
LIMIT 50;

\echo ''
\echo '--- JOIN: Negócios com cliente (dados cruzados) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT n.id, n.numero, p.nome as cliente_nome, n.etapa, n.valor
FROM negocio n
JOIN parceiro p ON n.cliente_id = p.id
WHERE n.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND p.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
ORDER BY n.numero
LIMIT 50;

\echo ''
\echo '--- Agregação: Total por categoria ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT categoria_id, COUNT(*) as quantidade, SUM(valor) as total
FROM despesa
WHERE empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid
  AND data >= '2024-01-01'::date
  AND data < '2024-12-31'::date
GROUP BY categoria_id
ORDER BY total DESC;

-- Mudar contexto para empresa grande
RESET ROLE;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-GRANDE'::uuid;

\echo ''
\echo ''
\echo '=== EMPRESA GRANDE ==='
\echo ''

-- Repetir consultas críticas para comparação
\echo '--- Lista de parceiros por nome (empresa_id, nome, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, nome, email, criado_em
FROM parceiro
WHERE empresa_id = 'UUID-EMPRESA-GRANDE'::uuid
ORDER BY nome, id
LIMIT 50;

\echo ''
\echo '--- Lista de negócios por etapa e previsão (empresa_id, etapa, previsao, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, cliente_id, etapa, previsao, valor
FROM negocio
WHERE empresa_id = 'UUID-EMPRESA-GRANDE'::uuid
ORDER BY etapa, previsao, id
LIMIT 50;

\echo ''
\echo '--- Tarefas com prioridade (empresa_id, coluna, prioridade_ordem, prazo, criado_em, id) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, projeto_id, coluna, prioridade_ordem, prazo, criado_em
FROM tarefa
WHERE empresa_id = 'UUID-EMPRESA-GRANDE'::uuid
  AND coluna = 'a_fazer'
ORDER BY prioridade_ordem, prazo, criado_em, id
LIMIT 50;

\echo ''
\echo '--- Agregação: Total por categoria (empresa grande) ---'
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT categoria_id, COUNT(*) as quantidade, SUM(valor) as total
FROM despesa
WHERE empresa_id = 'UUID-EMPRESA-GRANDE'::uuid
  AND data >= '2024-01-01'::date
  AND data < '2024-12-31'::date
GROUP BY categoria_id
ORDER BY total DESC;

\echo ''
\echo '=== ANÁLISE DE RESULTADOS ==='
\echo 'Comparar os planos entre empresa pequena e grande:'
\echo '  1. Seq Scan vs Index Scan: esperado Index Scan com índices candidatos'
\echo '  2. Heap Blks Read: validar se há many buffer reads (indício de índice ineficiente)'
\echo '  3. Actual Rows vs Estimated Rows: se muito diferentes, ANALYZE pode estar desatualizado'
\echo '  4. WAL bytes: se alto, considerar particionamento (apenas com evidência)'
\echo '  5. Planning time vs Execution time: planos complexos podem precisar simplificação'
\echo ''
\echo 'Ações:'
\echo '  - Se Seq Scan em todos os casos: índices não foram criados ou não ajudam'
\echo '  - Se Index Scan mas Actual Rows >> Estimated: falta ANALYZE ou estatísticas desatualizadas'
\echo '  - Se Heap Blks Read muito alto: considerar covering index ou INCLUDE (com medição)'
\echo '  - Se WAL muito alto: considerar particionamento (apenas em cenários de escrita pesada)'

RESET ROLE;
