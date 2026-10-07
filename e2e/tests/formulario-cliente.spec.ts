import { expect, test } from "@playwright/test";
import { abrir, estado, ID_CLIENTE, sessaoAberta, simularApi } from "./apoio";

let gravados: string[];

test.beforeEach(async ({ page }) => {
  gravados = [];
  await simularApi(page, { gravados });
  await sessaoAberta(page, "clientes");
});

const nome = (page: import("@playwright/test").Page) => page.locator("#view [name=nome]");

test("abrir um cliente da lista mostra o formulário em página com as seções", async ({ page }) => {
  await abrir(page, "/clientes");
  await page.locator("#view tbody tr").first().click();
  await expect.poll(() => estado(page)).toMatchObject({ url: `/clientes/${ID_CLIENTE}`, formulario: true });
  await expect(page.locator(".fp-sec h2")).toHaveText(["Dados gerais", "Contato", "Endereço", "Observações", "Relacionados"]);
  await expect(page.locator(".trilha")).toContainText("Clientes");
  await expect(page.locator(".drawer")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Conversar no WhatsApp" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Novo negócio" })).toBeVisible();
});

test("abrir pelo link mostra o formulário", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  expect(await estado(page)).toMatchObject({ formulario: true, url: `/clientes/${ID_CLIENTE}` });
});

test("recarregar o formulário o reabre, e Voltar leva à lista", async ({ page }) => {
  await abrir(page, "/clientes");
  await page.locator("#view tbody tr").first().click();
  await page.locator("[data-formulario-pagina]").waitFor();
  await page.reload();
  await page.locator("[data-formulario-pagina]").waitFor();
  expect(await estado(page)).toMatchObject({ formulario: true, url: `/clientes/${ID_CLIENTE}` });
  await page.goBack();
  await expect.poll(() => estado(page)).toMatchObject({ formulario: false, h1: "Clientes" });
});

test("a navegação entre seções leva o foco à seção", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  await page.getByRole("link", { name: "Contato" }).click();
  await expect(page.locator("#fp-contato h2")).toBeFocused();
  await expect(page.getByRole("link", { name: "Contato" })).toHaveAttribute("aria-current", "true");
});

test("o aviso de alterações aparece ao editar e some ao restaurar o valor", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  const original = await nome(page).inputValue();
  await expect(page.locator(".fp-acoes .sujo")).toBeHidden();
  await nome(page).fill("Nome alterado");
  await expect(page.locator(".fp-acoes .sujo")).toBeVisible();
  await nome(page).fill(original);
  await expect(page.locator(".fp-acoes .sujo")).toBeHidden();
});

test("com alterações, sair pelo menu pede confirmação; continuar editando preserva tudo", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  await nome(page).fill("Nome alterado");
  await page.locator("aside nav a[data-go='orcamentos']").click();
  const dialogo = page.getByRole("alertdialog");
  await expect(dialogo).toContainText("Descartar alterações?");
  await expect(page.getByRole("button", { name: "Continuar editando" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialogo).toHaveCount(0);
  await expect(nome(page)).toHaveValue("Nome alterado");
  expect((await estado(page)).url).toBe(`/clientes/${ID_CLIENTE}`);

  await page.locator("aside nav a[data-go='orcamentos']").click();
  await page.getByRole("button", { name: "Descartar e sair" }).click();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/orcamentos", formulario: false });
});

test("Voltar do navegador com alterações pergunta, e continuar editando restaura o endereço", async ({ page }) => {
  await abrir(page, "/clientes");
  await page.locator("#view tbody tr").first().click();
  await page.locator("[data-formulario-pagina]").waitFor();
  await nome(page).fill("Nome alterado");
  await page.goBack();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.getByRole("button", { name: "Continuar editando" }).click();
  await expect.poll(() => estado(page)).toMatchObject({ url: `/clientes/${ID_CLIENTE}`, formulario: true });
  await expect(nome(page)).toHaveValue("Nome alterado");
});

test("recarregar ou fechar a aba com alterações aciona a confirmação do navegador", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  await nome(page).fill("Nome alterado");
  const impedido = await page.evaluate(() => {
    const e = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(e);
    return e.defaultPrevented;
  });
  expect(impedido).toBe(true);
});

test("salvar grava, volta à lista e não deixa aviso pendente", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  await nome(page).fill("Nome alterado");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes", formulario: false, h1: "Clientes" });
  expect(gravados).toContain(`PUT /clientes/${ID_CLIENTE}`);
  await expect(page.getByRole("alertdialog")).toHaveCount(0);
});

test("novo cliente: rota própria e gravação", async ({ page }) => {
  await abrir(page, "/clientes");
  await page.getByRole("button", { name: "Novo cliente" }).first().click();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes/novo", formulario: true, h1: "Novo cliente" });
  await page.locator("#view [name=nome]").fill("Cliente Teste");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes", formulario: false });
  expect(gravados).toContain("POST /clientes");
});

test("registro inexistente mostra o estado 'não encontrado' com caminho de volta", async ({ page }) => {
  await abrir(page, "/clientes/nao-existe-123");
  await expect(page.locator("#view h1")).toHaveText("Registro não encontrado");
  await page.getByRole("link", { name: /Voltar para Clientes/ }).click();
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes", h1: "Clientes" });
});

test("excluir exige dois cliques: o primeiro só arma o botão", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  const excluir = page.locator("#fp-acoes [data-excluir]");
  await excluir.click();
  await expect(excluir).toHaveText("Confirmar exclusão");
  expect(gravados.filter((g) => g.startsWith("DELETE"))).toEqual([]);
  await excluir.click();
  await expect.poll(() => gravados.filter((g) => g.startsWith("DELETE"))).toEqual([`DELETE /clientes/${ID_CLIENTE}`]);
  await expect.poll(() => estado(page)).toMatchObject({ url: "/clientes", formulario: false });
});

test("edição curta continua na gaveta: Novo negócio abre por cima do formulário", async ({ page }) => {
  await abrir(page, `/clientes/${ID_CLIENTE}`);
  await page.getByRole("button", { name: "Novo negócio" }).click();
  await expect(page.locator(".drawer")).toBeVisible();
  await expect(page.locator("[data-formulario-pagina]")).toBeVisible();
});
