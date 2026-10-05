-- Testes de RLS, FK compostas e isolamento de tenant
-- Executar DEPOIS de habilitar RLS nas tabelas
-- Verificar que contexto incorreto/ausente não expõe dados

\echo '=== TESTES DE RLS E ISOLAMENTO ==='
\echo 'Data/hora:' :now
\echo ''

-- Preparação: criar role de teste (runtime)
-- Assumindo que existe role 'hub_runtime' sem ownership de tabelas
\echo '=== Configuração de teste ==='
-- CREATE ROLE hub_runtime NOINHERIT;
-- GRANT USAGE ON SCHEMA public TO hub_runtime;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hub_runtime;

-- ===== Teste 1: Leitura sem contexto RLS deve retornar 0 linhas =====
\echo ''
\echo '=== Teste 1: Leitura sem contexto RLS (deve retornar 0) ==='
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = '';  -- Contexto vazio
SELECT COUNT(*) as linhas_visiveis FROM parceiro;
ROLLBACK;

-- ===== Teste 2: Leitura com contexto correto deve retornar dados =====
\echo ''
\echo '=== Teste 2: Leitura com contexto de empresa válido (deve retornar dados) ==='
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-DA-EMPRESA-1';  -- Substituir com UUID real
SELECT COUNT(*) as linhas_visiveis FROM parceiro WHERE empresa_id = 'UUID-DA-EMPRESA-1'::uuid;
ROLLBACK;

-- ===== Teste 3: FK composta deve rejeitar relação cross-tenant =====
\echo ''
\echo '=== Teste 3: FK composta rejeita cross-tenant ==='
-- Assumindo que existem 2 empresas e um parceiro/negócio sem validação
-- Este teste falha se conseguir criar relação cross-tenant (BUG)
BEGIN;
-- INSERT INTO negocio (id, empresa_id, parceiro_id, cliente_id, ...)
-- VALUES ('uuid-negocio', 'uuid-empresa-1', (SELECT id FROM parceiro WHERE empresa_id = 'uuid-empresa-2' LIMIT 1), ...);
-- Esperado: CONSTRAINT VIOLATION
ROLLBACK;

-- ===== Teste 4: Unicidade tenant-local =====
\echo ''
\echo '=== Teste 4: Unicidade tenant-local (mesmo nome em empresas diferentes) ==='
-- Dois parceiros com mesmo nome em empresas diferentes devem ser aceitos
-- Dois parceiros com mesmo nome na MESMA empresa devem ser rejeitados
-- Este teste valida que UNIQUE(empresa_id, nome) funciona
BEGIN;
-- INSERT INTO parceiro (id, empresa_id, nome, ...)
-- VALUES ('uuid-p1', 'uuid-empresa-1', 'Acme', ...);
-- INSERT INTO parceiro (id, empresa_id, nome, ...)
-- VALUES ('uuid-p2', 'uuid-empresa-1', 'Acme', ...);
-- Esperado: CONSTRAINT VIOLATION na segunda
ROLLBACK;

-- ===== Teste 5: Sequência de orçamento por empresa/ano =====
\echo ''
\echo '=== Teste 5: Sequência de orçamento isolada por empresa/ano =====
-- Simultaneamente em mesma transação, emitir orçamentos na mesma empresa/ano
-- e em empresas/anos diferentes; verificar que não há colisão
-- Esperado: contador independente por (empresa_id, ano)
BEGIN;
-- LOCK sequencia_orcamento IN EXCLUSIVE MODE;
-- Emissão 1: empresa1, ano 2024
-- Emissão 2: empresa1, ano 2024 (deve bloquear)
-- Emissão 3: empresa2, ano 2024 (não deve bloquear, lock é por empresa/ano)
ROLLBACK;

-- ===== Teste 6: RLS bloqueia escrita em tenant errado =====
\echo ''
\echo '=== Teste 6: RLS bloqueia INSERT em empresa diferente do contexto ==='
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-1';
-- INSERT INTO parceiro (id, empresa_id, nome, ...)
-- VALUES ('uuid', 'UUID-EMPRESA-2', 'Teste', ...);
-- Esperado: POLICY VIOLATION ou nenhuma linha inserida
ROLLBACK;

-- ===== Teste 7: RLS bloqueia UPDATE cruzado =====
\echo ''
\echo '=== Teste 7: RLS bloqueia UPDATE para empresa diferente ==='
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-1';
-- UPDATE parceiro SET empresa_id = 'UUID-EMPRESA-2' WHERE id = 'uuid-parceiro-1';
-- Esperado: POLICY VIOLATION ou nenhuma linha atualizada
ROLLBACK;

-- ===== Teste 8: Conexão reutilizada não vaza contexto =====
\echo ''
\echo '=== Teste 8: Contexto isolado por transação ==='
-- Em duas transações consecutivas com contextos diferentes,
-- verificar que cada uma vê apenas seus dados
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-1';
SELECT COUNT(*) as conta_empresa_1 FROM parceiro;
ROLLBACK;

BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-2';
SELECT COUNT(*) as conta_empresa_2 FROM parceiro;
ROLLBACK;

-- ===== Teste 9: View com security_invoker =====
\echo ''
\echo '=== Teste 9: View com SECURITY_INVOKER respeita contexto ==='
-- Se houver view tenant-aware com SECURITY_INVOKER=true,
-- verificar que retorna corretamente quando filtrada por empresa_id
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'UUID-EMPRESA-1';
-- SELECT COUNT(*) FROM view_parceiros_ativa;  -- Se existir
ROLLBACK;

\echo ''
\echo '=== Testes SQL concluídos ==='
\echo 'Nota: Substituir UUID-EMPRESA-X pelos IDs reais no banco de testes'
\echo 'Nota: Descomentar INSERTs/UPDATEs e executar para validar'
