import { describe, expect, it } from "vitest";
import { consultaParaTexto, lerConsulta } from "./consulta-url";

const padroes = { status: "todos", pag: "1", q: "" } as const;
const validadores = { status: (v: string) => ["todos", "A", "Q"].includes(v), pag: (v: string) => /^[1-9]\d*$/.test(v) };

describe("lerConsulta", () => {
  it("sem consulta devolve os padrões", () => {
    expect(lerConsulta(padroes, "", validadores)).toEqual(padroes);
  });

  it("lê os valores presentes e mantém o padrão do resto", () => {
    expect(lerConsulta(padroes, "?status=A&pag=2", validadores)).toEqual({ status: "A", pag: "2", q: "" });
  });

  it("ignora valor inválido e chave desconhecida", () => {
    expect(lerConsulta(padroes, "?pag=abc&status=X&outra=1", validadores)).toEqual(padroes);
    expect(lerConsulta(padroes, "?pag=0", validadores).pag).toBe("1");
  });

  it("decodifica texto com acento e espaço", () => {
    expect(lerConsulta(padroes, "?q=Jo%C3%A3o%20Silva", validadores).q).toBe("João Silva");
  });
});

describe("consultaParaTexto", () => {
  it("omite o que é padrão", () => {
    expect(consultaParaTexto(padroes, padroes)).toBe("");
    expect(consultaParaTexto(padroes, { status: "A", pag: "1", q: "" })).toBe("?status=A");
  });

  it("vai e volta sem perder valores", () => {
    const valores = { status: "Q", pag: "3", q: "ação & café" };
    expect(lerConsulta(padroes, consultaParaTexto(padroes, valores), validadores)).toEqual(valores);
  });
});
