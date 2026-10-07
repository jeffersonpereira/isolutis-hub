/**
 * Paleta de comandos (Ctrl+K / ⌘+K): ir a qualquer tela e executar ações rápidas, com busca que ignora acentos e
 * caixa. Lista só o que o usuário pode acessar e NÃO busca registros (isso virá com o combobox assíncrono).
 *
 * Acessibilidade: diálogo modal com foco preso no campo, padrão ARIA combobox + listbox
 * (`aria-controls`, `aria-activedescendant`, `role="option"`), setas, Enter e Esc, e devolução do foco.
 */
import { normalizarTexto } from "@/core/formato";
import { html } from "@/core/html";
import { eu } from "@/state/estado";
import { acoesRapidas, iconeDaTela, ir, vistasVisiveis } from "@/state/nucleo";
import { despachar } from "@/ui/acoes";
import { icone } from "@/ui/icones";

export interface ItemDaPaleta {
  grupo: "Ir para" | "Ações";
  rotulo: string;
  icone: string;
  executar: () => void;
}

export const normalizar = normalizarTexto;

/** Itens que casam com a consulta: começo do texto ou de uma palavra vem antes de "contém"; vazio = todos. */
export function filtrarItens(itens: ItemDaPaleta[], consulta: string): ItemDaPaleta[] {
  const q = normalizar(consulta);
  if (!q) return itens;
  const pontuados: Array<{ item: ItemDaPaleta; pontos: number; ordem: number }> = [];
  itens.forEach((item, ordem) => {
    const r = normalizar(item.rotulo);
    const pos = r.indexOf(q);
    if (pos === -1) return;
    const inicioDePalavra = pos === 0 || r[pos - 1] === " ";
    pontuados.push({ item, pontos: pos === 0 ? 0 : inicioDePalavra ? 1 : 2, ordem });
  });
  return pontuados.sort((a, b) => a.pontos - b.pontos || a.ordem - b.ordem).map((p) => p.item);
}

interface Fontes {
  telas: Array<{ id: string; nome: string }>;
  acoes: Array<{ id: string; rotulo: string; icone?: string }>;
  iconeDaTela: (id: string) => string;
  irPara: (id: string) => void;
  executarAcao: (id: string) => void;
}

/** Monta os itens: primeiro as telas, depois as ações. */
export function montarItens(f: Fontes): ItemDaPaleta[] {
  return [
    ...f.telas.map((t): ItemDaPaleta => ({ grupo: "Ir para", rotulo: t.nome, icone: f.iconeDaTela(t.id), executar: () => f.irPara(t.id) })),
    ...f.acoes.map((a): ItemDaPaleta => ({ grupo: "Ações", rotulo: a.rotulo, icone: a.icone ?? "mais", executar: () => f.executarAcao(a.id) })),
  ];
}

const itensAtuais = (): ItemDaPaleta[] =>
  montarItens({
    telas: vistasVisiveis().map((v) => ({ id: v.id, nome: v.nome })),
    acoes: acoesRapidas(),
    iconeDaTela,
    irPara: (id) => void ir(id),
    executarAcao: (id) => void despachar(id, document.body),
  });

let camada: HTMLElement | null = null;
let anterior: HTMLElement | null = null;

export const paletaAberta = (): boolean => camada !== null;

export function fecharPaleta(devolverFoco = true): void {
  if (!camada) return;
  camada.remove();
  camada = null;
  document.removeEventListener("keydown", aoTeclarNaPaleta, true);
  if (devolverFoco) anterior?.focus?.();
  anterior = null;
}

let visiveis: ItemDaPaleta[] = [];
let selecionado = 0;

function desenharLista(consulta: string): void {
  if (!camada) return;
  visiveis = filtrarItens(itensAtuais(), consulta);
  selecionado = Math.min(selecionado, Math.max(visiveis.length - 1, 0));
  const lista = camada.querySelector<HTMLElement>("#paleta-lista");
  const campo = camada.querySelector<HTMLInputElement>("#paleta-campo");
  if (!lista || !campo) return;
  if (!visiveis.length) {
    lista.innerHTML = String(html`<div class="vazio" role="status"><b>Nada encontrado para “${consulta}”</b>Tente o nome de uma tela ou de uma ação, como “orçamentos” ou “novo cliente”.</div>`);
    campo.removeAttribute("aria-activedescendant");
    return;
  }
  let grupoAtual = "";
  lista.innerHTML = String(
    html`${visiveis.map((it, k) => {
      const cabecalho = it.grupo !== grupoAtual ? html`<div class="grupo" role="presentation">${it.grupo}</div>` : "";
      grupoAtual = it.grupo;
      return html`${cabecalho}<div class="op" role="option" id="paleta-op-${k}" aria-selected="${String(k === selecionado)}" data-k="${k}">${icone(it.icone)}<span>${it.rotulo}</span><small>${it.grupo === "Ações" ? "Ação" : "Tela"}</small></div>`;
    })}`,
  );
  campo.setAttribute("aria-activedescendant", `paleta-op-${selecionado}`);
  lista.querySelector("[aria-selected='true']")?.scrollIntoView({ block: "nearest" });
}

function escolher(k: number): void {
  const item = visiveis[k];
  if (!item) return;
  fecharPaleta(false);
  item.executar();
}

function aoTeclarNaPaleta(e: KeyboardEvent): void {
  if (!camada) return;
  const campo = camada.querySelector<HTMLInputElement>("#paleta-campo");
  if (e.key === "Escape") {
    e.preventDefault();
    e.stopPropagation();
    fecharPaleta(true);
  } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    if (!visiveis.length) return;
    selecionado = (selecionado + (e.key === "ArrowDown" ? 1 : -1) + visiveis.length) % visiveis.length;
    desenharLista(campo?.value ?? "");
  } else if (e.key === "Enter") {
    e.preventDefault();
    escolher(selecionado);
  } else if (e.key === "Tab") {
    e.preventDefault(); // o foco fica preso no campo da paleta
  }
}

export function abrirPaleta(): void {
  if (camada) return;
  anterior = document.activeElement as HTMLElement | null;
  camada = document.createElement("div");
  camada.className = "paleta-camada";
  camada.innerHTML = String(html`<div class="paleta-fundo" data-fechar></div>
    <div class="paleta" role="dialog" aria-modal="true" aria-label="Paleta de comandos">
      <div class="in">${icone("busca")}<input id="paleta-campo" role="combobox" aria-expanded="true" aria-controls="paleta-lista" aria-autocomplete="list" aria-label="Buscar telas e ações" placeholder="Para onde você quer ir ou o que quer fazer?" autocomplete="off" spellcheck="false"><kbd>Esc</kbd></div>
      <div id="paleta-lista" class="lista" role="listbox" aria-label="Resultados"></div>
      <div class="rod"><span><kbd>↑</kbd> <kbd>↓</kbd> navegar</span><span><kbd>Enter</kbd> abrir</span><span><kbd>Esc</kbd> fechar</span></div>
    </div>`);
  document.body.appendChild(camada);
  selecionado = 0;
  const campo = camada.querySelector<HTMLInputElement>("#paleta-campo");
  campo?.addEventListener("input", () => {
    selecionado = 0;
    desenharLista(campo.value);
  });
  camada.addEventListener("click", (e) => {
    const alvo = e.target as Element;
    if (alvo.closest("[data-fechar]")) return fecharPaleta(true);
    const op = alvo.closest<HTMLElement>(".op");
    if (op) escolher(Number(op.dataset.k));
  });
  camada.addEventListener("mousemove", (e) => {
    const op = (e.target as Element).closest<HTMLElement>(".op");
    const k = op ? Number(op.dataset.k) : -1;
    if (k >= 0 && k !== selecionado) {
      selecionado = k;
      camada?.querySelectorAll(".op").forEach((el, i) => el.setAttribute("aria-selected", String(i === k)));
      campo?.setAttribute("aria-activedescendant", `paleta-op-${k}`);
    }
  });
  document.addEventListener("keydown", aoTeclarNaPaleta, true);
  desenharLista("");
  campo?.focus();
}

/** Liga Ctrl+K e ⌘+K. Só vale com a sessão aberta (não por cima da tela de login). */
export function ligarAtalhoDaPaleta(): void {
  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.key.toLowerCase() !== "k" || e.shiftKey || e.altKey) return;
    if (!eu.id || document.getElementById("login")?.hidden === false) return;
    e.preventDefault();
    if (paletaAberta()) fecharPaleta(true);
    else abrirPaleta();
  });
}

