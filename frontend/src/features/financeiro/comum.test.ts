import { describe, expect, it } from "vitest";
import { formatarCep, formatarDocumento } from "./comum";

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
