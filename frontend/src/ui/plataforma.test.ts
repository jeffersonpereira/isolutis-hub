import { describe, expect, it } from "vitest";
import { formatarCnpj } from "./plataforma";

describe("formatarCnpj", () => {
  it("aplica a máscara em 14 dígitos", () => {
    expect(formatarCnpj("12345678000195")).toBe("12.345.678/0001-95");
  });

  it("não inventa máscara quando não há 14 dígitos", () => {
    expect(formatarCnpj("123")).toBe("123");
    expect(formatarCnpj(null)).toBe("");
    expect(formatarCnpj(undefined)).toBe("");
  });
});
