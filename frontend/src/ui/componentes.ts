/**
 * Peças de interface compartilhadas pelas telas: cabeçalho de página, barra de ferramentas de listagem,
 * chips de filtro e os estados vazio, de erro e de carregamento. O visual vem das classes em
 * `styles/components.css`; aqui só se monta a marcação (sempre com escape, via `html`).
 */
import { html, raw, type Safe } from "@/core/html";
import { icone } from "@/ui/icones";

export interface OpcoesCabecalho {
  titulo: string;
  descricao?: string;
  /** Botões e controles principais da tela, à direita do título. */
  acoes?: Safe;
}

export const cabecalhoDePagina = (o: OpcoesCabecalho): Safe =>
  html`<div class="head"><div><h1>${o.titulo}</h1>${o.descricao ? html`<p>${o.descricao}</p>` : ""}</div>${o.acoes ? html`<div class="tools">${o.acoes}</div>` : ""}</div>`;

export interface OpcoesBusca {
  /** Valor de `data-busca`: chave do campo em `ui`, que `main.ts` usa para refazer a tela a cada tecla. */
  chave: string;
  valor: string;
  placeholder: string;
  /** Nome acessível do campo. */
  rotulo: string;
}

export interface OpcoesBarra {
  busca?: OpcoesBusca;
  /** Chips e seletores de filtro, ao lado da busca. */
  filtros?: Safe;
  /** Texto de contagem de resultados, como "8 clientes" (anunciado por leitores de tela). */
  contagem?: string;
}

export const barraDeFerramentas = (o: OpcoesBarra): Safe =>
  html`<div class="tbar">${o.busca ? html`<input class="search" id="${o.busca.chave}" data-busca="${o.busca.chave}" type="search" aria-label="${o.busca.rotulo}" placeholder="${o.busca.placeholder}" value="${o.busca.valor}">` : ""}${o.filtros ?? ""}${o.contagem !== undefined ? html`<span class="cont" role="status">${o.contagem}</span>` : ""}</div>`;

export interface OpcoesChip {
  rotulo: string;
  /** Nome da ação registrada que alterna o filtro. */
  acao: string;
  pressionado: boolean;
  icone?: string;
}

/** Botão de filtro liga/desliga. */
export const chip = (o: OpcoesChip): Safe =>
  html`<button type="button" class="chip" data-act="${o.acao}" aria-pressed="${String(o.pressionado)}">${o.icone ? icone(o.icone) : ""}${o.rotulo}</button>`;

export interface OpcoesVazio {
  icone?: string;
  titulo: string;
  texto?: string;
  /** Ação sugerida (botão), quando o usuário pode criar o primeiro registro. */
  acao?: Safe;
}

/** Lista ou painel sem registros: explica o que falta e oferece o próximo passo. */
export const estadoVazio = (o: OpcoesVazio): Safe =>
  html`<div class="empty">${icone(o.icone ?? "vazio", { classe: "ico-grande" })}<b>${o.titulo}</b>${o.texto ?? ""}${o.acao ? html`<div>${o.acao}</div>` : ""}</div>`;

export interface OpcoesErro {
  mensagem: string;
  /** Nome da ação registrada que tenta carregar de novo. */
  acaoRepetir: string;
}

/** Falha ao carregar: diz o que houve e oferece "Tentar de novo" (a tela não fica em branco). */
export const estadoDeErro = (o: OpcoesErro): Safe =>
  html`<div class="erro-estado" role="alert">${icone("erro")}<p>${o.mensagem}</p><button type="button" class="btn" data-act="${o.acaoRepetir}">Tentar de novo</button></div>`;

/** Esqueleto de carregamento (indicadores e gráfico), anunciado como "Carregando". */
export const carregando = (rotulo = "Carregando…"): Safe =>
  raw(`<div class="skeleton-wrap" role="status" aria-label="${rotulo.replace(/"/g, "&quot;")}"><div class="skeleton-row"><div class="skeleton skeleton-kpi"></div><div class="skeleton skeleton-kpi"></div><div class="skeleton skeleton-kpi"></div></div><div class="skeleton skeleton-chart"></div></div>`);
