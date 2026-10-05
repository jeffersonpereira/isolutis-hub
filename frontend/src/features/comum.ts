import { html, type Safe } from "@/core/html";
import { conexao, podeEscrever } from "@/state/estado";

/** Botão "Novo ..." do cabeçalho (some em modo leitura ou sem dados). */
export const botaoNovo = (acao: string, rotulo: string): Safe =>
  podeEscrever() ? html`<button class="btn primary" data-act="${acao}">${rotulo}</button>` : html``;

export const semDados = (): boolean => conexao.semDados;
