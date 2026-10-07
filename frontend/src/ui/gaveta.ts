import { $, $$ } from "@/core/dom";
import { esc, type Safe } from "@/core/html";
import { ligarExclusaoEmDoisCliques } from "./exclusao";
import { abrirRegistro, fecharRegistro } from "./registro-aberto";

/**
 * Gaveta lateral (onde abrem todos os formulários).
 *
 * Responsabilidades: foco e acessibilidade (dialog modal, Esc, devolve o foco), confirmação em dois
 * cliques para exclusão, e os ganchos de conflito/autoria/presença que a funcionalidade preenche.
 */
export interface OpcoesGaveta {
  titulo: string;
  corpo: Safe;
  rodape: Safe;
  /** Registro aberto (para aviso de conflito e presença "editando"). */
  registro?: { recurso: string; id: string; versao: number } | null;
  /** Linha "Cadastrado por …" mostrada acima do formulário. */
  autoria?: Safe | null;
  /** Liga os eventos do formulário; `camada` contém também o rodapé com os botões. */
  montar?: (form: HTMLFormElement, fechar: () => void, camada: HTMLElement) => void;
  aoFechar?: () => void;
}

/** O estado do registro aberto é comum à gaveta e ao formulário em página (ver `registro-aberto.ts`). */
export { registroAberto as gavetaAberta, observarRegistro as observarGaveta } from "./registro-aberto";
export type { RegistroAberto as GavetaAberta } from "./registro-aberto";

export function abrirGaveta(o: OpcoesGaveta): () => void {
  const camada = $("#layer");
  if (!camada) throw new Error("#layer ausente");
  const anterior = document.activeElement as HTMLElement | null;
  const anteriorRegistro = abrirRegistro(o.titulo, o.registro ?? null);
  camada.innerHTML = `<div class="scrim" data-fechar></div><div class="drawer" role="dialog" aria-modal="true" aria-label="${esc(o.titulo)}"><header><h2>${esc(o.titulo)}</h2><button class="btn ghost" data-fechar aria-label="Fechar">Fechar</button></header><form class="body" id="gform" novalidate><div class="banner conflito" id="conflito" hidden></div>${o.autoria ?? ""}${o.corpo}</form><footer>${o.rodape}</footer></div>`;

  const aoTeclar = (e: KeyboardEvent): void => {
    if (e.key === "Escape") fechar();
  };
  const fechar = (): void => {
    camada.innerHTML = "";
    document.removeEventListener("keydown", aoTeclar);
    fecharRegistro(anteriorRegistro);
    o.aoFechar?.();
    anterior?.focus?.();
  };
  document.addEventListener("keydown", aoTeclar);
  $$("[data-fechar]", camada).forEach((b) => b.addEventListener("click", fechar));

  const form = $<HTMLFormElement>("#gform", camada);
  if (!form) throw new Error("#gform ausente");
  form.addEventListener("submit", (e) => e.preventDefault());

  // Exclusão em dois cliques: o primeiro clique arma o botão, o segundo confirma.
  ligarExclusaoEmDoisCliques(camada);

  form.querySelector<HTMLElement>("input:not([readonly]):not([disabled]),select:not([disabled]),textarea")?.focus();
  o.montar?.(form, fechar, camada);
  return fechar;
}
