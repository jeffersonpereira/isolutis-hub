import { describe, expect, it } from "vitest";
import { graficoFaturamento, passoDaEscala } from "./grafico";

describe("gráfico", () => {
  it("passo da escala é redondo", () => {
    expect(passoDaEscala(1000)).toBe(250);
    expect(passoDaEscala(40000)).toBe(10000);
    expect(passoDaEscala(9000)).toBe(2500);
  });
  it("gera uma barra por valor e escapa rótulos", () => {
    const svg = String(graficoFaturamento([{ rotulo: "Jan <b>", recebido: 100, previsto: 50, atual: true }]));
    expect(svg).toContain("<svg");
    expect(svg).toContain("recebido");
    expect(svg).toContain("previsto");
    expect(svg).not.toContain("<b>");
  });
});
