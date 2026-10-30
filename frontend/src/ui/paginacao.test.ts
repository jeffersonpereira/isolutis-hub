import { describe, expect, it } from "vitest";
import { paginacao, paginasVisiveis } from "./paginacao";

describe("paginasVisiveis", () => {
  it("poucas páginas aparecem todas", () => {
    expect(paginasVisiveis(1, 1)).toEqual([1]);
    expect(paginasVisiveis(2, 4)).toEqual([1, 2, 3, 4]);
  });

  it("muitas páginas ganham saltos, sem esconder uma página só", () => {
    expect(paginasVisiveis(1, 20)).toEqual([1, 2, null, 20]);
    expect(paginasVisiveis(10, 20)).toEqual([1, null, 9, 10, 11, null, 20]);
    expect(paginasVisiveis(3, 20)).toEqual([1, 2, 3, 4, null, 20]);
    expect(paginasVisiveis(20, 20)).toEqual([1, null, 19, 20]);
  });
});

describe("paginacao", () => {
  const base = { tamanhos: [25, 50, 100], acaoPagina: "p", acaoTamanho: "t" } as const;

  it("sem registros não mostra nada", () => {
    expect(String(paginacao({ ...base, pagina: 1, tamanho: 25, total: 0 }))).toBe("");
  });

  it("mostra o intervalo e marca a página atual", () => {
    const h = String(paginacao({ ...base, pagina: 2, tamanho: 25, total: 130 }));
    expect(h).toContain("Mostrando 26–50 de 130");
    expect(h).toMatch(/data-valor="2"[^>]*aria-current="page"/);
    expect(h).toContain('<option value="25" selected>');
  });

  it("na primeira página 'anterior' fica desabilitado; na última, 'próxima'", () => {
    expect(String(paginacao({ ...base, pagina: 1, tamanho: 25, total: 60 }))).toMatch(/data-valor="0"[^>]*disabled/);
    expect(String(paginacao({ ...base, pagina: 3, tamanho: 25, total: 60 }))).toMatch(/data-valor="4"[^>]*disabled/);
  });
});
