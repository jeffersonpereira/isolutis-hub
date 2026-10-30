import { expect, test } from "@playwright/test";
import { sessaoAberta, simularApi } from "./apoio";

// A API é simulada com page.route: só o frontend (Vite) precisa estar no ar.
const json = (corpo: unknown, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(corpo) });
const EMPRESA = { id: "e-beta", nome: "Cliente Beta", inscricao: null, status: "ativa", membros_ativos: 0, criado_em: "2026-10-30T12:00:00Z" };

test("operador cria empresa e suspende pela área da plataforma", async ({ page }) => {
  const gravados: string[] = [];
  let corpoCriacao: unknown = null;
  let status: "ativa" | "suspensa" = "ativa";
  await simularApi(page);
  // Registradas depois de simularApi: têm precedência sobre o "responde [] a tudo".
  await page.route("**/api/v1/plataforma/**", async (rota) => {
    const req = rota.request();
    const caminho = new URL(req.url()).pathname.replace(/^\/api\/v1\/plataforma/, "");
    if (caminho === "/acesso") return rota.fulfill(json({ operador: true }));
    if (req.method() !== "GET") gravados.push(`${req.method()} ${caminho}`);
    if (caminho === "/empresas" && req.method() === "GET") return rota.fulfill(json([]));
    if (caminho === "/empresas" && req.method() === "POST") {
      corpoCriacao = req.postDataJSON();
      return rota.fulfill(json(EMPRESA, 201));
    }
    if (caminho === "/empresas/e-beta/status") {
      status = (req.postDataJSON() as { status: "ativa" | "suspensa" }).status;
      return rota.fulfill(json({ ...EMPRESA, status }));
    }
    if (caminho === "/empresas/e-beta") return rota.fulfill(json({ empresa: { ...EMPRESA, status }, membros: [], convites: [] }));
    return rota.fulfill(json({}, 404));
  });
  await sessaoAberta(page);
  await page.goto("/plataforma");

  await expect(page.getByRole("heading", { name: "Empresas" })).toBeVisible();
  await expect(page.getByText("Nenhuma empresa cadastrada ainda.")).toBeVisible();

  await page.getByRole("button", { name: "Nova empresa" }).click();
  await page.getByLabel("Nome da empresa").fill("Cliente Beta");
  await page.getByLabel("Nome do administrador").fill("Dona Beta");
  await page.getByLabel("E-mail do administrador").fill("Dona@Beta.com.br");
  await page.getByRole("button", { name: "Criar empresa e enviar convite" }).click();

  await expect(page.getByRole("heading", { name: /Cliente Beta/ })).toBeVisible();
  expect(corpoCriacao).toMatchObject({ nome: "Cliente Beta", admin_nome: "Dona Beta", admin_email: "dona@beta.com.br", inscricao: null });

  await page.getByRole("button", { name: "Suspender empresa" }).click();
  await page.getByRole("button", { name: "Suspender", exact: true }).click();
  await expect(page.getByText("Empresa suspensa: os membros não conseguem entrar.")).toBeVisible();
  expect(gravados).toEqual(["POST /empresas", "PATCH /empresas/e-beta/status"]);
});

test("quem não é operador em /plataforma cai no Hub", async ({ page }) => {
  await simularApi(page);
  await page.route("**/api/v1/plataforma/acesso", (rota) => rota.fulfill(json({ operador: false })));
  await sessaoAberta(page);
  await page.goto("/plataforma");
  await expect(page.locator("#plataforma")).toHaveCount(0);
  await page.locator("#view").waitFor();
});
