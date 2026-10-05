import { describe, expect, it } from "vitest";
import { centavos, numero, paraCampo } from "./numero";

describe("numero", () => {
  it("lê formato brasileiro", () => {
    expect(numero("1.500,50")).toBe(1500.5);
    expect(numero("1500,5")).toBe(1500.5);
    expect(numero("0,99")).toBe(0.99);
  });
  it("não corrompe ponto decimal (bug do sistema anterior: 1500.50 virava 150050)", () => {
    expect(numero("1500.50")).toBe(1500.5);
    expect(numero("12.5")).toBe(12.5);
  });
  it("trata ponto de milhar", () => {
    expect(numero("1.500")).toBe(1500);
    expect(numero("1.234.567")).toBe(1234567);
  });
  it("aceita número, vazio, lixo e negativo", () => {
    expect(numero(42.5)).toBe(42.5);
    expect(numero("")).toBe(0);
    expect(numero(null)).toBe(0);
    expect(numero("abc")).toBe(0);
    expect(numero("-1.000,50")).toBe(-1000.5);
    expect(numero("R$ 2.000,00")).toBe(2000);
  });
});

describe("centavos / paraCampo", () => {
  it("arredonda para centavos", () => {
    expect(centavos(1.005)).toBe(1.01);
    expect(centavos(0.1 + 0.2)).toBe(0.3);
  });
  it("formata para campo", () => {
    expect(paraCampo(1500.5)).toBe("1500,5");
    expect(paraCampo(0)).toBe("");
    expect(paraCampo(null)).toBe("");
  });
});
