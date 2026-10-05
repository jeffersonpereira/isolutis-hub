# Testes E2E Multi-Tenant: Especificação

**Objetivo:** Validar isolamento de dados e funcionalidade de múltiplas empresas em cenários de usuário final.

**Framework:** Playwright (recomendado) ou Cypress

**Setup:**
- Navegador: Chrome (headless ok)
- Timeout: 30s por step
- Screenshot em caso de falha
- Executar contra staging ou cópia de produção

---

## Cenários de Teste

### Cenário 1: Login e Seleção de Empresa

**Dado:** Usuário `alice@teste.com` pertence a Empresa A e Empresa B

**Quando:**
1. Alice acessa `/` (página de login)
2. Faz login com credenciais
3. Sistema redireciona para seleção de empresa (se múltiplas)
4. Alice seleciona Empresa A

**Então:**
- [ ] Menu principal mostra "Empresa A" no cabeçalho
- [ ] URL muda para `/empresas/abc123/inicio`
- [ ] Header HTTP contém `X-Empresa-ID: abc123`

**Implementação Playwright:**
```typescript
test("login e selecionar empresa", async ({ page }) => {
  await page.goto("/");
  await page.fill('[data-testid="email"]', "alice@teste.com");
  await page.fill('[data-testid="senha"]', "senha-alice");
  await page.click('[data-testid="login-btn"]');
  
  await page.waitForNavigation();
  await expect(page).toHaveURL(/\/empresas\/.*\/inicio/);
  
  // Validar que header X-Empresa-ID é enviado
  const requests = [];
  page.on("request", req => requests.push(req));
  await page.goto("/parceiros");
  const parceiroReq = requests.find(r => r.url().includes("/parceiros"));
  expect(parceiroReq.headers()["x-empresa-id"]).toBeTruthy();
});
```

---

### Cenário 2: Dados Isolados por Empresa

**Dado:**
- Empresa A tem 5 parceiros: "Cliente A1", "Fornecedor A1", ...
- Empresa B tem 3 parceiros: "Cliente B1", "Fornecedor B1", ...
- Alice tem acesso a ambas

**Quando:**
1. Alice em Empresa A acessa `/parceiros`
2. Lista mostra 5 parceiros
3. Alice alterna para Empresa B (seletor no header)
4. Lista mostra 3 parceiros

**Então:**
- [ ] Empresa A: lista mostra exatamente 5 parceiros (nomes de A)
- [ ] Empresa B: lista mostra exatamente 3 parceiros (nomes de B)
- [ ] Nenhum parceiro de A aparece em B (e vice versa)

**Implementação Playwright:**
```typescript
test("dados isolados por empresa", async ({ page }) => {
  await page.goto("/");
  // ... login como alice ...
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-a-id");
  
  await page.goto("/parceiros");
  const parceirosA = await page.locator('[data-testid="parceiro-item"]').count();
  expect(parceirosA).toBe(5);
  
  // Validar nomes específicos de Empresa A
  expect(await page.textContent("body")).toContain("Cliente A1");
  expect(await page.textContent("body")).not.toContain("Cliente B1");
  
  // Alternar para Empresa B
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-b-id");
  await page.reload();
  
  const parceirosB = await page.locator('[data-testid="parceiro-item"]').count();
  expect(parceirosB).toBe(3);
  
  expect(await page.textContent("body")).toContain("Cliente B1");
  expect(await page.textContent("body")).not.toContain("Cliente A1");
});
```

---

### Cenário 3: Criar Dados em Empresa A (não visíveis em B)

**Dado:** Alice autenticada em Empresa A

**Quando:**
1. Alice cria novo parceiro "Novo Parceiro A" em Empresa A
2. Alice alterna para Empresa B
3. Busca "Novo Parceiro A"

**Então:**
- [ ] Parceiro criado aparece em Empresa A
- [ ] Parceiro NÃO aparece em Empresa B
- [ ] Resposta da API reflete isolamento

**Implementação Playwright:**
```typescript
test("criar dados isolados por empresa", async ({ page }) => {
  // ... login em empresa-a ...
  
  await page.goto("/parceiros");
  await page.click('[data-testid="criar-parceiro"]');
  await page.fill('[data-testid="nome"]', "Novo Parceiro A");
  await page.fill('[data-testid="email"]', "novo@a.com");
  await page.click('[data-testid="salvar"]');
  
  await expect(page.locator("text=Novo Parceiro A")).toBeVisible();
  
  // Alternar para Empresa B
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-b-id");
  await page.goto("/parceiros");
  
  await page.fill('[data-testid="busca"]', "Novo Parceiro A");
  await page.waitForTimeout(500);
  
  const resultados = await page.locator('[data-testid="parceiro-item"]').count();
  expect(resultados).toBe(0);  // Nenhum resultado em Empresa B
});
```

---

### Cenário 4: Tentar Acessar URL de Outra Empresa (403)

**Dado:** Alice tem acesso a Empresa A, NÃO tem acesso a Empresa C

**Quando:**
1. Alice tenta acessar `/empresas/empresa-c-id/parceiros` (URL direta)

**Então:**
- [ ] Resposta 403 (Forbidden)
- [ ] Mensagem: "Você não tem acesso a esta empresa"
- [ ] Redirecionado para `/` ou empresa atual

**Implementação Playwright:**
```typescript
test("acesso negado a empresa não autorizada", async ({ page }) => {
  // ... login ...
  
  // Tentar acessar empresa não autorizada
  const response = await page.goto("/empresas/empresa-c-id/parceiros");
  expect(response?.status()).toBe(403);
  
  // Deve redirecionar para login ou empresa padrão
  await expect(page).toHaveURL(/\/(login|empresas\/.*\/inicio)/);
});
```

---

### Cenário 5: Filtros com Múltiplas Tags (OR) Isolados

**Dado:**
- Empresa A: 3 parceiros com tag "Premium", 2 com tag "Gold"
- Empresa B: 2 parceiros com tag "Premium", 1 com tag "Gold"
- Alice em Empresa A

**Quando:**
1. Alice seleciona tags "Premium" OU "Gold" no filtro

**Então:**
- [ ] Retorna 5 parceiros (3 Premium + 2 Gold = Empresa A only)
- [ ] NÃO inclui os 3 de Empresa B

**Implementação Playwright:**
```typescript
test("filtro de tags com semântica OR isolado por empresa", async ({ page }) => {
  // ... setup e login ...
  
  await page.goto("/parceiros");
  
  // Selecionar múltiplas tags
  await page.click('[data-testid="tag-filter-premium"]');
  await page.click('[data-testid="tag-filter-gold"]');
  
  const parceiros = await page.locator('[data-testid="parceiro-item"]').count();
  expect(parceiros).toBe(5);  // 3 + 2 de Empresa A
  
  // Validar que contém parceiros de Empresa A
  expect(await page.textContent("body")).toContain("Premium A1");
  expect(await page.textContent("body")).not.toContain("Premium B1");
});
```

---

### Cenário 6: Mudança de Empresa na Mesma Sessão

**Dado:** Alice logada, alternando entre Empresa A e B várias vezes

**Quando:**
1. Acessa Empresa A → cria parceiro
2. Alterna para Empresa B → cria negócio
3. Alterna de volta para Empresa A
4. Alterna para Empresa B

**Então:**
- [ ] Parceiro de A aparece em A, não em B
- [ ] Negócio de B aparece em B, não em A
- [ ] Sem vazamento de dados entre empresas
- [ ] Sem cache incorreto

**Implementação Playwright:**
```typescript
test("alternância de empresa sem vazamento", async ({ page }) => {
  // ... login ...
  
  // Empresa A: criar parceiro
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-a");
  await page.goto("/parceiros");
  await criarParceiro(page, "Parceiro A1");
  
  // Empresa B: criar negócio
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-b");
  await page.goto("/negocios");
  await criarNegocio(page, "Negócio B1");
  
  // Voltar para Empresa A
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-a");
  await page.goto("/parceiros");
  expect(await page.textContent("body")).toContain("Parceiro A1");
  expect(await page.textContent("body")).not.toContain("Negócio B1");
  
  // Empresa B novamente
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-b");
  await page.goto("/negocios");
  expect(await page.textContent("body")).toContain("Negócio B1");
  expect(await page.textContent("body")).not.toContain("Parceiro A1");
});
```

---

### Cenário 7: Listagem de Empresas (GET /auth/empresas)

**Dado:** Alice tem 3 empresas associadas

**Quando:**
1. Alice acessa seletor de empresas (ou GET /auth/empresas via API)

**Então:**
- [ ] Mostra exatamente 3 empresas
- [ ] NÃO mostra outras empresas (de Bob, Carol, etc)
- [ ] Cada empresa tem ID e nome corretos

**Implementação Playwright:**
```typescript
test("listar empresas do usuário", async ({ page }) => {
  // ... login ...
  
  // Abrir seletor de empresas
  await page.click('[data-testid="empresa-selector"]');
  
  const opcoes = await page.locator('[data-testid="empresa-option"]').count();
  expect(opcoes).toBe(3);  // Alice tem 3
  
  // Validar nomes/IDs
  expect(await page.textContent('[data-testid="empresa-option"]')).toContain("Empresa A");
  expect(await page.textContent('[data-testid="empresa-option"]')).toContain("Empresa B");
});
```

---

### Cenário 8: Desativação Remove Acesso

**Dado:** Admin desativa membership de Alice em Empresa B

**Quando:**
1. Alice é membro ativo de Empresa A e B
2. Admin desativa Alice em Empresa B
3. Alice (sessão existente) alterna para Empresa B

**Então:**
- [ ] Acesso negado (403)
- [ ] Seletor não mostra mais Empresa B
- [ ] Nova sessão de Alice também não acessa B

**Implementação Playwright:**
```typescript
test("desativação de membership revoga acesso", async ({ page, context }) => {
  // ... setup com Alice em A e B ...
  
  // Admin desativa Alice em B
  const adminPage = await context.newPage();
  await autenticarComoAdmin(adminPage);
  await desativarMembership(adminPage, "alice", "empresa-b");
  
  // Alice tenta acessar B
  await page.selectOption('[data-testid="empresa-selector"]', "empresa-b");
  const response = await page.goto("/parceiros");
  expect(response?.status()).toBe(403);
  
  // Seletor não mostra mais B
  await page.reload();
  const opcoes = await page.locator('[data-testid="empresa-option"]').count();
  expect(opcoes).toBe(1);  // Só A
});
```

---

## Checklist de Execução

- [ ] Cenário 1: Login e seleção
- [ ] Cenário 2: Dados isolados (leitura)
- [ ] Cenário 3: Criar dados isolados
- [ ] Cenário 4: Acesso negado a outra empresa
- [ ] Cenário 5: Filtros isolados
- [ ] Cenário 6: Alternância sem vazamento
- [ ] Cenário 7: Listagem de empresas
- [ ] Cenário 8: Desativação de acesso

**Total esperado:** 8 testes, ~5-10 minutos cada

---

## Requisitos de Ambiente

```yaml
Node.js: 18+
Playwright: 1.40+
Base URL: http://localhost:3000 (ou staging)
API URL: http://localhost:8000 (backend)
Usuários de teste: alice@teste.com, bob@teste.com (com múltiplas empresas)
```

---

## Executar Testes

```bash
# Instalar dependências
npm install @playwright/test

# Executar todos os testes
npx playwright test tests/e2e/multi-tenant.spec.ts

# Mode headed (visualizar)
npx playwright test tests/e2e/multi-tenant.spec.ts --headed

# Modo debug
npx playwright test tests/e2e/multi-tenant.spec.ts --debug

# Gerar relatório
npx playwright show-report
```

---

## Expected Results

- **Todos os testes passam:** Isolamento de tenant está funcionando corretamente
- **Algum teste falha:** Identificar falha, rodar EXPLAIN ANALYZE, verificar RLS policies
- **Performance degradada:** Monitorar com script 0005 (EXPLAIN ANALYZE)

---

## Documentação Alternativa

Se não há framework E2E configurado, usar testes manuais com checklist:

1. Login como usuário com múltiplas empresas
2. Selecionar Empresa A → criar parceiro → validar que aparece
3. Alterna para Empresa B → listar parceiros → validar que não aparece parceiro de A
4. Tentar acessar URL de Empresa C (sem acesso) → validar 403
5. Validar seletor mostra apenas empresas do usuário
6. Verificar header X-Empresa-ID em Network tab do navegador
7. Testar filtros, buscas, relatórios por empresa

Documentar resultados em spreadsheet com data, navegador, versão.
