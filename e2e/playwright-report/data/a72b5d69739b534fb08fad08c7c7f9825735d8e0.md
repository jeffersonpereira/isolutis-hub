# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: fluxo-critico.spec.ts >> Fluxo Crítico: Cliente → Negócio >> loading visual durante operação
- Location: tests\fluxo-critico.spec.ts:123:3

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected pattern: /painel|clientes|equipe/i
Error: strict mode violation: locator('h1') resolved to 2 elements:
    1) <h1>Entrar</h1> aka getByRole('heading', { name: 'Entrar' })
    2) <h1>Trocar senha</h1> aka locator('#lgNova').getByText('Trocar senha')

Call log:
  - Expect "toContainText" locator('h1') with timeout 10000ms
  - waiting for locator('h1')

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - img "iSolutis" [ref=e6]
        - generic [ref=e7]: Hub Comercial
      - navigation "Áreas do Hub Comercial"
      - generic [ref=e8]: Conectando…
    - main [ref=e10]
  - generic [ref=e12]:
    - generic [ref=e13]:
      - img "iSolutis" [ref=e14]
      - generic [ref=e15]: Hub Comercial
    - generic [ref=e16]:
      - heading "Entrar" [level=1] [ref=e17]
      - generic [ref=e18]: E-mail
      - textbox "E-mail" [ref=e19]: admin@test.example.com
      - generic [ref=e20]: Senha
      - textbox "Senha" [ref=e21]: TestPassword123
      - button "Entrar" [ref=e22] [cursor=pointer]
      - paragraph [ref=e23]: Esqueceu a senha? Peça a um administrador do Hub para definir uma nova.
    - status [ref=e24]: Não foi possível concluir a operação agora. Verifique a conexão e tente de novo.
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | /**
  4   |  * Fluxo crítico: login → criar cliente → criar negócio → validar sync
  5   |  *
  6   |  * Testa:
  7   |  * - Autenticação
  8   |  * - Criação de registros
  9   |  * - Validação de formulários
  10  |  * - Recarregamento de dados
  11  |  * - Feedback de sucesso/erro
  12  |  */
  13  | 
  14  | const EMAIL_ADMIN = 'admin@test.example.com';
  15  | const SENHA = 'TestPassword123';
  16  | const CLIENTE_NOME = `Cliente E2E ${Date.now()}`;
  17  | const NEGOCIO_TITULO = `Negócio E2E ${Date.now()}`;
  18  | 
  19  | test.describe('Fluxo Crítico: Cliente → Negócio', () => {
  20  |   test.beforeEach(async ({ page }) => {
  21  |     // Login
  22  |     await page.goto('/');
  23  | 
  24  |     // Esperar form de login
  25  |     await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 5000 });
  26  | 
  27  |     // Preencher credenciais
  28  |     await page.fill('input[type="email"]', EMAIL_ADMIN);
  29  |     await page.fill('input[type="password"]', SENHA);
  30  | 
  31  |     // Submeter
  32  |     await page.click('button[type="submit"]');
  33  | 
  34  |     // Esperar navegação (dashboard)
> 35  |     await expect(page.locator('h1')).toContainText(/painel|clientes|equipe/i, { timeout: 10000 });
      |                                      ^ Error: expect(locator).toContainText(expected) failed
  36  |   });
  37  | 
  38  |   test('criar cliente com validação', async ({ page }) => {
  39  |     // Navegar para clientes
  40  |     await page.click('button:has-text("Clientes")');
  41  |     await expect(page.locator('h1')).toContainText('Clientes', { timeout: 5000 });
  42  | 
  43  |     // Abrir formulário novo cliente
  44  |     await page.click('button[data-act="novoCliente"]');
  45  |     await expect(page.locator('[role="dialog"]')).toBeVisible();
  46  | 
  47  |     // Tentar salvar vazio (validação)
  48  |     const botaoSalvar = page.locator('[data-salvar]');
  49  |     await botaoSalvar.click();
  50  | 
  51  |     // Deve mostrar erro de validação
  52  |     const toast = page.locator('.toast');
  53  |     await expect(toast).toBeVisible({ timeout: 2000 });
  54  |     await expect(toast).toContainText(/obrigat|informe|preench/i, { timeout: 2000 });
  55  | 
  56  |     // Preencher nome
  57  |     await page.fill('input[name="nome"]', CLIENTE_NOME);
  58  | 
  59  |     // Email opcional, mas vamos validar se preencher
  60  |     await page.fill('input[name="email"]', 'cliente@test.com');
  61  | 
  62  |     // Salvar
  63  |     await botaoSalvar.click();
  64  | 
  65  |     // Esperar spinner ou feedback de sucesso
  66  |     await expect(toast).toContainText(/salv|criado/i, { timeout: 3000 });
  67  | 
  68  |     // Verificar que cliente aparece na lista
  69  |     await expect(page.locator('text=' + CLIENTE_NOME)).toBeVisible({ timeout: 5000 });
  70  |   });
  71  | 
  72  |   test('criar negócio com cliente', async ({ page }) => {
  73  |     // Navegar para clientes
  74  |     await page.click('button:has-text("Clientes")');
  75  |     await expect(page.locator('h1')).toContainText('Clientes', { timeout: 5000 });
  76  | 
  77  |     // Procurar cliente existente (use o primeiro da lista)
  78  |     const primeiraLinha = page.locator('table tbody tr').first();
  79  |     await primeiraLinha.click();
  80  | 
  81  |     // Esperar drawer abrir
  82  |     await expect(page.locator('[role="dialog"]')).toBeVisible();
  83  | 
  84  |     // Clicar em "Novo negócio"
  85  |     await page.click('button[data-novo-negocio]');
  86  | 
  87  |     // Novo drawer para negócio
  88  |     const dialog = page.locator('[role="dialog"]').last();
  89  |     await expect(dialog).toBeVisible();
  90  | 
  91  |     // Preencher título
  92  |     await dialog.locator('input[name="titulo"]').fill(NEGOCIO_TITULO);
  93  | 
  94  |     // Salvar
  95  |     await dialog.locator('[data-salvar]').click();
  96  | 
  97  |     // Feedback de sucesso
  98  |     const toast = page.locator('.toast');
  99  |     await expect(toast).toContainText(/salv|criado/i, { timeout: 3000 });
  100 | 
  101 |     // Voltar para negócios e verificar aparição
  102 |     await page.click('button:has-text("Negócios")');
  103 |     await expect(page.locator('text=' + NEGOCIO_TITULO)).toBeVisible({ timeout: 5000 });
  104 |   });
  105 | 
  106 |   test('validação de campos obrigatórios', async ({ page }) => {
  107 |     await page.click('button:has-text("Clientes")');
  108 |     await page.click('button[data-act="novoCliente"]');
  109 | 
  110 |     const dialog = page.locator('[role="dialog"]');
  111 | 
  112 |     // Nome é obrigatório
  113 |     await dialog.locator('[data-salvar]').click();
  114 |     await expect(page.locator('.toast')).toContainText(/nome|obrigat/i, { timeout: 2000 });
  115 | 
  116 |     // Preencher nome e tentar novamente
  117 |     await dialog.locator('input[name="nome"]').fill('Teste');
  118 | 
  119 |     // Se houver mais campos obrigatórios, toast deve aparecer
  120 |     // ou formulário deve salvar com sucesso
  121 |   });
  122 | 
  123 |   test('loading visual durante operação', async ({ page }) => {
  124 |     await page.click('button:has-text("Clientes")');
  125 |     await page.click('button[data-act="novoCliente"]');
  126 | 
  127 |     const dialog = page.locator('[role="dialog"]');
  128 |     const botaoSalvar = dialog.locator('[data-salvar]');
  129 | 
  130 |     // Preencher
  131 |     await dialog.locator('input[name="nome"]').fill(CLIENTE_NOME + ' - Loading');
  132 | 
  133 |     // Verificar que botão fica desabilitado durante operação
  134 |     const promiseClick = botaoSalvar.click();
  135 | 
```