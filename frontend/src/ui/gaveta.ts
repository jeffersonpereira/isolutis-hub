import { $, $$ } from "@/core/dom";
import { esc, type Safe } from "@/core/html";

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

export interface GavetaAberta {
  recurso: string;
  id: string;
  versao: number;
  /** Versão que esta própria sessão acabou de gravar (para não acusar conflito consigo mesma). */
  minhaVersao: number | null;
  excluidoPorMim: boolean;
}

export let gavetaAberta: GavetaAberta | null = null;

let aoMudarGaveta: (titulo: string | null, editando: boolean) => void = () => {};
export const observarGaveta = (fn: typeof aoMudarGaveta): void => {
  aoMudarGaveta = fn;
};

export function abrirGaveta(o: OpcoesGaveta): () => void {
  const camada = $("#layer");
  if (!camada) throw new Error("#layer ausente");
  const anterior = document.activeElement as HTMLElement | null;
  gavetaAberta = o.registro
    ? { recurso: o.registro.recurso, id: o.registro.id, versao: o.registro.versao, minhaVersao: null, excluidoPorMim: false }
    : null;

  camada.innerHTML = `<div class="scrim" data-fechar></div><div class="drawer" role="dialog" aria-modal="true" aria-label="${esc(o.titulo)}"><header><h2>${esc(o.titulo)}</h2><button class="btn ghost" data-fechar aria-label="Fechar">Fechar</button></header><form class="body" id="gform" novalidate><div class="banner conflito" id="conflito" hidden></div>${o.autoria ?? ""}${o.corpo}</form><footer>${o.rodape}</footer></div>`;
  aoMudarGaveta(o.titulo, !!o.registro);

  const aoTeclar = (e: KeyboardEvent): void => {
    if (e.key === "Escape") fechar();
  };
  const fechar = (): void => {
    camada.innerHTML = "";
    gavetaAberta = null;
    document.removeEventListener("keydown", aoTeclar);
    aoMudarGaveta(null, false);
    o.aoFechar?.();
    anterior?.focus?.();
  };
  document.addEventListener("keydown", aoTeclar);
  $$("[data-fechar]", camada).forEach((b) => b.addEventListener("click", fechar));

  const form = $<HTMLFormElement>("#gform", camada);
  if (!form) throw new Error("#gform ausente");
  form.addEventListener("submit", (e) => e.preventDefault());

  // Exclusão em dois cliques: o primeiro arma o botão, o segundo confirma.
  $$(".btn.danger", camada).forEach((b) =>
    b.addEventListener(
      "click",
      (e) => {
        if (!b.classList.contains("armed")) {
          e.stopImmediatePropagation();
          b.classList.add("armed");
          b.textContent = "Confirmar exclusão";
        }
      },
      true,
    ),
  );

  form.querySelector<HTMLElement>("input:not([readonly]):not([disabled]),select:not([disabled]),textarea")?.focus();
  o.montar?.(form, fechar, camada);
  return fechar;
}
