import { describe, expect, it } from "vitest";
import { contasDoPlanoParaTitulo, formatarCep, formatarDocumento } from "./comum";

describe("formatação de documentos do financeiro", () => {
  it("formata CNPJ e CPF guardados só com dígitos", () => {
    expect(formatarDocumento("11222333000181")).toBe("11.222.333/0001-81");
    expect(formatarDocumento("52998224725")).toBe("529.982.247-25");
    expect(formatarDocumento("123")).toBe("123");
  });
  it("formata CEP", () => {
    expect(formatarCep("40000000")).toBe("40000-000");
    expect(formatarCep(null)).toBe("");
  });
});

describe("conta do plano para o título (RN04)", () => {
  const plano = [
    { id: "1", tipo_conta: "S", natureza: "R" },
    { id: "2", tipo_conta: "A", natureza: "R" },
    { id: "3", tipo_conta: "A", natureza: "D" },
    { id: "4", tipo_conta: "S", natureza: "D" },
  ];
  it("a pagar lista só analíticas de despesa", () => {
    expect(contasDoPlanoParaTitulo(plano, "P").map((c) => c.id)).toEqual(["3"]);
  });
  it("a receber lista só analíticas de receita", () => {
    expect(contasDoPlanoParaTitulo(plano, "R").map((c) => c.id)).toEqual(["2"]);
  });
  it("plano sem conta compatível devolve lista vazia", () => {
    expect(contasDoPlanoParaTitulo(plano.filter((c) => c.natureza === "R"), "P")).toEqual([]);
  });
});
