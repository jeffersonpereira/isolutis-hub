import { html, type Safe } from "@/core/html";

export interface OpcoesChipsFiltro {
  rotulos: readonly string[];
  /** Ação registrada que remove um chip; o índice vai em `data-i`. */
  acaoRemover: string;
  /** Ação registrada que remove todos. */
  acaoLimpar: string;
}

/** Filtros ativos como chips removíveis, com "Limpar" ao fim (só aparece com dois ou mais). */
export const chipsDeFiltro = (o: OpcoesChipsFiltro): Safe =>
  o.rotulos.length
    ? html`<div class="chips-filtro" role="group" aria-label="Filtros ativos">${o.rotulos.map(
        (r, i) => html`<button type="button" class="chip-filtro" data-act="${o.acaoRemover}" data-i="${i}" aria-label="Remover filtro: ${r}">${r}<span aria-hidden="true">×</span></button>`,
      )}${o.rotulos.length > 1 ? html`<button type="button" class="btn ghost" data-act="${o.acaoLimpar}">Limpar</button>` : ""}</div>`
    : html``;
