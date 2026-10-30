import { describe, expect, it } from "vitest";
import {
  aplicarAtalho, atalhoAtivo, chipsDeFiltro, contarAvancados, filtrosDaApi, lerConsultaTitulos, limparChaves, PADROES_TITULOS, ultimaPagina, valorParaConsulta,
} from "./titulos-consulta";

const HOJE = "2026-11-02";
const nomes = { parceiro: () => "Acme", plano: () => "2.01 Salário", conta: () => "Itaú" };

describe("lerConsultaTitulos", () => {
  it("sem URL usa os padrões", () => {
    expect(lerConsultaTitulos("")).toEqual(PADROES_TITULOS);
  });

  it("ignora valores inválidos", () => {
    const c = lerConsultaTitulos("?status=Z&pag=abc&tam=7&ordem=x&venc_de=ontem&vmin=-3&parceiro=1");
    expect(c).toEqual(PADROES_TITULOS);
  });

  it("lê filtros válidos", () => {
    const c = lerConsultaTitulos("?status=A&venc_ate=2026-11-07&tam=50&pag=2&ordem=valor&sentido=desc");
    expect(c).toMatchObject({ status: "A", venc_ate: "2026-11-07", tam: "50", pag: "2", ordem: "valor", sentido: "desc" });
  });
});

describe("atalhos", () => {
  it("atrasados: abertos com vencimento até ontem", () => {
    const c = aplicarAtalho({ ...PADROES_TITULOS, pag: "3", venc_de: "2026-01-01" }, "atrasados", HOJE);
    expect(c).toMatchObject({ status: "A", venc_de: "", venc_ate: "2026-11-01", pag: "1" });
  });

  it("próximos 7 dias: de hoje a hoje + 6", () => {
    expect(aplicarAtalho(PADROES_TITULOS, "semana", HOJE)).toMatchObject({ status: "A", venc_de: HOJE, venc_ate: "2026-11-08" });
  });

  it("reconhece qual atalho está ativo", () => {
    expect(atalhoAtivo(aplicarAtalho(PADROES_TITULOS, "atrasados", HOJE), HOJE)).toBe("atrasados");
    expect(atalhoAtivo(aplicarAtalho(PADROES_TITULOS, "semana", HOJE), HOJE)).toBe("semana");
    expect(atalhoAtivo(PADROES_TITULOS, HOJE)).toBeNull();
    expect(atalhoAtivo({ ...aplicarAtalho(PADROES_TITULOS, "semana", HOJE), status: "Q" }, HOJE)).toBeNull();
  });
});

describe("filtrosDaApi", () => {
  it("omite o que não filtra", () => {
    expect(filtrosDaApi(PADROES_TITULOS)).toEqual({ ordem: "vencimento", sentido: "asc" });
  });

  it("traduz as chaves da URL para os parâmetros da API", () => {
    const c = { ...PADROES_TITULOS, tipo: "P", q: "acme", venc_de: "2026-11-01", venc_ate: "2026-11-07", vmin: "10", vmax: "99.5", origem: "avulsos", parceiro: "p1" };
    expect(filtrosDaApi(c)).toMatchObject({
      tipo: "P", busca: "acme", de: "2026-11-01", ate: "2026-11-07", valor_min: "10", valor_max: "99.5", recorrente: "false", parceiro_id: "p1",
    });
    expect(filtrosDaApi({ ...PADROES_TITULOS, origem: "recorrentes" }).recorrente).toBe("true");
  });
});

describe("filtros avançados e chips", () => {
  it("conta só os filtros da gaveta", () => {
    expect(contarAvancados({ ...PADROES_TITULOS, status: "A", q: "x" })).toBe(0);
    expect(contarAvancados({ ...PADROES_TITULOS, venc_de: "2026-11-01", venc_ate: "2026-11-07", origem: "recorrentes" })).toBe(3);
  });

  it("um chip por filtro, com período e faixa agrupados e sem Tipo e Situação", () => {
    const chips = chipsDeFiltro(
      { ...PADROES_TITULOS, tipo: "R", status: "A", q: "ac", parceiro: "p", venc_de: "2026-11-01", venc_ate: "2026-11-07", vmax: "500" },
      nomes,
    );
    expect(chips.map((c) => c.rotulo)).toEqual(["Busca: ac", "Parceiro: Acme", "Vencimento 01/11/2026 a 07/11/2026", expect.stringContaining("Valor até")]);
    expect(chips[2]!.chaves).toEqual(["venc_de", "venc_ate"]);
  });

  it("remover um chip limpa só aquele filtro e volta à primeira página", () => {
    const c = { ...PADROES_TITULOS, parceiro: "p", plano: "q", pag: "4" };
    expect(limparChaves(c, ["parceiro"])).toEqual({ ...PADROES_TITULOS, plano: "q" });
  });
});

describe("auxiliares", () => {
  it("converte o valor digitado para o formato da URL", () => {
    expect(valorParaConsulta("1.500,50")).toBe("1500.5");
    expect(valorParaConsulta("")).toBe("");
    expect(valorParaConsulta("0,00")).toBe("");
  });

  it("última página existente", () => {
    expect(ultimaPagina(0, 25)).toBe(1);
    expect(ultimaPagina(25, 25)).toBe(1);
    expect(ultimaPagina(26, 25)).toBe(2);
    expect(ultimaPagina(130, 50)).toBe(3);
  });
});
