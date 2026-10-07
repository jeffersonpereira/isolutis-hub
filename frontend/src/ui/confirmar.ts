/**
 * Janela de confirmação (diálogo modal): foco preso, Esc cancela, devolve o foco. Resolve `true` ao confirmar e
 * `false` ao cancelar. Usada, por exemplo, para descartar alterações não salvas.
 */
import { html } from "@/core/html";

export interface OpcoesConfirmar {
  titulo: string;
  texto: string;
  confirmar: string;
  cancelar: string;
}

export function confirmar(o: OpcoesConfirmar): Promise<boolean> {
  return new Promise((resolve) => {
    const anterior = document.activeElement as HTMLElement | null;
    const camada = document.createElement("div");
    camada.className = "confirmar-camada";
    camada.innerHTML = String(html`<div class="confirmar-fundo"></div>
      <div class="confirmar" role="alertdialog" aria-modal="true" aria-labelledby="confirmar-t" aria-describedby="confirmar-d">
        <h2 id="confirmar-t">${o.titulo}</h2>
        <p id="confirmar-d">${o.texto}</p>
        <div class="confirmar-bt"><button type="button" class="btn" data-confirmar-nao>${o.cancelar}</button><button type="button" class="btn primary" data-confirmar-sim>${o.confirmar}</button></div>
      </div>`);
    document.body.appendChild(camada);
    const cancelar = camada.querySelector<HTMLButtonElement>("[data-confirmar-nao]");
    const confirmarBt = camada.querySelector<HTMLButtonElement>("[data-confirmar-sim]");

    const encerrar = (resultado: boolean): void => {
      document.removeEventListener("keydown", aoTeclar, true);
      camada.remove();
      anterior?.focus?.();
      resolve(resultado);
    };
    function aoTeclar(e: KeyboardEvent): void {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        encerrar(false);
      } else if (e.key === "Tab" && cancelar && confirmarBt) {
        const foco = document.activeElement;
        if (e.shiftKey && foco === cancelar) {
          e.preventDefault();
          confirmarBt.focus();
        } else if (!e.shiftKey && foco === confirmarBt) {
          e.preventDefault();
          cancelar.focus();
        }
      }
    }
    document.addEventListener("keydown", aoTeclar, true);
    cancelar?.addEventListener("click", () => encerrar(false));
    confirmarBt?.addEventListener("click", () => encerrar(true));
    camada.querySelector(".confirmar-fundo")?.addEventListener("click", () => encerrar(false));
    cancelar?.focus(); // o padrão seguro é continuar editando
  });
}
