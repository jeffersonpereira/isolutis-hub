import { expect, test } from "@playwright/test";
import { abrir, estado, sessaoAberta, simularApi } from "./apoio";

test.beforeEach(async ({ page }) => {
  await simularApi(page);
});

test("navegar pelo menu atualiza a URL, e Voltar e Avançar acompanham", async ({ page }) => {
  await sessaoAberta(page);
  await abrir(page, "/clientes");
  expect(await estado(page)).toMatchObject({ url: "/clientes", tela: "Clientes" });

  await page.locator("aside nav a[data-go='orcamentos']").click();
  await expect.poll(() => estado(page).then((e) => e.url)).toBe("/orcamentos");

  await page.goBack();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes", tela: "Clientes" });
  await page.goForward();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/orcamentos", tela: "Orçamentos" });
});

test("link direto abre a tela, e recarregar a mantém", async ({ page }) => {
  await sessaoAberta(page);
  await abrir(page, "/fin-titulos");
  expect(await estado(page)).toMatchObject({ url: "/fin-titulos", tela: "Títulos Financeiros" });
  await page.reload();
  await page.locator("#view h1").waitFor();
  expect(await estado(page)).toMatchObject({ url: "/fin-titulos", tela: "Títulos Financeiros" });
});

test("endereço desconhecido leva ao painel e corrige a URL", async ({ page }) => {
  await sessaoAberta(page);
  await abrir(page, "/rota-que-nao-existe");
  expect(await estado(page)).toMatchObject({ url: "/painel", tela: "Painel" });
});

test("a raiz reabre a última tela, mas um endereço explícito prevalece", async ({ page }) => {
  await sessaoAberta(page, "orcamentos");
  await abrir(page, "/");
  expect(await estado(page)).toMatchObject({ url: "/orcamentos", tela: "Orçamentos" });
  await abrir(page, "/clientes");
  expect(await estado(page)).toMatchObject({ url: "/clientes", tela: "Clientes" });
});

test("tela sem permissão cai no painel", async ({ page }) => {
  await page.unroute("**/api/v1/**");
  await simularApi(page, { papel: "membro" });
  await sessaoAberta(page);
  await abrir(page, "/equipe");
  expect(await estado(page)).toMatchObject({ url: "/painel", tela: "Painel" });
});

test("a paleta de comandos navega e atualiza a URL", async ({ page }) => {
  await sessaoAberta(page, "clientes");
  await abrir(page, "/clientes");
  await page.keyboard.press("Control+k");
  await page.keyboard.type("fluxo");
  await page.keyboard.press("Enter");
  await expect.poll(() => estado(page)).toMatchObject({ url: "/fin-fluxo", tela: "Fluxo de Caixa" });
});

test("link direto atravessa o login com 2FA", async ({ page }) => {
  await page.unroute("**/api/v1/**");
  await simularApi(page, { com2fa: true });
  await page.goto("/fin-titulos");
  await page.fill("#lgEmail", "ana@isolutis.example");
  await page.fill("#lgSenha", "senha-de-teste-123");
  await page.click("#lgBotao");
  await expect(page.locator("#lg2fa")).toBeVisible();
  await expect(page).toHaveURL(/\/login\/2fa$/);
  await page.fill("#lg2faCodigo", "123456");
  await page.click("#lg2faBotao");
  await page.locator("#view h1").waitFor();
  expect(await estado(page)).toMatchObject({ url: "/fin-titulos", tela: "Títulos Financeiros" });
});

test("link direto atravessa o login sem 2FA", async ({ page }) => {
  await page.goto("/negocios");
  await page.fill("#lgEmail", "ana@isolutis.example");
  await page.fill("#lgSenha", "senha-de-teste-123");
  await page.click("#lgBotao");
  await page.locator("#view h1").waitFor();
  expect(await estado(page)).toMatchObject({ url: "/negocios", tela: "Funil de Vendas" });
});
