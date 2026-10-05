import { test, expect } from '@playwright/test';

/**
 * Fluxo crítico: login → criar cliente → criar negócio → validar sync
 *
 * Testa:
 * - Autenticação
 * - Criação de registros
 * - Validação de formulários
 * - Recarregamento de dados
 * - Feedback de sucesso/erro
 */

const EMAIL_ADMIN = 'admin@test.example.com';
const SENHA = 'TestPassword123';
const CLIENTE_NOME = `Cliente E2E ${Date.now()}`;
const NEGOCIO_TITULO = `Negócio E2E ${Date.now()}`;

test.describe('Fluxo Crítico: Cliente → Negócio', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/');

    // Esperar form de login
    await expect(page.locator('input[type="email"]')).toBeVisible({ timeout: 5000 });

    // Preencher credenciais
    await page.fill('input[type="email"]', EMAIL_ADMIN);
    await page.fill('input[type="password"]', SENHA);

    // Submeter
    await page.click('button[type="submit"]');

    // Esperar navegação (dashboard)
    await expect(page.locator('h1')).toContainText(/painel|clientes|equipe/i, { timeout: 10000 });
  });

  test('criar cliente com validação', async ({ page }) => {
    // Navegar para clientes
    await page.click('button:has-text("Clientes")');
    await expect(page.locator('h1')).toContainText('Clientes', { timeout: 5000 });

    // Abrir formulário novo cliente
    await page.click('button[data-act="novoCliente"]');
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Tentar salvar vazio (validação)
    const botaoSalvar = page.locator('[data-salvar]');
    await botaoSalvar.click();

    // Deve mostrar erro de validação
    const toast = page.locator('.toast');
    await expect(toast).toBeVisible({ timeout: 2000 });
    await expect(toast).toContainText(/obrigat|informe|preench/i, { timeout: 2000 });

    // Preencher nome
    await page.fill('input[name="nome"]', CLIENTE_NOME);

    // Email opcional, mas vamos validar se preencher
    await page.fill('input[name="email"]', 'cliente@test.com');

    // Salvar
    await botaoSalvar.click();

    // Esperar spinner ou feedback de sucesso
    await expect(toast).toContainText(/salv|criado/i, { timeout: 3000 });

    // Verificar que cliente aparece na lista
    await expect(page.locator('text=' + CLIENTE_NOME)).toBeVisible({ timeout: 5000 });
  });

  test('criar negócio com cliente', async ({ page }) => {
    // Navegar para clientes
    await page.click('button:has-text("Clientes")');
    await expect(page.locator('h1')).toContainText('Clientes', { timeout: 5000 });

    // Procurar cliente existente (use o primeiro da lista)
    const primeiraLinha = page.locator('table tbody tr').first();
    await primeiraLinha.click();

    // Esperar drawer abrir
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Clicar em "Novo negócio"
    await page.click('button[data-novo-negocio]');

    // Novo drawer para negócio
    const dialog = page.locator('[role="dialog"]').last();
    await expect(dialog).toBeVisible();

    // Preencher título
    await dialog.locator('input[name="titulo"]').fill(NEGOCIO_TITULO);

    // Salvar
    await dialog.locator('[data-salvar]').click();

    // Feedback de sucesso
    const toast = page.locator('.toast');
    await expect(toast).toContainText(/salv|criado/i, { timeout: 3000 });

    // Voltar para negócios e verificar aparição
    await page.click('button:has-text("Negócios")');
    await expect(page.locator('text=' + NEGOCIO_TITULO)).toBeVisible({ timeout: 5000 });
  });

  test('validação de campos obrigatórios', async ({ page }) => {
    await page.click('button:has-text("Clientes")');
    await page.click('button[data-act="novoCliente"]');

    const dialog = page.locator('[role="dialog"]');

    // Nome é obrigatório
    await dialog.locator('[data-salvar]').click();
    await expect(page.locator('.toast')).toContainText(/nome|obrigat/i, { timeout: 2000 });

    // Preencher nome e tentar novamente
    await dialog.locator('input[name="nome"]').fill('Teste');

    // Se houver mais campos obrigatórios, toast deve aparecer
    // ou formulário deve salvar com sucesso
  });

  test('loading visual durante operação', async ({ page }) => {
    await page.click('button:has-text("Clientes")');
    await page.click('button[data-act="novoCliente"]');

    const dialog = page.locator('[role="dialog"]');
    const botaoSalvar = dialog.locator('[data-salvar]');

    // Preencher
    await dialog.locator('input[name="nome"]').fill(CLIENTE_NOME + ' - Loading');

    // Verificar que botão fica desabilitado durante operação
    const promiseClick = botaoSalvar.click();

    // Deve ter classe loading ou estar desabilitado
    await expect(botaoSalvar).toHaveAttribute('disabled', /true|disabled/, { timeout: 100 });

    await promiseClick;

    // Deve voltar ao normal após sucesso
    await expect(page.locator('.toast')).toBeVisible({ timeout: 3000 });
  });

  test('acessibilidade: labels associadas a inputs', async ({ page }) => {
    await page.click('button:has-text("Clientes")');
    await page.click('button[data-act="novoCliente"]');

    const dialog = page.locator('[role="dialog"]');

    // Labels devem ter atributo "for"
    const labels = await dialog.locator('label[for]').count();
    expect(labels).toBeGreaterThan(0);

    // Inputs devem ter "id"
    const inputs = await dialog.locator('input[id]').count();
    expect(inputs).toBeGreaterThan(0);

    // Testar navegação por teclado
    await page.keyboard.press('Tab');

    // Foco deve estar em um input
    const focused = page.locator('input:focus');
    await expect(focused).toBeVisible();
  });
});

test.describe('Multi-aba sync', () => {
  test('criar cliente em aba 1, verificar em aba 2', async ({ browser }) => {
    const context = await browser.newContext();
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Login em ambas
    for (const page of [page1, page2]) {
      await page.goto('/');
      await page.fill('input[type="email"]', EMAIL_ADMIN);
      await page.fill('input[type="password"]', SENHA);
      await page.click('button[type="submit"]');
      await page.waitForLoadState('networkidle');
    }

    // Navegar para clientes
    await page1.click('button:has-text("Clientes")');
    await page2.click('button:has-text("Clientes")');

    // Criar cliente em page1
    const nomeUnico = `SyncTest ${Date.now()}`;
    await page1.click('button[data-act="novoCliente"]');
    await page1.fill('input[name="nome"]', nomeUnico);
    await page1.click('[data-salvar]');

    // Esperar sucesso
    await expect(page1.locator('.toast')).toContainText(/salv/i, { timeout: 3000 });

    // Recarregar page2 (ou esperar sync realtime)
    await page2.reload();
    await page2.waitForLoadState('networkidle');

    // Cliente deve aparecer em page2
    await expect(page2.locator('text=' + nomeUnico)).toBeVisible({ timeout: 5000 });

    await context.close();
  });
});
