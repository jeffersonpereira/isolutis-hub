import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { aplicarTema, CHAVE_TEMA, definirTema, iniciarTema, lerPreferencia, resolverTema, salvarPreferencia } from "./tema";

/** Simula `matchMedia("(prefers-color-scheme: dark)")` com mudança disparável. */
function simularSistema(escuro: boolean) {
  const ouvintes: Array<() => void> = [];
  const estado = { escuro };
  vi.stubGlobal("matchMedia", () => ({
    get matches() {
      return estado.escuro;
    },
    addEventListener: (_: string, fn: () => void) => void ouvintes.push(fn),
  }));
  return {
    mudarPara(novo: boolean) {
      estado.escuro = novo;
      ouvintes.forEach((fn) => fn());
    },
  };
}

const tema = () => document.documentElement.getAttribute("data-theme");

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("preferência", () => {
  it("o padrão é sistema", () => {
    expect(lerPreferencia()).toBe("sistema");
  });

  it("lê a escolha salva", () => {
    salvarPreferencia("escuro");
    expect(localStorage.getItem(CHAVE_TEMA)).toBe("escuro");
    expect(lerPreferencia()).toBe("escuro");
  });

  it("valor desconhecido vale sistema", () => {
    localStorage.setItem(CHAVE_TEMA, "roxo");
    expect(lerPreferencia()).toBe("sistema");
  });

  it("armazenamento que lança não quebra a leitura nem a gravação", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });
    expect(lerPreferencia()).toBe("sistema");
    expect(() => salvarPreferencia("claro")).not.toThrow();
  });
});

describe("resolverTema", () => {
  it.each([
    ["claro", true, "light"],
    ["claro", false, "light"],
    ["escuro", true, "dark"],
    ["escuro", false, "dark"],
    ["sistema", true, "dark"],
    ["sistema", false, "light"],
  ] as const)("%s com sistema escuro=%s resulta em %s", (pref, sistemaEscuro, esperado) => {
    expect(resolverTema(pref, sistemaEscuro)).toBe(esperado);
  });
});

describe("aplicar e definir", () => {
  it("sistema escuro aplica a paleta escura", () => {
    simularSistema(true);
    expect(aplicarTema("sistema")).toBe("dark");
    expect(tema()).toBe("dark");
  });

  it("definirTema salva e aplica na hora", () => {
    simularSistema(false);
    definirTema("escuro");
    expect(tema()).toBe("dark");
    expect(lerPreferencia()).toBe("escuro");
  });

  it("sem matchMedia cai no tema claro", () => {
    vi.stubGlobal("matchMedia", undefined);
    expect(aplicarTema("sistema")).toBe("light");
  });
});

describe("iniciarTema", () => {
  it("aplica a preferência salva ao iniciar e avisa a interface", () => {
    simularSistema(false);
    salvarPreferencia("escuro");
    const aoMudar = vi.fn();
    iniciarTema(aoMudar);
    expect(tema()).toBe("dark");
    expect(aoMudar).toHaveBeenCalledWith("escuro", "dark");
  });

  it("com preferência sistema, acompanha o sistema sem recarregar", () => {
    const sistema = simularSistema(false);
    const aoMudar = vi.fn();
    iniciarTema(aoMudar);
    expect(tema()).toBe("light");
    sistema.mudarPara(true);
    expect(tema()).toBe("dark");
    expect(aoMudar).toHaveBeenLastCalledWith("sistema", "dark");
  });

  it("com escolha manual, ignora mudanças do sistema", () => {
    const sistema = simularSistema(false);
    salvarPreferencia("claro");
    iniciarTema();
    sistema.mudarPara(true);
    expect(tema()).toBe("light");
  });
});
