import { describe, expect, it } from "vitest";
import { caminhoDaTela, caminhoDoRegistro, caminhoNovo, resolverCaminho } from "./caminhos";

const telas = new Set(["painel", "clientes", "fin-titulos", "orcamentos"]);

describe("resolverCaminho", () => {
  it("a raiz é a raiz, com ou sem barra extra", () => {
    expect(resolverCaminho("/", telas)).toEqual({ tipo: "raiz" });
    expect(resolverCaminho("", telas)).toEqual({ tipo: "raiz" });
  });

  it("reconhece uma tela, ignorando barra final, consulta e âncora", () => {
    expect(resolverCaminho("/clientes", telas)).toEqual({ tipo: "tela", vista: "clientes" });
    expect(resolverCaminho("/clientes/", telas)).toEqual({ tipo: "tela", vista: "clientes" });
    expect(resolverCaminho("/fin-titulos?x=1#topo", telas)).toEqual({ tipo: "tela", vista: "fin-titulos" });
  });

  it("reconhece novo registro e registro existente", () => {
    expect(resolverCaminho("/clientes/novo", telas)).toEqual({ tipo: "novo", vista: "clientes" });
    expect(resolverCaminho("/clientes/abc-123", telas)).toEqual({ tipo: "registro", vista: "clientes", id: "abc-123" });
  });

  it("decodifica o id do registro", () => {
    expect(resolverCaminho("/clientes/a%20b", telas)).toEqual({ tipo: "registro", vista: "clientes", id: "a b" });
  });

  it("rotas reservadas não passam pelo roteador de telas", () => {
    for (const r of ["/login", "/login/2fa", "/convite/xyz", "/assets/app.js", "/api/v1/clientes"]) {
      expect(resolverCaminho(r, telas)).toEqual({ tipo: "reservada" });
    }
  });

  it("tela inexistente ou sem permissão é desconhecida", () => {
    expect(resolverCaminho("/rota-que-nao-existe", telas)).toEqual({ tipo: "desconhecida" });
    expect(resolverCaminho("/equipe", telas)).toEqual({ tipo: "desconhecida" });
    expect(resolverCaminho("/equipe/novo", telas)).toEqual({ tipo: "desconhecida" });
  });

  it("caminho com segmentos demais, vazios ou mal codificados é desconhecido", () => {
    expect(resolverCaminho("/clientes/a/b", telas)).toEqual({ tipo: "desconhecida" });
    expect(resolverCaminho("//clientes", telas)).toEqual({ tipo: "desconhecida" });
    expect(resolverCaminho("/clientes/%E0%A4%A", telas)).toEqual({ tipo: "desconhecida" });
  });
});

describe("construção de caminhos", () => {
  it("monta tela, novo e registro (codificando o id)", () => {
    expect(caminhoDaTela("clientes")).toBe("/clientes");
    expect(caminhoNovo("clientes")).toBe("/clientes/novo");
    expect(caminhoDoRegistro("clientes", "a b")).toBe("/clientes/a%20b");
  });

  it("o caminho montado volta como a mesma rota", () => {
    for (const id of ["id 1", "id/1", "a%b"]) {
      expect(resolverCaminho(caminhoDoRegistro("orcamentos", id), telas)).toEqual({ tipo: "registro", vista: "orcamentos", id });
    }
  });
});
