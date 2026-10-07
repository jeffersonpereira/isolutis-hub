/**
 * Varredura visual: abre todas as telas do Hub (API simulada com `fixtures.json`) em claro, escuro e celular,
 * grava uma captura de cada e relata rolagem horizontal (página ou área principal) e erros de JavaScript.
 *
 * Uso (com o frontend no ar em http://localhost:5173):
 *   node e2e/visual/varredura.mjs <fase> [pasta-de-saída]     ex.: node e2e/visual/varredura.mjs antes ../capturas
 * As capturas ficam FORA do repositório (padrão: ./saida-varredura, ignorada pelo git).
 */
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const fase = process.argv[2] ?? "depois";
const saida = process.argv[3] ?? join(aqui, "saida-varredura");
const base = process.env.BASE_URL ?? "http://localhost:5173";
const fixtures = JSON.parse(readFileSync(join(aqui, "fixtures.json"), "utf-8"));
mkdirSync(saida, { recursive: true });

const USUARIO = { id: "00000000-0000-0000-0000-0000000000a1", nome: "Ana Souza", email: "ana@isolutis.example", admin: true, ativo: true, totp_ativo: false, versao: 1, senha_definida: true };
const EMPRESA = { id: "e1", nome: "iSolutis Tecnologia", papel: "admin", permissoes: ["base", "comercial", "financeiro", "administracao"], onboarding_concluido: true };
const TELAS = ["painel", "clientes", "negocios", "orcamentos", "projetos", "tarefas", "produtos", "fin-plano", "fin-contas", "fin-parceiros", "fin-titulos", "fin-fluxo", "faturamento", "relatorios", "equipe", "despesas", "empresa", "conta"];
const MODOS = [
  { id: "claro", w: 1366, h: 860, tema: "light" },
  { id: "escuro", w: 1366, h: 860, tema: "dark" },
  { id: "celular", w: 390, h: 844, tema: "light" },
];

const json = (corpo, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(corpo) });
const browser = await chromium.launch();
const relatorio = [];

for (const tela of TELAS) {
  for (const modo of MODOS) {
    const ctx = await browser.newContext({ viewport: { width: modo.w, height: modo.h } });
    const page = await ctx.newPage();
    const erros = [];
    page.on("pageerror", (e) => erros.push(e.message));
    page.on("console", (m) => m.type() === "error" && !/WebSocket|ERR_|net::|favicon/.test(m.text()) && erros.push(m.text()));
    await page.addInitScript(([aba, empresa]) => {
      localStorage.setItem("hub.token", "t");
      localStorage.setItem("hub.empresa", empresa);
      localStorage.setItem("hub.aba", aba);
      sessionStorage.setItem("hub.empresa", empresa);
    }, [tela, EMPRESA.id]);
    await page.route("**/api/v1/**", (rota) => {
      const req = rota.request();
      const caminho = new URL(req.url()).pathname.replace(/^\/api\/v1/, "");
      if (caminho === "/auth/eu") return rota.fulfill(json(USUARIO));
      if (caminho === "/empresas") return rota.fulfill(json([EMPRESA]));
      if (req.method() !== "GET") return rota.fulfill(json({}));
      return rota.fulfill(json(caminho in fixtures ? fixtures[caminho] : []));
    });
    await page.goto(base + "/");
    await page.locator("#view").waitFor();
    await page.waitForTimeout(900);
    await page.evaluate((t) => document.documentElement.setAttribute("data-theme", t), modo.tema);
    await page.waitForTimeout(150);
    // Mede a página e também a área principal (no layout novo é ela que rola)
    const transborda = await page.evaluate(() => {
      const doc = document.documentElement;
      const view = document.getElementById("view");
      return doc.scrollWidth > doc.clientWidth + 1 || (view !== null && view.scrollWidth > view.clientWidth + 1);
    });
    await page.screenshot({ path: join(saida, `${fase}-${tela}-${modo.id}.png`) });
    relatorio.push({ tela, modo: modo.id, transborda, erros: [...new Set(erros)].slice(0, 2) });
    await ctx.close();
  }
}
await browser.close();

const problemas = relatorio.filter((r) => r.transborda || r.erros.length);
console.log(`${relatorio.length} capturas em ${saida}`);
console.log(problemas.length ? "Problemas:" : "Nenhuma rolagem horizontal nem erro de JavaScript.");
for (const p of problemas) console.log(`  ${p.tela} (${p.modo}): ${p.transborda ? "rolagem horizontal; " : ""}${p.erros.join(" | ")}`);
