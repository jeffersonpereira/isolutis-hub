import { expect, test, type Page } from "@playwright/test";
import { abrir, estado, sessaoAberta, simularApi } from "./apoio";

test.beforeEach(async ({ page }) => {
  await simularApi(page);
  await sessaoAberta(page, "clientes");
});

const focoEm = (page: Page) => page.evaluate(() => document.activeElement?.id || document.activeElement?.textContent?.trim() || document.activeElement?.tagName);

test.describe("estrutura e navegação", () => {
  test("pontos de referência e link para pular ao conteúdo", async ({ page }) => {
    await abrir(page, "/clientes");
    await expect(page.locator("header[role=banner]")).toHaveCount(1);
    await expect(page.locator("aside nav[aria-label]")).toHaveCount(1);
    await expect(page.locator("main")).toHaveCount(1);
    await page.keyboard.press("Tab");
    expect(await page.evaluate(() => document.activeElement?.textContent)).toContain("Pular para o conteúdo");
    await page.keyboard.press("Enter");
    expect(await focoEm(page)).toBe("view");
    expect(await page.evaluate(() => location.hash)).toBe("");
  });

  test("a barra superior mostra o título da tela e acompanha a navegação", async ({ page }) => {
    await abrir(page, "/clientes");
    await expect(page.locator("#tituloTela")).toHaveText("Clientes");
    await page.locator("aside nav a[data-go='tarefas']").click();
    await expect(page.locator("#tituloTela")).toHaveText("Tarefas");
  });

  test("recolher a barra lateral mostra só ícones, mantém nomes acessíveis e lembra a escolha", async ({ page }) => {
    await abrir(page, "/clientes");
    await page.locator("#recolher").click();
    await expect(page.locator("#app")).toHaveClass(/recolhida/);
    await expect(page.locator("aside nav a[data-go='clientes']")).toHaveAttribute("title", "Clientes");
    await expect(page.locator("aside nav a[data-go='clientes'] .tx")).toBeHidden();
    await expect(page.locator("#sync")).toBeVisible();
    await page.reload();
    await page.locator("#view").waitFor();
    await expect(page.locator("#app")).toHaveClass(/recolhida/);
  });
});

test.describe("menus da barra superior", () => {
  test("menu do usuário: dados, Esc devolve o foco e Sair encerra a sessão", async ({ page }) => {
    await abrir(page, "/clientes");
    await page.locator("#btnMe").click();
    const menu = page.getByRole("menu", { name: "Menu do usuário" });
    await expect(menu).toContainText("Ana Souza");
    await expect(menu).toContainText("ana@isolutis.example");
    await page.keyboard.press("Escape");
    await expect(menu).toHaveCount(0);
    expect(await focoEm(page)).toBe("btnMe");

    await page.locator("#btnMe").click();
    await page.getByRole("menuitem", { name: "Sair" }).click();
    await expect(page.locator("#lgEntrar")).toBeVisible();
  });

  test("menu do usuário leva a Minha conta", async ({ page }) => {
    await abrir(page, "/clientes");
    await page.locator("#btnMe").click();
    await page.getByRole("menuitem", { name: "Minha conta" }).click();
    await expect.poll(() => estado(page)).toMatchObject({ url: "/conta", h1: "Minha conta" });
  });

  test("+ Novo lista as ações, funciona pelo teclado e abre o formulário", async ({ page }) => {
    await abrir(page, "/painel");
    await page.locator("#btnNovo").click();
    const itens = page.getByRole("menu", { name: "Criar novo" }).getByRole("menuitem");
    await expect(itens.first()).toHaveText("Novo cliente");
    await expect(itens.filter({ hasText: "Nova tarefa" })).toHaveCount(1);
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("ArrowUp");
    await page.keyboard.press("Enter");
    await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes/novo", formulario: true });
  });

  test("Esc fecha o + Novo e devolve o foco ao botão", async ({ page }) => {
    await abrir(page, "/painel");
    await page.locator("#btnNovo").click();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("menu", { name: "Criar novo" })).toHaveCount(0);
    expect(await focoEm(page)).toBe("btnNovo");
  });
});

test.describe("painel de menu no celular", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("abre com foco preso, fecha com Esc devolvendo o foco e fecha ao escolher uma tela", async ({ page }) => {
    await abrir(page, "/clientes");
    await expect(page.locator("#abrirMenu")).toBeVisible();
    await expect(page.locator("aside")).toBeHidden();

    await page.locator("#abrirMenu").click();
    await expect(page.locator("aside")).toBeVisible();
    await expect(page.locator("#abrirMenu")).toHaveAttribute("aria-expanded", "true");
    for (let i = 0; i < 30; i++) await page.keyboard.press("Tab");
    expect(await page.evaluate(() => !!document.activeElement?.closest("aside"))).toBe(true);

    await page.keyboard.press("Escape");
    await expect(page.locator("aside")).toBeHidden();
    expect(await focoEm(page)).toBe("abrirMenu");

    await page.locator("#abrirMenu").click();
    await page.locator("aside nav a[data-go='tarefas']").click();
    await expect(page.locator("aside")).toBeHidden();
    await expect(page.locator("#tituloTela")).toHaveText("Tarefas");
  });

  test("não há faixa horizontal de abas e a presença continua acessível no painel", async ({ page }) => {
    await abrir(page, "/clientes");
    const direcao = await page.evaluate(() => getComputedStyle(document.querySelector("aside nav")!).flexDirection);
    expect(direcao).toBe("column");
    await page.locator("#abrirMenu").click();
    await expect(page.locator("#sync")).toBeVisible();
  });
});

test.describe("paleta de comandos", () => {
  test("abre pelo atalho, filtra sem acento e vai para a tela", async ({ page }) => {
    await abrir(page, "/painel");
    await page.keyboard.press("Control+k");
    const campo = page.getByRole("combobox", { name: "Buscar telas e ações" });
    await expect(campo).toBeFocused();
    await campo.fill("orcamen");
    await expect(page.getByRole("option")).toHaveText([/Orçamentos/, /Novo orçamento/]);
    await page.keyboard.press("Enter");
    await expect.poll(() => estado(page)).toMatchObject({ url: "/orcamentos" });
    await expect(page.getByRole("dialog", { name: "Paleta de comandos" })).toHaveCount(0);
  });

  test("executa uma ação rápida", async ({ page }) => {
    await abrir(page, "/painel");
    await page.locator("#abrirPaleta").click();
    await page.getByRole("combobox").fill("novo cli");
    await page.keyboard.press("Enter");
    await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes/novo", formulario: true });
  });

  test("sem resultados, teclado e Esc devolvem o foco", async ({ page }) => {
    await abrir(page, "/painel");
    await page.locator("#abrirPaleta").focus();
    await page.keyboard.press("Enter");
    const campo = page.getByRole("combobox");
    await campo.fill("xyz");
    await expect(page.getByRole("dialog")).toContainText("Nada encontrado");
    await campo.fill("");
    await page.keyboard.press("ArrowDown");
    await expect(page.locator(".paleta [aria-selected=true]")).toHaveCount(1);
    await page.keyboard.press("Tab");
    await expect(campo).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(await focoEm(page)).toBe("abrirPaleta");
  });

  test("não lista registros: o nome de um cliente não aparece", async ({ page }) => {
    await abrir(page, "/painel");
    await page.keyboard.press("Control+k");
    await page.getByRole("combobox").fill("clinica horizonte");
    await expect(page.getByRole("option")).toHaveCount(0);
  });
});

test.describe("tema", () => {
  test("escolher Escuro aplica na hora e persiste após recarregar", async ({ page }) => {
    await abrir(page, "/clientes");
    await page.locator("#btnTema").click();
    await page.getByRole("menuitemradio", { name: "Escuro" }).click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.locator("#btnTema").click();
    await expect(page.getByRole("menuitemradio", { name: "Escuro" })).toHaveAttribute("aria-checked", "true");
    await page.keyboard.press("Escape");
    await page.reload();
    await page.locator("#view").waitFor();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });

  test("sistema escuro com preferência Sistema usa a paleta escura", async ({ browser }) => {
    const ctx = await browser.newContext({ colorScheme: "dark" });
    const page = await ctx.newPage();
    await simularApi(page);
    await sessaoAberta(page, "clientes");
    await abrir(page, "/clientes");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await ctx.close();
  });

  test("o tema é aplicado antes da aplicação carregar (sem piscar o tema errado)", async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("hub.tema", "escuro"));
    await page.route("**/src/main.ts*", (rota) => rota.abort()); // só o script do <head> pode ter aplicado o tema
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });
});
