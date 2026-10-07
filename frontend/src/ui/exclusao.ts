import { $$ } from "@/core/dom";

/**
 * Exclusão em dois cliques: o primeiro clique num botão `.btn.danger` o arma ("Confirmar exclusão") e não executa
 * nada; só o segundo exclui. Vale para a gaveta e para o formulário em página.
 */
export function ligarExclusaoEmDoisCliques(raiz: ParentNode): void {
  $$(".btn.danger", raiz).forEach((b) =>
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
}
