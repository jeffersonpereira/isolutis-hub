import { beforeAll, beforeEach, describe, expect, it } from "vitest";
import type { Permissao } from "@/api/tipos";
import { html } from "@/core/html";
import { acesso } from "./estado";
import { abaSalva, caminhoAtual, ir, registrarGuarda, registrarVista, vistaAtual } from "./nucleo";
import { aplicarRegistroDaRota, iniciarRoteador, registrarRotaDeRegistro, resolverRotaInicial } from "./roteador";

const tela = (id: string, nome: string, permissao?: Permissao) => registrarVista({ id, nome, permissao, desenhar: () => html`<p>${nome}</p>` });

beforeAll(() => {
  document.body.innerHTML = '<div id="app"><nav id="nav"></nav><header></header><main id="view"></main></div>';
  tela("painel", "Painel");
  tela("clientes", "Clientes");
  tela("orcamentos", "Orçamentos");
  tela("equipe", "Equipe", "administracao");
  iniciarRoteador();
});

beforeEach(() => {
  localStorage.clear();
  acesso.permissoes = ["base"];
  registrarGuarda(null);
  history.replaceState(null, "", "/");
});

describe("resolverRotaInicial", () => {
  it("a raiz reabre a última tela usada e corrige o endereço", () => {
    localStorage.setItem("hub.aba", "orcamentos");
    expect(resolverRotaInicial("/")).toEqual({ vista: "orcamentos", corrigir: "/orcamentos", registro: null });
  });

  it("sem tela salva, a raiz abre o painel", () => {
    expect(resolverRotaInicial("/")).toMatchObject({ vista: "painel", corrigir: "/painel" });
  });

  it("endereço explícito prevalece sobre a tela salva", () => {
    localStorage.setItem("hub.aba", "orcamentos");
    expect(resolverRotaInicial("/clientes")).toEqual({ vista: "clientes", corrigir: null, registro: null });
  });

  it("rota de registro devolve a tela e o registro a abrir", () => {
    expect(resolverRotaInicial("/clientes/abc")).toMatchObject({ vista: "clientes", registro: { tipo: "registro", id: "abc" } });
    expect(resolverRotaInicial("/clientes/novo")).toMatchObject({ vista: "clientes", registro: { tipo: "novo" } });
  });

  it("tela sem permissão cai no painel e corrige o endereço", () => {
    expect(resolverRotaInicial("/equipe")).toEqual({ vista: "painel", corrigir: "/painel", registro: null });
    acesso.permissoes = ["base", "administracao"];
    expect(resolverRotaInicial("/equipe")).toMatchObject({ vista: "equipe", corrigir: null });
  });

  it("rota inexistente cai no painel", () => {
    expect(resolverRotaInicial("/rota-que-nao-existe")).toEqual({ vista: "painel", corrigir: "/painel", registro: null });
  });

  it("a aba salva de uma tela sem permissão não é usada", () => {
    localStorage.setItem("hub.aba", "equipe");
    expect(resolverRotaInicial("/").vista).toBe("painel");
    expect(abaSalva()).toBe("equipe");
  });
});

describe("aplicarRegistroDaRota", () => {
  it("chama o abrir ou o novo da tela registrada", () => {
    const chamadas: string[] = [];
    registrarRotaDeRegistro("clientes", { novo: () => chamadas.push("novo"), abrir: (id) => chamadas.push(`abrir:${id}`) });
    aplicarRegistroDaRota({ tipo: "novo", vista: "clientes" });
    aplicarRegistroDaRota({ tipo: "registro", vista: "clientes", id: "x1" });
    aplicarRegistroDaRota(null);
    expect(chamadas).toEqual(["novo", "abrir:x1"]);
  });
});

describe("navegação e histórico", () => {
  it("ir() atualiza o endereço e não duplica a entrada ao repetir", async () => {
    await ir("clientes");
    expect(location.pathname).toBe("/clientes");
    const tamanho = history.length;
    await ir("clientes");
    expect(history.length).toBe(tamanho);
    expect(vistaAtual()).toBe("clientes");
  });

  it("Voltar do navegador mostra a tela do endereço", async () => {
    await ir("clientes");
    await ir("orcamentos");
    history.replaceState(null, "", "/clientes");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await new Promise((r) => setTimeout(r, 10));
    expect(vistaAtual()).toBe("clientes");
    expect(location.pathname).toBe("/clientes");
  });

  it("Voltar para endereço desconhecido leva ao painel e corrige a URL", async () => {
    await ir("clientes");
    history.replaceState(null, "", "/nao-existe");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await new Promise((r) => setTimeout(r, 10));
    expect(vistaAtual()).toBe("painel");
    expect(location.pathname).toBe("/painel");
  });

  it("com alterações pendentes, Voltar não sai e o endereço anterior é restaurado", async () => {
    await ir("clientes");
    registrarGuarda(() => false);
    history.replaceState(null, "", "/orcamentos");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await new Promise((r) => setTimeout(r, 10));
    expect(vistaAtual()).toBe("clientes");
    expect(location.pathname).toBe("/clientes");
    expect(caminhoAtual()).toBe("/clientes");
  });

  it("a guarda também impede a troca de tela pelo menu", async () => {
    await ir("clientes");
    registrarGuarda(() => false);
    await ir("orcamentos");
    expect(vistaAtual()).toBe("clientes");
    registrarGuarda(() => true);
    await ir("orcamentos");
    expect(vistaAtual()).toBe("orcamentos");
  });

  it("rotas reservadas não são tratadas pelo roteador", async () => {
    await ir("clientes");
    history.replaceState(null, "", "/login/2fa");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await new Promise((r) => setTimeout(r, 10));
    expect(vistaAtual()).toBe("clientes");
    expect(location.pathname).toBe("/login/2fa");
  });
});
