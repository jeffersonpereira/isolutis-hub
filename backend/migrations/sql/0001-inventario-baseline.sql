-- Inventário de tabelas tenant-scoped: contagem, tamanho, índices, constraints
-- Executar contra banco de produção representativo antes de cutover
-- Resultado: baseline para comparação pós-migração e planejamento de índices

\echo '=== INVENTÁRIO DE TABELAS TENANT-SCOPED ==='
\echo 'Data/hora:' :now
\echo ''

-- ===== Contagem de linhas por tabela =====
\echo '=== Contagem de linhas por tabela ==='
SELECT
    schemaname,
    tablename,
    n_live_tup as linhas,
    n_dead_tup as mortas,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho_total
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- ===== Distribuição de linhas por empresa (para tabelas com empresa_id) =====
\echo ''
\echo '=== Distribuição de linhas por empresa ==='
SELECT
    'parceiro' as tabela,
    COUNT(*) as total,
    COUNT(DISTINCT empresa_id) as empresas,
    MIN(empresa_id::text) as primeira_empresa,
    MAX(empresa_id::text) as ultima_empresa
FROM parceiro
UNION ALL
SELECT
    'negocio',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM negocio
UNION ALL
SELECT
    'orcamento',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM orcamento
UNION ALL
SELECT
    'lancamento_receita',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM lancamento_receita
UNION ALL
SELECT
    'despesa',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM despesa
UNION ALL
SELECT
    'projeto',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM projeto
UNION ALL
SELECT
    'tarefa',
    COUNT(*),
    COUNT(DISTINCT empresa_id),
    MIN(empresa_id::text),
    MAX(empresa_id::text)
FROM tarefa
ORDER BY tabela;

-- ===== Índices por tabela =====
\echo ''
\echo '=== Índices por tabela (tenant-scoped) ==='
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('parceiro', 'negocio', 'orcamento', 'lancamento_receita', 'despesa', 'projeto', 'tarefa')
ORDER BY tablename, indexname;

-- ===== Constraints (PK, FK, UNIQUE) =====
\echo ''
\echo '=== Constraints por tabela ==='
SELECT
    constraint_name,
    table_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'public'
    AND table_name IN ('parceiro', 'negocio', 'orcamento', 'lancamento_receita', 'despesa', 'projeto', 'tarefa')
ORDER BY table_name, constraint_type, constraint_name;

-- ===== Colunas com empresa_id (verificar quais tabelas operacionais já têm) =====
\echo ''
\echo '=== Presença de empresa_id em tabelas operacionais ==='
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND column_name = 'empresa_id'
    AND table_name IN ('parceiro', 'negocio', 'orcamento', 'lancamento_receita', 'despesa', 'projeto', 'tarefa', 'produto', 'categoria_despesa')
ORDER BY table_name;

-- ===== Estatísticas para planejar índices =====
\echo ''
\echo '=== Estatísticas detalhadas ==='
-- Parceiros: candidato a índice (empresa_id, nome, id)
SELECT
    'parceiro' as tabela,
    COUNT(*) as total,
    COUNT(DISTINCT nome) as nomes_unicos,
    COUNT(DISTINCT empresa_id) as empresas,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT empresa_id), 0), 2) as media_por_empresa
FROM parceiro;

-- Negócios: candidato a índices (empresa_id, etapa, previsao, id)
SELECT
    'negocio' as tabela,
    COUNT(*) as total,
    COUNT(DISTINCT etapa) as etapas_unicas,
    COUNT(DISTINCT empresa_id) as empresas,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT empresa_id), 0), 2) as media_por_empresa
FROM negocio;

-- Orçamentos: candidato (empresa_id, numero) único
SELECT
    'orcamento' as tabela,
    COUNT(*) as total,
    COUNT(DISTINCT numero) as numeros_unicos,
    COUNT(DISTINCT empresa_id) as empresas,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT empresa_id), 0), 2) as media_por_empresa
FROM orcamento;

-- Tarefas: candidato (empresa_id, coluna, prioridade_ordem, prazo, criado_em, id)
SELECT
    'tarefa' as tabela,
    COUNT(*) as total,
    COUNT(DISTINCT coluna) as colunas_unicas,
    COUNT(DISTINCT empresa_id) as empresas,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT empresa_id), 0), 2) as media_por_empresa
FROM tarefa;

\echo ''
\echo '=== Inventário concluído ==='
