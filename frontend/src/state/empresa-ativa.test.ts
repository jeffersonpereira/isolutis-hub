import { beforeEach, describe, expect, it } from "vitest";
import type { EmpresaAcesso } from "@/api/tipos";
import { ROTULO_PAPEL, rotuloDoPapel } from "@/domain/papeis";
import { decidirEmpresa } from "./empresa-ativa";
import { acesso, temPermissao } from "./estado";

const empresa = (id: string, papel: EmpresaAcesso["papel"] = "membro"): EmpresaAcesso => ({ id, nome: `Empresa ${id}`, papel, permissoes: ["base"] });

describe("decidirEmpresa", () => {
  it("sem nenhuma empresa, informa que não há acesso", () => {
    expect(decidirEmpresa([], "a", "a")).toEqual({ tipo: "nenhuma" });
  });

  it("mantém a empresa da aba se o usuário ainda tem acesso a ela (F5 não pergunta de novo)", () => {
    const a = empresa("a");
    expect(decidirEmpresa([a, empresa("b")], "a", "b")).toEqual({ tipo: "seguir", empresa: a });
  });

  it("aba nova (sem empresa guardada) mostra a escolha, com a última usada sugerida", () => {
    expect(decidirEmpresa([empresa("a"), empresa("b")], null, "b")).toEqual({ tipo: "escolher", sugerida: "b" });
  });

  it("mesmo com uma única empresa a escolha é exibida", () => {
    expect(decidirEmpresa([empresa("a")], null, null)).toEqual({ tipo: "escolher", sugerida: null });
  });

  it("empresa guardada que deixou de ser acessível reabre a escolha e não é usada", () => {
    expect(decidirEmpresa([empresa("b")], "a", null)).toEqual({ tipo: "escolher", sugerida: null });
  });

  it("última usada que não consta mais na lista não é sugerida", () => {
    expect(decidirEmpresa([empresa("a")], null, "removida")).toEqual({ tipo: "escolher", sugerida: null });
  });

  it("outro usuário no mesmo navegador (nada lembrado) não tem empresa pré-selecionada", () => {
    expect(decidirEmpresa([empresa("a"), empresa("b")], null, null)).toEqual({ tipo: "escolher", sugerida: null });
  });
});

describe("armazenamento da empresa por aba", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it("a empresa fica no sessionStorage (por aba) e a última usada no localStorage", async () => {
    const { sessaoToken } = await import("@/api/http");
    sessaoToken.definirEmpresa("abc");
    expect(sessionStorage.getItem("hub.empresa")).toBe("abc");
    expect(localStorage.getItem("hub.empresa")).toBe("abc");
    expect(sessaoToken.empresa()).toBe("abc");
  });

  it("trocar de empresa descarta só a da aba; a última usada continua como sugestão", async () => {
    const { sessaoToken } = await import("@/api/http");
    sessaoToken.definirEmpresa("abc");
    sessaoToken.esquecerEmpresaDaAba();
    expect(sessaoToken.empresa()).toBeNull();
    expect(sessionStorage.getItem("hub.empresa")).toBeNull();
    expect(sessaoToken.ultimaEmpresa()).toBe("abc");
  });

  it("sair limpa a empresa da aba e a última usada", async () => {
    const { sessaoToken } = await import("@/api/http");
    sessaoToken.definirEmpresa("abc");
    sessaoToken.limparEmpresas();
    expect(sessaoToken.empresa()).toBeNull();
    expect(sessaoToken.ultimaEmpresa()).toBeNull();
    expect(localStorage.getItem("hub.empresa")).toBeNull();
    expect(sessionStorage.getItem("hub.empresa")).toBeNull();
  });
});

describe("temPermissao", () => {
  it("decide só pela lista de permissões da empresa ativa", () => {
    acesso.permissoes = ["base", "financeiro"];
    expect(temPermissao("financeiro")).toBe(true);
    expect(temPermissao("comercial")).toBe(false);
    expect(temPermissao("administracao")).toBe(false);
    acesso.permissoes = [];
    expect(temPermissao("base")).toBe(false);
  });
});

describe("rótulos de papel", () => {
  it("traduz os quatro papéis e tolera valor desconhecido", () => {
    expect(Object.values(ROTULO_PAPEL)).toEqual(["Administrador", "Financeiro", "Comercial", "Membro"]);
    expect(rotuloDoPapel("financeiro")).toBe("Financeiro");
    expect(rotuloDoPapel("inventado")).toBe("—");
    expect(rotuloDoPapel(null)).toBe("—");
  });
});
