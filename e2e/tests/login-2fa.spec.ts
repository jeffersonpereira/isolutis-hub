import { expect, test, type Page } from "@playwright/test";

// A API é simulada com page.route: só o frontend (Vite) precisa estar no ar.
const USUARIO = { id: "u1", nome: "Ana", email: "ana@isolutis.com.br", admin: true, ativo: true, totp_ativo: false };
const EMPRESA = { id: "e1", nome: "Empresa Teste", papel: "admin", onboarding_concluido: true };
const json = (corpo: unknown, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(corpo) });

async function simularApi(
  page: Page,
  opcoes: { com2fa: boolean; papel?: string; verificar?: (n: number) => ReturnType<typeof json> },
) {
  let tentativas = 0;
  await page.route("**/api/v1/**", (rota) => rota.fulfill(json([])));
  await page.route("**/api/v1/empresas", (rota) => rota.fulfill(json([{ ...EMPRESA, papel: opcoes.papel ?? EMPRESA.papel }])));
  await page.route("**/api/v1/auth/eu", (rota) => rota.fulfill(json({ ...USUARIO, totp_ativo: opcoes.com2fa })));
  await page.route("**/api/v1/auth/login", (rota) =>
    rota.fulfill(
      json(
        opcoes.com2fa
          ? { requer_2fa: true, token_temporario: "tmp.jwt.parcial" }
          : { access_token: "acesso", token_type: "bearer", usuario: USUARIO },
      ),
    ),
  );
  await page.route("**/api/v1/auth/2fa/verificar", (rota) => {
    tentativas += 1;
    const resposta = opcoes.verificar?.(tentativas) ?? json({ access_token: "acesso", token_type: "bearer", usuario: USUARIO });
    return rota.fulfill(resposta);
  });
}

async function entrar(page: Page) {
  await page.goto("/");
  await page.fill("#lgEmail", "ana@isolutis.com.br");
  await page.fill("#lgSenha", "senha-de-teste-123");
  await page.click("#lgBotao");
}

test("admin sem 2FA entra direto, sem tela de configuração obrigatória", async ({ page }) => {
  await simularApi(page, { com2fa: false });
  await entrar(page);
  await expect(page.locator("aside nav a").first()).toBeVisible();
  await expect(page.getByText("Autenticação em dois fatores obrigatória")).toHaveCount(0);
  await expect(page.locator("#lg2fa")).toHaveCount(0);
});

test("membro sem papel de administrador encontra o 2FA em Minha conta", async ({ page }) => {
  await simularApi(page, { com2fa: false, papel: "membro" });
  await entrar(page);
  await expect(page.locator("aside nav a").first()).toBeVisible();
  await expect(page.locator("aside nav a", { hasText: "Dados da empresa" })).toHaveCount(0);
  await page.locator("#btnMe").click();
  await page.getByRole("menuitem", { name: "Minha conta" }).click();
  await expect(page.getByRole("heading", { name: "Minha conta" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ativar 2FA" })).toBeVisible();
});

test("login com 2FA leva a /login/2fa sem token na URL nem em storage e conclui com o código", async ({ page }) => {
  await simularApi(page, { com2fa: true });
  await entrar(page);
  await expect(page.locator("#lg2fa")).toBeVisible();
  await expect(page).toHaveURL(/\/login\/2fa$/);
  expect(page.url()).not.toContain("tmp.jwt.parcial");
  const armazenado = await page.evaluate(() => JSON.stringify({ ...localStorage }) + JSON.stringify({ ...sessionStorage }));
  expect(armazenado).not.toContain("tmp.jwt.parcial");

  await page.fill("#lg2faCodigo", "123456");
  await page.click("#lg2faBotao");
  await expect(page.locator("aside nav a").first()).toBeVisible();
  await expect(page).not.toHaveURL(/\/login/);
});

test("acesso direto e reload em /login/2fa voltam ao login", async ({ page }) => {
  await simularApi(page, { com2fa: true });
  await page.goto("/login/2fa");
  await expect(page.locator("#lgEntrar")).toBeVisible();
  await expect(page.locator("#lg2fa")).toHaveCount(0);
  await expect(page).toHaveURL(/\/login$/);

  await entrar(page);
  await expect(page.locator("#lg2fa")).toBeVisible();
  await page.reload();
  await expect(page.locator("#lgEntrar")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

test("Voltar ao login descarta o token e permite novo login", async ({ page }) => {
  await simularApi(page, { com2fa: true });
  await entrar(page);
  await page.click("#lg2faVoltar");
  await expect(page.locator("#lg2fa")).toHaveCount(0);
  await expect(page.locator("#lgEntrar")).toBeVisible();
  await expect(page.locator("#lgEmail")).toBeFocused();
  await expect(page).toHaveURL(/\/login$/);

  await page.fill("#lgSenha", "senha-de-teste-123");
  await page.click("#lgBotao");
  await expect(page.locator("#lg2fa")).toBeVisible();
});

test("voltar do navegador em /login/2fa cancela o fluxo", async ({ page }) => {
  await simularApi(page, { com2fa: true });
  await entrar(page);
  await expect(page.locator("#lg2fa")).toBeVisible();
  await page.goBack();
  await expect(page.locator("#lg2fa")).toHaveCount(0);
  await expect(page.locator("#lgEntrar")).toBeVisible();
});

test("código incorreto mantém a tela; token invalidado (401) volta ao login com aviso", async ({ page }) => {
  const erro = (status: number, codigo: string, mensagem: string) => json({ erro: { codigo, mensagem } }, status);
  await simularApi(page, {
    com2fa: true,
    verificar: (n) =>
      n < 2
        ? erro(400, "codigo_invalido", "Código inválido. Verifique o horário do seu dispositivo ou use um backup code.")
        : erro(401, "nao_autenticado", "Muitos códigos incorretos. Entre novamente com seu e-mail e senha."),
  });
  await entrar(page);
  await page.fill("#lg2faCodigo", "000000");
  await page.click("#lg2faBotao");
  await expect(page.locator("#lgMsg")).toContainText("Código inválido");
  await expect(page.locator("#lg2fa")).toBeVisible();

  await page.fill("#lg2faCodigo", "000000");
  await page.click("#lg2faBotao");
  await expect(page.locator("#lg2fa")).toHaveCount(0);
  await expect(page.locator("#lgEntrar")).toBeVisible();
  await expect(page.locator("#lgMsg")).toContainText("Entre novamente");
});

test("alternar para código de backup ajusta o campo", async ({ page }) => {
  await simularApi(page, { com2fa: true });
  await entrar(page);
  await page.click("#lg2faAlternar");
  await expect(page.locator("#lg2faRotulo")).toHaveText("Código de backup");
  await expect(page.locator("#lg2faCodigo")).toHaveAttribute("maxlength", "12");
});
