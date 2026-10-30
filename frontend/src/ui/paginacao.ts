import { html, type Safe } from "@/core/html";

/** Números de página a mostrar, com `null` onde há salto: 1 … 4 5 [6] 7 8 … 20. */
export function paginasVisiveis(atual: number, ultima: number): Array<number | null> {
  const mostrar = new Set([1, ultima, atual - 1, atual, atual + 1].filter((p) => p >= 1 && p <= ultima));
  const ordenadas = [...mostrar].sort((a, b) => a - b);
  const saida: Array<number | null> = [];
  ordenadas.forEach((p, i) => {
    const anterior = ordenadas[i - 1];
    if (anterior !== undefined && p - anterior > 1) saida.push(p - anterior === 2 ? p - 1 : null);
    saida.push(p);
  });
  return saida;
}

export interface OpcoesPaginacao {
  pagina: number;
  tamanho: number;
  total: number;
  tamanhos: readonly number[];
  /** Ação registrada que troca de página; o número vai em `data-valor`. */
  acaoPagina: string;
  /** Ação registrada (em `<select>`) que troca o tamanho da página. */
  acaoTamanho: string;
}

/** Rodapé de listagem paginada: intervalo exibido, páginas e tamanho da página. Não aparece sem registros. */
export function paginacao(o: OpcoesPaginacao): Safe {
  if (o.total === 0) return html``;
  const ultima = Math.max(1, Math.ceil(o.total / o.tamanho));
  const de = (o.pagina - 1) * o.tamanho + 1;
  const ate = Math.min(o.total, o.pagina * o.tamanho);
  const botao = (valor: number, rotulo: string | number, nome: string, desabilitado = false, atual = false): Safe =>
    html`<button type="button" class="pag-btn" data-act="${o.acaoPagina}" data-valor="${valor}" aria-label="${nome}"${atual ? html` aria-current="page"` : ""}${desabilitado ? html` disabled` : ""}>${rotulo}</button>`;
  return html`<nav class="pag" aria-label="Paginação">
    <span class="pag-info" role="status">Mostrando ${de}–${ate} de ${o.total}</span>
    <span class="pag-nav">${botao(o.pagina - 1, "‹", "Página anterior", o.pagina <= 1)}${paginasVisiveis(o.pagina, ultima).map((p) => (p === null ? html`<span class="pag-gap" aria-hidden="true">…</span>` : botao(p, p, `Página ${p}`, false, p === o.pagina)))}${botao(o.pagina + 1, "›", "Próxima página", o.pagina >= ultima)}</span>
    <label class="pag-tam">Por página <select data-act="${o.acaoTamanho}" aria-label="Títulos por página">${o.tamanhos.map((t) => html`<option value="${t}"${t === o.tamanho ? html` selected` : ""}>${t}</option>`)}</select></label>
  </nav>`;
}
