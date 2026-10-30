import { expect, test } from "@playwright/test";
import { sessaoAberta, simularApi } from "./apoio";

// A API é simulada com page.route: só o frontend (Vite) precisa estar no ar.
const json = (corpo: unknown, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(corpo) });
const conta = (id: string, pai: string | null, codigo: string, nome: string, tipo: "A" | "S", nivel: number) => ({
  id, plano_pai_id: pai, codigo, nome, tipo_conta: tipo, natureza: "R", nivel, aporte_socio: false, possui_filhas: tipo === "S", possui_titulos: false,
});
const PLANO = [conta("c1", null, "1", "RECEITAS", "S", 1), conta("c2", "c1", "1.01", "Receitas Operacionais", "S", 2), conta("c3", "c2", "1.01.001", "Serviços", "A", 3)];

test("empresa sem plano importa o padrão pela tela", async ({ page }) => {
  const gravados: string[] = [];
  let importado = false;
  await simularApi(page);
  // Registrada depois de simularApi: tem precedência sobre as respostas das fixtures.
  await page.route("**/api/v1/financeiro/plano-contas**", (rota) => {
    const req = rota.request();
    if (req.method() === "POST") {
      gravados.push(`POST ${new URL(req.url()).pathname.replace(/^\/api\/v1/, "")}`);
      importado = true;
      return rota.fulfill(json(PLANO, 201));
    }
    return rota.fulfill(json(importado ? PLANO : []));
  });
  await sessaoAberta(page, "fin-plano");
  await page.goto("/fin-plano");

  await expect(page.getByText("Plano de contas vazio")).toBeVisible();
  await expect(page.getByRole("button", { name: "Criar a primeira conta" })).toBeVisible();

  // Cancelar não grava nada.
  await page.getByRole("button", { name: "Importar plano padrão" }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Cancelar" }).click();
  expect(gravados).toEqual([]);

  await page.getByRole("button", { name: "Importar plano padrão" }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Importar" }).click();

  await expect(page.getByRole("tree", { name: "Plano de contas" })).toBeVisible();
  await expect(page.getByText("Plano de contas vazio")).toHaveCount(0);
  expect(gravados).toEqual(["POST /financeiro/plano-contas/importar-padrao"]);
});

test("empresa com plano não vê a opção de importar", async ({ page }) => {
  await simularApi(page);
  await page.route("**/api/v1/financeiro/plano-contas**", (rota) => rota.fulfill(json(PLANO)));
  await sessaoAberta(page, "fin-plano");
  await page.goto("/fin-plano");
  await expect(page.getByRole("tree", { name: "Plano de contas" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Importar plano padrão" })).toHaveCount(0);
});
