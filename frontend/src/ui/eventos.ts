/**
 * Eventos globais da página, em um só lugar:
 *  - `data-go="vista"`      navega
 *  - `data-act="nome"`      executa a ação registrada com `registrarAcao` (dados extras em data-*)
 *  - `data-open="tipo:id"`  abre o registro com a função registrada via `registrarAbertura`
 */
import { $ } from "@/core/dom";
import { ir } from "@/state/nucleo";
import { despachar } from "./acoes";
import { toast } from "./toast";

type Abertura = (id: string) => void;
const aberturas = new Map<string, Abertura>();
export const registrarAbertura = (tipo: string, fn: Abertura): void => void aberturas.set(tipo, fn);

export function iniciarEventos(): void {
  document.addEventListener("click", async (e) => {
    const alvo = e.target as Element;

    // Botões do WhatsApp sem número: avisa em vez de navegar.
    const wa = alvo.closest<HTMLElement>(".btn.wa");
    if (wa) {
      if (wa.getAttribute("aria-disabled") === "true" && wa.id !== "waOrc") toast("Cadastre o WhatsApp do cliente para usar este botão.");
      return;
    }

    const acao = alvo.closest<HTMLElement>("[data-act]");
    // <select data-act> reage ao "change" (abaixo): no clique o valor ainda é o antigo.
    if (acao?.tagName === "SELECT") return;
    if (acao && !acao.closest(".drawer")) {
      e.stopPropagation();
      await despachar(acao.dataset.act ?? "", acao);
      return;
    }

    const ir_ = alvo.closest<HTMLElement>("[data-go]");
    if (ir_) {
      // Ctrl, Cmd, Shift ou botão do meio: deixa o navegador abrir o link em outra aba/janela.
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      e.preventDefault();
      await ir(ir_.dataset.go ?? "painel");
      return;
    }

    const abrir = alvo.closest<HTMLElement>("[data-open]");
    if (abrir) {
      const [tipo = "", id = ""] = (abrir.dataset.open ?? "").split(":");
      aberturas.get(tipo)?.(id);
    }
  });

  document.addEventListener("change", (e) => {
    const sel = (e.target as Element).closest<HTMLSelectElement>("select[data-act]");
    if (sel && !sel.closest(".drawer")) void despachar(sel.dataset.act ?? "", sel);
  });

  document.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement;
    if (e.key === "Enter" && t.matches?.("[data-open],[data-act][tabindex]")) t.click();
  });

  // Arrastar cartões entre colunas (funil de negócios e kanban de tarefas)
  const view = $("#view");
  if (!view) return;
  view.addEventListener("dragstart", (e) => {
    const card = (e.target as Element).closest<HTMLElement>(".card");
    if (card && e.dataTransfer) {
      e.dataTransfer.setData("text/plain", card.dataset.id ?? "");
      e.dataTransfer.effectAllowed = "move";
    }
  });
  view.addEventListener("dragover", (e) => {
    const col = (e.target as Element).closest<HTMLElement>(".col");
    if (!col) return;
    e.preventDefault();
    document.querySelectorAll(".col.over").forEach((x) => x !== col && x.classList.remove("over"));
    col.classList.add("over");
  });
  view.addEventListener("dragleave", (e) => {
    const col = (e.target as Element).closest<HTMLElement>(".col");
    if (col && !col.contains(e.relatedTarget as Node | null)) col.classList.remove("over");
  });
  view.addEventListener("drop", (e) => {
    const col = (e.target as Element).closest<HTMLElement>(".col");
    if (!col) return;
    e.preventDefault();
    col.classList.remove("over");
    const id = e.dataTransfer?.getData("text/plain");
    if (!id) return;
    for (const [atributo, tratar] of soltadores) {
      const destino = col.dataset[atributo];
      if (destino) tratar(id, destino);
    }
  });
}

type Soltar = (id: string, destino: string) => void;
const soltadores = new Map<string, Soltar>();
/** Cada quadro registra o atributo que identifica suas colunas (`data-etapa`, `data-coluna`) e o que fazer ao soltar. */
export const registrarSoltar = (atributo: string, fn: Soltar): void => void soltadores.set(atributo, fn);
