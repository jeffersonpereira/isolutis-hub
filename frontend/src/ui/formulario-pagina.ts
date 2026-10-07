/**
 * Formulário em página: o padrão para formulários longos (muitos campos, seções ou listas relacionadas).
 * Ocupa a área principal, tem URL própria, seções navegáveis, barra de ações fixa e proteção contra perda de
 * alterações. Edições curtas continuam na gaveta (`gaveta.ts`); os dois compartilham o estado de "registro
 * aberto" (conflito de edição, versão gravada pela própria sessão e presença "editando…").
 */
import { $, $$ } from "@/core/dom";
import { html, type Safe } from "@/core/html";
import { atualizarUrl, ir, podeSair, registrarGuarda, sairDaPagina, travarConteudo, vistaAtual } from "@/state/nucleo";
import { cabecalhoDePagina, estadoVazio } from "./componentes";
import { confirmar } from "./confirmar";
import { ligarExclusaoEmDoisCliques } from "./exclusao";
import { abrirRegistro, fecharRegistro } from "./registro-aberto";

export interface SecaoFormulario {
  id: string;
  titulo: string;
  descricao?: string;
  corpo: Safe;
}

export interface OpcoesFormularioPagina {
  /** Id da tela (listagem) a que o registro pertence, e o nome dela na trilha. */
  vista: string;
  rotuloLista: string;
  /** Caminho do registro (`/clientes/<id>` ou `/clientes/novo`). */
  caminho: string;
  titulo: string;
  /** Iniciais no avatar do cabeçalho (omita para registro novo). */
  avatar?: string;
  /** Linha sob o título: autoria, papéis etc. */
  meta?: Safe | null;
  secoes: SecaoFormulario[];
  /** Botões do registro, à direita da barra de ações (ex.: WhatsApp, Novo negócio). */
  acoes?: Safe;
  /** Botão Salvar já montado (some em modo leitura). */
  salvar: Safe;
  /** Botão Excluir já montado (vazio para registro novo ou sem permissão). */
  excluir: Safe;
  registro?: { recurso: string; id: string; versao: number } | null;
  /** Liga os eventos do formulário. `raiz` contém também a barra de ações (botões com `data-salvar`, `data-excluir`…). */
  montar?: (form: HTMLFormElement, fechar: () => void, raiz: HTMLElement) => void;
}

/** Valores do formulário, normalizados, para saber se algo mudou (alterar e restaurar não conta como alteração). */
export function instantaneo(form: HTMLFormElement): string {
  const pares: Array<[string, string]> = [];
  for (const el of Array.from(form.elements)) {
    const campo = el as HTMLInputElement;
    if (!campo.name || campo.disabled) continue;
    if (campo.type === "button" || campo.type === "submit" || campo.type === "file") continue;
    if ((campo.type === "checkbox" || campo.type === "radio") && !campo.checked) continue;
    pares.push([campo.name, String(campo.value ?? "").trim()]);
  }
  return JSON.stringify(pares);
}

export async function abrirFormularioPagina(o: OpcoesFormularioPagina): Promise<void> {
  // Já há um formulário com alterações? Pergunta antes de trocá-lo por este.
  if (!(await podeSair())) return;
  sairDaPagina();
  if (vistaAtual() !== o.vista) await ir(o.vista, { historico: "nenhum", semGuarda: true });
  const raiz = $("#view");
  if (!raiz) return;

  travarConteudo(true);
  raiz.innerHTML = String(html`<div class="fp" data-formulario-pagina>
    <nav class="trilha" aria-label="Trilha"><a href="/${o.vista}" data-go="${o.vista}">${o.rotuloLista}</a><span aria-hidden="true">›</span><span aria-current="page">${o.titulo}</span></nav>
    <div class="fp-head">${o.avatar ? html`<i class="av fp-av" aria-hidden="true">${o.avatar}</i>` : ""}<div><h1>${o.titulo}</h1>${o.meta ? html`<div class="fp-meta">${o.meta}</div>` : ""}</div></div>
    <div class="banner conflito" id="conflito" hidden></div>
    <div class="fp-lay">
      <nav class="fp-snav" aria-label="Seções do formulário">${o.secoes.map((s, i) => html`<a href="#fp-${s.id}"${i === 0 ? html` aria-current="true"` : ""}>${s.titulo}</a>`)}</nav>
      <form class="fp-secs" id="gform" novalidate>${o.secoes.map((s) => html`<section class="panel fp-sec" id="fp-${s.id}" aria-labelledby="fp-${s.id}-t"><header><h2 id="fp-${s.id}-t">${s.titulo}</h2>${s.descricao ? html`<p class="sub">${s.descricao}</p>` : ""}</header><div class="corpo">${s.corpo}</div></section>`)}</form>
    </div>
    <div class="fp-acoes" id="fp-acoes">${o.excluir}<span class="sujo" role="status">Alterações não salvas</span><span class="sp"></span>${o.acoes ?? ""}<button type="button" class="btn ghost" data-cancelar>Cancelar</button>${o.salvar}</div>
  </div>`);
  atualizarUrl(o.caminho);

  const anteriorRegistro = abrirRegistro(o.titulo, o.registro ?? null);
  const form = $<HTMLFormElement>("#gform", raiz);
  const barra = $("#fp-acoes", raiz);
  if (!form || !barra) return;
  form.addEventListener("submit", (e) => e.preventDefault());
  ligarExclusaoEmDoisCliques(raiz);

  // Proteção contra perda de alterações
  const inicial = instantaneo(form);
  const alterado = (): boolean => instantaneo(form) !== inicial;
  const marcar = (): void => {
    barra.classList.toggle("dirty", alterado());
  };
  form.addEventListener("input", marcar);
  form.addEventListener("change", marcar);
  const aoFecharAba = (e: BeforeUnloadEvent): void => {
    if (alterado()) {
      e.preventDefault();
      e.returnValue = "";
    }
  };
  window.addEventListener("beforeunload", aoFecharAba);
  registrarGuarda(
    async () =>
      !alterado() ||
      (await confirmar({
        titulo: "Descartar alterações?",
        texto: "Você alterou este registro e ainda não salvou. Se sair agora, as alterações serão perdidas.",
        confirmar: "Descartar e sair",
        cancelar: "Continuar editando",
      })),
    () => {
      window.removeEventListener("beforeunload", aoFecharAba);
      travarConteudo(false);
      fecharRegistro(anteriorRegistro);
    },
  );

  // Navegação entre seções
  $$(".fp-snav a", raiz).forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      $$(".fp-snav a", raiz).forEach((x) => x.removeAttribute("aria-current"));
      a.setAttribute("aria-current", "true");
      const alvo = $<HTMLElement>(a.getAttribute("href") ?? "", raiz);
      alvo?.scrollIntoView({ behavior: "smooth", block: "start" });
      alvo?.querySelector<HTMLElement>("h2")?.setAttribute("tabindex", "-1");
      alvo?.querySelector<HTMLElement>("h2")?.focus({ preventScroll: true });
    }),
  );

  // Depois de salvar ou excluir, volta à listagem trocando a entrada do histórico (Voltar não reabre o registro)
  const fechar = (): void => void ir(o.vista, { historico: "replace", semGuarda: true });
  $("[data-cancelar]", raiz)?.addEventListener("click", () => void ir(o.vista, { historico: "replace" }));

  form.querySelector<HTMLElement>("input:not([readonly]):not([disabled]),select:not([disabled]),textarea")?.focus({ preventScroll: true });
  o.montar?.(form, fechar, raiz);
}

/** A rota pede um registro que não existe (ou que o usuário não pode ver). */
export function mostrarRegistroNaoEncontrado(o: { vista: string; rotuloLista: string }): void {
  const raiz = $("#view");
  if (!raiz) return;
  sairDaPagina();
  travarConteudo(true);
  raiz.innerHTML = String(
    html`${cabecalhoDePagina({ titulo: "Registro não encontrado" })}${estadoVazio({
      icone: "vazio",
      titulo: "Não encontramos este registro",
      texto: "Ele pode ter sido excluído ou você não tem acesso a ele.",
      acao: html`<a class="btn primary" href="/${o.vista}" data-go="${o.vista}">Voltar para ${o.rotuloLista}</a>`,
    })}`,
  );
  registrarGuarda(null, () => travarConteudo(false));
}
