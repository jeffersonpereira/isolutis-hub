# Validação de Isolamento RLS sem Vazamento

**Objetivo:** Confirmar que contexto ausente, inválido ou transação subsequente no pool não expõe dados de outro tenant.

**Executar:** Após habilitar RLS nas tabelas e antes de ativar tráfego multi-tenant.

---

## Cenários de Teste

### 1. Contexto Ausente (GUC vazio/não definido)

**Esperado:** Nenhuma linha acessível em tabelas tenant-scoped.

```sql
BEGIN;
SET ROLE hub_runtime;
-- NÃO definir app.empresa_id
SELECT COUNT(*) FROM parceiro;  -- Deve retornar 0
SELECT COUNT(*) FROM negocio;   -- Deve retornar 0
ROLLBACK;
```

**Validação:** Se retornar > 0, há falha crítica de RLS.

---

### 2. Contexto Vazio (GUC = '')

**Esperado:** Nenhuma linha acessível.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = '';
SELECT COUNT(*) FROM parceiro;  -- Deve retornar 0
ROLLBACK;
```

**Validação:** Mesmo com string vazia, política deve bloquear.

---

### 3. Contexto Inválido (UUID que não existe)

**Esperado:** Nenhuma linha acessível.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = '00000000-0000-0000-0000-000000000000'::uuid;
SELECT COUNT(*) FROM parceiro;  -- Deve retornar 0
ROLLBACK;
```

**Validação:** UUID inválido retorna 0 linhas (correto, não há empresa com esse ID).

---

### 4. Contexto Correto (UUID de empresa existente)

**Esperado:** Linhas daquela empresa são visíveis.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-da-empresa-1'::uuid;
SELECT COUNT(*) FROM parceiro;  -- Deve retornar n_linhas_daquela_empresa
ROLLBACK;
```

**Validação:** Retorna exatamente a contagem de linhas daquela empresa (pré-registrada).

---

### 5. Reutilização de Conexão (context stale)

**Esperado:** Cada transação isolada, sem vazamento entre requisições.

```sql
-- Transação 1
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;
SELECT COUNT(*) as resultado_1 FROM parceiro;
ROLLBACK;

-- Transação 2 (mesma conexão)
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-2'::uuid;
SELECT COUNT(*) as resultado_2 FROM parceiro;
ROLLBACK;
```

**Validação:**
- resultado_1 = contagem parceiros empresa1
- resultado_2 = contagem parceiros empresa2
- Os valores devem ser diferentes (não vazar contexto anterior)

---

### 6. INSERT Bloqueado em Empresa Errada

**Esperado:** RLS policy bloqueia INSERT com empresa_id diferente do contexto.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

-- Tentar inserir parceiro com empresa_id = empresa-2
INSERT INTO parceiro (id, empresa_id, nome, email, ...)
VALUES ('uuid-novo', 'uuid-empresa-2'::uuid, 'Parceiro Fake', ...);
-- Esperado: FALHA (0 linhas inseridas ou POLICY VIOLATION)

ROLLBACK;
```

**Validação:** Se INSERT acontecer sem erro, há falha de RLS.

---

### 7. UPDATE para Tenant Diferente Bloqueado

**Esperado:** RLS policy bloqueia UPDATE que mude empresa_id para outro tenant.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

-- Parceiro pertence a empresa1
-- Tentar mudar para empresa2
UPDATE parceiro SET empresa_id = 'uuid-empresa-2'::uuid
WHERE id = 'uuid-parceiro-existing';
-- Esperado: FALHA (0 linhas atualizadas ou POLICY VIOLATION)

ROLLBACK;
```

**Validação:** UPDATE não deve ter efeito.

---

### 8. DELETE Bloqueado em Tenant Diferente

**Esperado:** RLS policy bloqueia DELETE de registros de outro tenant.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

-- Tentar deletar parceiro da empresa2
DELETE FROM parceiro WHERE empresa_id = 'uuid-empresa-2'::uuid AND id = 'uuid-parceiro-empresa2';
-- Esperado: FALHA (0 linhas deletadas)

ROLLBACK;
```

**Validação:** DELETE não deve ter efeito.

---

### 9. SELECT (WHERE empresa_id diferente) Bloqueado

**Esperado:** RLS policy bloqueia SELECT de outro tenant, mesmo com WHERE explícito.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

-- Tentar ler parceiro da empresa2 explicitamente
SELECT * FROM parceiro WHERE empresa_id = 'uuid-empresa-2'::uuid;
-- Esperado: 0 linhas retornadas

ROLLBACK;
```

**Validação:** Retorna 0, mesmo que pareça que há dados.

---

### 10. JOIN Cross-Tenant Bloqueado

**Esperado:** RLS policy bloqueia joins entre registros de tenants diferentes.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

-- Tentar fazer join negocio (empresa1) com parceiro (empresa2)
SELECT n.id, p.nome FROM negocio n
JOIN parceiro p ON n.cliente_id = p.id
WHERE n.empresa_id = 'uuid-empresa-1'::uuid;
-- Esperado: parceiro da empresa2 não é visível, join não retorna

ROLLBACK;
```

**Validação:** Se houver registros, então parceiro era de empresa1 (OK). Se todos os parceiros retornados forem de empresa1, está correto.

---

### 11. Agregação Isolada

**Esperado:** GROUP BY / SUM / COUNT refletem apenas o tenant do contexto.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

SELECT COUNT(*) as total_parceiros FROM parceiro;
-- Esperado: contagem apenas de empresa1

ROLLBACK;
```

**Validação:** Total deve coincidir com baseline de empresa1.

---

### 12. View com SECURITY_INVOKER Respeita Contexto

**Esperado:** Views com `security_invoker = true` filtram por contexto do caller.

```sql
BEGIN;
SET ROLE hub_runtime;
SET app.empresa_id = 'uuid-empresa-1'::uuid;

SELECT * FROM view_parceiros_ativa;  -- View tenant-aware com SECURITY_INVOKER
-- Esperado: apenas parceiros ativos de empresa1

ROLLBACK;
```

**Validação:** Resultado restrito ao tenant e critérios da view.

---

## Checklist de Execução

- [ ] Cenário 1: Contexto ausente → 0 linhas
- [ ] Cenário 2: Contexto vazio → 0 linhas
- [ ] Cenário 3: Contexto inválido → 0 linhas
- [ ] Cenário 4: Contexto correto → n linhas esperadas
- [ ] Cenário 5: Reutilização sem vazamento → contextos isolados
- [ ] Cenário 6: INSERT bloqueado cross-tenant
- [ ] Cenário 7: UPDATE bloqueado cross-tenant
- [ ] Cenário 8: DELETE bloqueado cross-tenant
- [ ] Cenário 9: SELECT WHERE bloqueado cross-tenant
- [ ] Cenário 10: JOIN cross-tenant bloqueado
- [ ] Cenário 11: Agregação isolada por tenant
- [ ] Cenário 12: View com SECURITY_INVOKER respeita contexto

---

## Resultado

**PASSOU:** Todos os cenários retornam resultado esperado → RLS implementado corretamente.

**FALHOU:** Algum cenário não passa → identificar a falha:
- RLS não habilitada em algumas tabelas
- Política RLS incorreta (faltam colunas, operador errado)
- Contexto não está sendo definido corretamente no application code
- View sem SECURITY_INVOKER expõe dados

Documentar falhas e corrigir antes de proceeder com tráfego multi-tenant.
