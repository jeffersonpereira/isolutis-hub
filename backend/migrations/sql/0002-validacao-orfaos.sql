-- Validação de orphans, relações cross-tenant e colisões de unicidade
-- Executar ANTES de tornar empresa_id NOT NULL e adicionar FK compostas
-- Resultado: lista de problemas a resolver manualmente

\echo '=== VALIDAÇÃO DE ÓRFÃOS E RELAÇÕES CROSS-TENANT ==='
\echo 'Data/hora:' :now
\echo ''

-- ===== Órfãos: registros sem empresa_id ou empresa inexistente =====
\echo '=== Órfãos: registros com empresa_id NULL ou inválido ==='
SELECT
    'parceiro' as tabela,
    COUNT(*) as quantidade
FROM parceiro
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'negocio',
    COUNT(*)
FROM negocio
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'orcamento',
    COUNT(*)
FROM orcamento
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'lancamento_receita',
    COUNT(*)
FROM lancamento_receita
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'despesa',
    COUNT(*)
FROM despesa
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'projeto',
    COUNT(*)
FROM projeto
WHERE empresa_id IS NULL
UNION ALL
SELECT
    'tarefa',
    COUNT(*)
FROM tarefa
WHERE empresa_id IS NULL
ORDER BY tabela;

-- ===== Relações cross-tenant: FK sem validação ainda =====
\echo ''
\echo '=== Verificação: Negócios com cliente de outra empresa (se empresa_id for adicionada a cliente) ==='
SELECT
    COUNT(*) as quantidade,
    'parceiro de cliente diferente' as tipo
FROM negocio n
WHERE n.cliente_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM parceiro p
        WHERE p.id = n.cliente_id
        -- Se parceiro tiver empresa_id, descomente:
        -- AND p.empresa_id = n.empresa_id
    );

\echo ''
\echo '=== Colisões de unicidade por empresa (numero de orcamento, se aplicável) ==='
SELECT
    empresa_id,
    numero,
    COUNT(*) as duplicados
FROM orcamento
WHERE numero IS NOT NULL
GROUP BY empresa_id, numero
HAVING COUNT(*) > 1
ORDER BY empresa_id, numero;

-- ===== Relações órfãs: items sem pai =====
\echo ''
\echo '=== Itens de orçamento sem orçamento pai ==='
SELECT
    COUNT(*) as quantidade
FROM item_orcamento io
WHERE NOT EXISTS (SELECT 1 FROM orcamento o WHERE o.id = io.orcamento_id);

\echo ''
\echo '=== Tarefas sem projeto pai ==='
SELECT
    COUNT(*) as quantidade
FROM tarefa t
WHERE t.projeto_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM projeto p WHERE p.id = t.projeto_id);

\echo ''
\echo '=== Lançamentos sem negócio/orçamento associado (se campo existir) ==='
-- Ajustar conforme schema real
SELECT
    COUNT(*) as lancamentos_orfaos
FROM lancamento_receita lr
WHERE lr.negocio_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM negocio n WHERE n.id = lr.negocio_id);

-- ===== Contagens antes do cutover (para validação pós-migração) =====
\echo ''
\echo '=== Contagens de referência (antes do cutover) ==='
SELECT 'parceiro' as tabela, COUNT(*) as total FROM parceiro
UNION ALL
SELECT 'negocio', COUNT(*) FROM negocio
UNION ALL
SELECT 'orcamento', COUNT(*) FROM orcamento
UNION ALL
SELECT 'item_orcamento', COUNT(*) FROM item_orcamento
UNION ALL
SELECT 'lancamento_receita', COUNT(*) FROM lancamento_receita
UNION ALL
SELECT 'despesa', COUNT(*) FROM despesa
UNION ALL
SELECT 'projeto', COUNT(*) FROM projeto
UNION ALL
SELECT 'tarefa', COUNT(*) FROM tarefa
ORDER BY tabela;

-- ===== Validação de IDs únicos globalmente (para renomear tabelas com segurança) =====
\echo ''
\echo '=== Colisões de ID globais (improvável, mas verificar) ==='
-- Espera-se que não haja, pois UUIDs são únicos por design
SELECT
    'parceiro' as tabela,
    COUNT(*) as duplicados
FROM (SELECT id, COUNT(*) as cnt FROM parceiro GROUP BY id HAVING COUNT(*) > 1) x
UNION ALL
SELECT
    'negocio',
    COUNT(*)
FROM (SELECT id, COUNT(*) as cnt FROM negocio GROUP BY id HAVING COUNT(*) > 1) x
ORDER BY tabela;

\echo ''
\echo '=== Validação concluída ==='
\echo 'Se houver órfãos ou relações inválidas acima, resolver antes do cutover.'
