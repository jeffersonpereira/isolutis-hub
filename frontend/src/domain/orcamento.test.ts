import { describe, expect, it } from "vitest";
import { textoWhatsapp, totais } from "./orcamento";
import { numeroWa, urlWa } from "./whatsapp";

const itens = [
  { descricao: "Sistema", qtd: 1, preco_unitario: 10000, mensal: false },
  { descricao: "Treino", qtd: 2, preco_unitario: 500.5, mensal: false },
  { descricao: "Manutenção", qtd: 1, preco_unitario: 800, mensal: true },
];

describe("totais do orçamento", () => {
  it("separa projeto e mensal e aplica desconto", () => {
    expect(totais(itens, 1000)).toEqual({ projeto: 10001, mensal: 800 });
  });
  it("desconto maior que o projeto não deixa negativo", () => {
    expect(totais(itens, 999999).projeto).toBe(0);
  });
  it("aceita texto digitado em formato brasileiro", () => {
    expect(totais([{ descricao: "x", qtd: 1, preco_unitario: "1.500,50" as unknown as number, mensal: false }], 0).projeto).toBe(1500.5);
  });
});

describe("whatsapp", () => {
  it("normaliza telefones brasileiros", () => {
    expect(numeroWa("(71) 99239-0992")).toBe("5571992390992");
    expect(numeroWa("+55 71 3333-4444")).toBe("557133334444");
    expect(numeroWa("123")).toBe("");
  });
  it("monta o link com texto codificado", () => {
    expect(urlWa("71992390992", "Olá & tudo bem")).toBe("https://wa.me/5571992390992?text=Ol%C3%A1%20%26%20tudo%20bem");
  });
  it("texto do orçamento", () => {
    const t = textoWhatsapp(
      { numero: "2026-001", data: "2026-01-10", validade: 15, desconto: 1000, obs: "À vista", itens },
      { nome: "Alfa", contato: "Maria Souza" },
    );
    expect(t).toContain("Olá, Maria! Segue o orçamento Nº 2026-001 da iSolutis para Alfa:");
    expect(t).toContain("• Treino (2×)");
    expect(t).toContain("Válido até 25/01/2026.");
    expect(t).toContain("/mês*");
  });
});
