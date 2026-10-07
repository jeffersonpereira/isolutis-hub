import { readFileSync } from "node:fs";
import type { Page } from "@playwright/test";

/** Respostas simuladas de todos os GET do backend, geradas do OpenAPI (ver e2e/visual/gerar-fixtures.py). */
const fixtures = JSON.parse(readFileSync(new URL("../visual/fixtures.json", import.meta.url), "utf-8")) as Record<string, unknown>;

export const ID_CLIENTE = (fixtures["/clientes"] as Array<{ id: string }>)[0]!.id;
export const USUARIO = { id: "00000000-0000-0000-0000-0000000000a1", nome: "Ana Souza", email: "ana@isolutis.example", admin: true, ativo: true, totp_ativo: false, versao: 1, senha_definida: true };
const EMPRESA = { id: "e1", nome: "iSolutis Tecnologia", papel: "admin", onboarding_concluido: true };

const json = (corpo: unknown, status = 200) => ({ status, contentType: "application/json", body: JSON.stringify(corpo) });

export interface OpcoesApi {
  /** Login pede o código do 2FA. */
  com2fa?: boolean;
  papel?: "admin" | "membro";
  /** Recebe "METODO /caminho" de cada escrita (POST, PUT, DELETE…). */
  gravados?: string[];
}

/** Simula a API inteira: leituras vêm das fixtures; escritas são registradas e respondem com sucesso. */
export async function simularApi(page: Page, o: OpcoesApi = {}): Promise<void> {
  await page.route("**/api/v1/**", (rota) => {
    const req = rota.request();
    const caminho = new URL(req.url()).pathname.replace(/^\/api\/v1/, "");
    if (caminho === "/auth/eu") return rota.fulfill(json({ ...USUARIO, totp_ativo: false }));
    if (caminho === "/auth/login") {
      return rota.fulfill(json(o.com2fa ? { requer_2fa: true, token_temporario: "tmp.jwt.parcial" } : { access_token: "acesso", token_type: "bearer", usuario: USUARIO }));
    }
    if (caminho === "/auth/2fa/verificar") return rota.fulfill(json({ access_token: "acesso", token_type: "bearer", usuario: USUARIO }));
    if (caminho === "/empresas") return rota.fulfill(json([{ ...EMPRESA, papel: o.papel ?? "admin" }]));
    if (/^\/clientes\/[^/]+\/relacionados$/.test(caminho)) return rota.fulfill(json({ lancamentos: 4, recebido: 48200 }));
    if (req.method() !== "GET") {
      o.gravados?.push(`${req.method()} ${caminho}`);
      return rota.fulfill(req.method() === "DELETE" ? { status: 204, body: "" } : json({ ...(fixtures["/clientes"] as unknown[])[0] as object, versao: 8 }));
    }
    return rota.fulfill(json(caminho in fixtures ? fixtures[caminho] : []));
  });
}

/**
 * Deixa a sessão já aberta (token, empresa e tela inicial) na primeira carga da aba. Em cargas seguintes
 * não sobrescreve nada, então recarregar, sair e a "última tela usada" se comportam como no uso real.
 */
export async function sessaoAberta(page: Page, aba = "painel"): Promise<void> {
  await page.addInitScript((telaInicial) => {
    if (sessionStorage.getItem("e2e.semeado")) return;
    sessionStorage.setItem("e2e.semeado", "1");
    localStorage.setItem("hub.token", "acesso");
    localStorage.setItem("hub.empresa", "e1");
    localStorage.setItem("hub.aba", telaInicial);
  }, aba);
}

/** Abre a aplicação num caminho e espera a área principal desenhar. */
export async function abrir(page: Page, caminho = "/"): Promise<void> {
  await page.goto(caminho);
  await page.locator("#view").waitFor();
  await page.waitForTimeout(600);
}

export const estado = (page: Page) =>
  page.evaluate(() => ({
    url: location.pathname,
    tela: document.getElementById("tituloTela")?.textContent ?? "",
    h1: document.querySelector("#view h1")?.textContent ?? "",
    formulario: !!document.querySelector("[data-formulario-pagina]"),
  }));
