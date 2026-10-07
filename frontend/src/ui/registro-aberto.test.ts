import { beforeEach, describe, expect, it, vi } from "vitest";

const { ouvintes, recarregarFalso } = vi.hoisted(() => ({
  ouvintes: [] as Array<(recurso: string) => void>,
  recarregarFalso: vi.fn(async () => {}),
}));

// O núcleo real faz chamadas à API ao recarregar; aqui só interessam os ganchos que conflito e gravação usam.
vi.mock("@/state/nucleo", async (original) => {
  const real = await original<typeof import("@/state/nucleo")>();
  return { ...real, recarregar: recarregarFalso, aoRecarregar: (fn: (recurso: string) => void) => void ouvintes.push(fn) };
});

import { eu } from "@/state/estado";
import { iniciarAvisoDeConflito, registrarConsulta } from "./conflito";
import { gavetaAberta } from "./gaveta";
import { excluir, gravar } from "./gravacao";
import { abrirRegistro, fecharRegistro, observarRegistro, registroAberto } from "./registro-aberto";

const avisar = (recurso: string): void => ouvintes.forEach((fn) => fn(recurso));
const banner = (): HTMLElement => document.getElementById("conflito") as HTMLElement;

beforeEach(() => {
  document.body.innerHTML = '<div class="banner conflito" id="conflito" hidden></div>';
  fecharRegistro();
  observarRegistro(() => {});
  recarregarFalso.mockClear();
  eu.id = "eu-1";
  ouvintes.length = 0;
  iniciarAvisoDeConflito();
});

describe("registro aberto", () => {
  it("guarda o registro e avisa a presença; fechar limpa", () => {
    const chamadas: Array<[string | null, boolean]> = [];
    observarRegistro((titulo, editando) => chamadas.push([titulo, editando]));
    abrirRegistro("Distribuidora Alfa", { recurso: "clientes", id: "c1", versao: 3 });
    expect(registroAberto).toMatchObject({ recurso: "clientes", id: "c1", versao: 3, minhaVersao: null, excluidoPorMim: false });
    fecharRegistro();
    expect(registroAberto).toBeNull();
    expect(chamadas).toEqual([["Distribuidora Alfa", true], [null, false]]);
  });

  it("a gaveta e o formulário em página enxergam o mesmo estado (alias gavetaAberta)", () => {
    abrirRegistro("X", { recurso: "clientes", id: "c1", versao: 1 });
    expect(gavetaAberta).toBe(registroAberto);
  });

  it("uma gaveta aberta por cima de um formulário restaura o registro anterior ao fechar", () => {
    const chamadas: Array<[string | null, boolean]> = [];
    observarRegistro((titulo, editando) => chamadas.push([titulo, editando]));
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 1 });
    const anterior = abrirRegistro("Novo negócio", null);
    expect(registroAberto).toBeNull();
    fecharRegistro(anterior);
    expect(registroAberto).toMatchObject({ id: "c1" });
    expect(chamadas.at(-1)).toEqual(["Cliente", true]);
  });
});

describe("gravação com registro aberto", () => {
  it("anota a versão gravada pela própria sessão", async () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    const fechar = vi.fn();
    await gravar({ recarregar: ["clientes"], mensagem: "", operacao: async () => ({ versao: 4 }), fechar });
    expect(registroAberto?.minhaVersao).toBe(4);
    expect(recarregarFalso).toHaveBeenCalledWith("clientes");
    expect(fechar).toHaveBeenCalled();
  });

  it("excluir marca 'excluído por mim' e fecha", async () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    const fechar = vi.fn();
    await excluir({ recarregar: ["clientes"], mensagem: "", operacao: async () => {}, fechar });
    expect(registroAberto?.excluidoPorMim).toBe(true);
    expect(fechar).toHaveBeenCalled();
  });

  it("se a exclusão falhar, desfaz a marca e não fecha", async () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    const fechar = vi.fn();
    const ok = await excluir({
      recarregar: ["clientes"],
      mensagem: "",
      operacao: async () => {
        throw new Error("falhou");
      },
      fechar,
    });
    expect(ok).toBe(false);
    expect(registroAberto?.excluidoPorMim).toBe(false);
    expect(fechar).not.toHaveBeenCalled();
  });
});

describe("aviso de edição concorrente", () => {
  it("outra pessoa altera o registro aberto: mostra o aviso", () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    registrarConsulta("clientes", () => ({ id: "c1", versao: 4, atualizado_por: "outra-pessoa" }));
    avisar("clientes");
    expect(banner().hidden).toBe(false);
    expect(banner().textContent).toContain("acabou de alterar");
  });

  it("a própria gravação não gera aviso", () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    registroAberto!.minhaVersao = 4;
    registrarConsulta("clientes", () => ({ id: "c1", versao: 4, atualizado_por: "eu-1" }));
    avisar("clientes");
    expect(banner().hidden).toBe(true);
  });

  it("outra pessoa exclui o registro aberto: avisa", () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    registrarConsulta("clientes", () => undefined);
    avisar("clientes");
    expect(banner().hidden).toBe(false);
    expect(banner().textContent).toContain("excluiu este registro");
  });

  it("a exclusão feita por mim não gera aviso", () => {
    abrirRegistro("Cliente", { recurso: "clientes", id: "c1", versao: 3 });
    registroAberto!.excluidoPorMim = true;
    registrarConsulta("clientes", () => undefined);
    avisar("clientes");
    expect(banner().hidden).toBe(true);
  });

  it("mudanças em outro recurso ou sem registro aberto são ignoradas", () => {
    registrarConsulta("clientes", () => ({ id: "c1", versao: 9, atualizado_por: "outra-pessoa" }));
    avisar("clientes");
    expect(banner().hidden).toBe(true);
    abrirRegistro("Produto", { recurso: "produtos", id: "p1", versao: 1 });
    avisar("clientes");
    expect(banner().hidden).toBe(true);
  });
});
