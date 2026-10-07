/** Barra lateral: "Usando agora", indicador de sincronização, recolhimento e painel de menu no celular. */
import { $, obrigatorio } from "@/core/dom";
import { esc, html } from "@/core/html";
import { iniciais, primeiroNome } from "@/core/formato";
import { AREA_NOME } from "@/domain/constantes";
import { eu } from "@/state/estado";
import { icone } from "@/ui/icones";
import type { PessoaOnline } from "@/state/realtime";

export function desenharOnline(pessoas: PessoaOnline[]): void {
  const el = obrigatorio("#online");
  const lista = [...pessoas].sort((a, b) => Number(b.usuario_id === eu.id) - Number(a.usuario_id === eu.id));
  el.hidden = !lista.length;
  el.innerHTML = String(
    html`<div class="on-t">Usando agora · ${lista.length}</div>${lista.map((p) => {
      const souEu = p.usuario_id === eu.id;
      const nome = souEu ? `${primeiroNome(eu.nome)} (você)` : p.nome || "Pessoa da equipe";
      const onde = p.editando ? "editando " + p.editando : (AREA_NOME[p.area] ?? "");
      return html`<div class="on-p" title="${nome + (onde ? " · " + onde : "")}"><i class="av"><span>${iniciais(p.nome)}</span></i><div class="on-n"><b>${nome}</b><small>${onde}</small></div></div>`;
    })}`,
  );
}

type Situacao = "conectando" | "on" | "off";
export function indicarSincronizacao(situacao: Situacao, texto: string): void {
  const el = obrigatorio("#sync");
  el.className = situacao === "conectando" ? "sync" : `sync ${situacao}`;
  el.innerHTML = `<span class="dot"></span><span class="tx">${esc(texto)}</span>`;
}

const CHAVE_RECOLHIDO = "hub.menu.recolhido";
const CONSULTA_CELULAR = "(max-width: 860px)";

function lerRecolhido(): boolean {
  try {
    return localStorage.getItem(CHAVE_RECOLHIDO) === "1";
  } catch {
    return false;
  }
}
function salvarRecolhido(valor: boolean): void {
  try {
    localStorage.setItem(CHAVE_RECOLHIDO, valor ? "1" : "0");
  } catch {
    /* sem armazenamento: só não lembra a preferência */
  }
}

/** Recolher a barra lateral (lembrando a escolha) e, no celular, abri-la como painel sobreposto. */
export function iniciarBarraLateral(): void {
  const app = obrigatorio("#app");
  const lateral = obrigatorio("#side");
  const recolher = obrigatorio<HTMLButtonElement>("#recolher");
  const abrirMenu = $<HTMLButtonElement>("#abrirMenu");
  if (abrirMenu) abrirMenu.innerHTML = String(icone("menu"));

  const aplicarRecolhido = (recolhida: boolean): void => {
    app.classList.toggle("recolhida", recolhida);
    const rotulo = recolhida ? "Expandir a barra lateral" : "Recolher a barra lateral";
    recolher.setAttribute("aria-label", rotulo);
    recolher.title = rotulo;
    recolher.innerHTML = String(html`${icone("recolher")}<span class="tx">${recolhida ? "Expandir menu" : "Recolher menu"}</span>`);
  };
  aplicarRecolhido(lerRecolhido());
  recolher.addEventListener("click", () => {
    const novo = !app.classList.contains("recolhida");
    aplicarRecolhido(novo);
    salvarRecolhido(novo);
  });

  // Painel do celular
  let fundo: HTMLElement | null = null;
  const focaveis = (): HTMLElement[] => [...lateral.querySelectorAll<HTMLElement>("a[href], button:not([disabled])")].filter((el) => el.getClientRects().length > 0);
  const aoTeclar = (e: KeyboardEvent): void => {
    if (e.key === "Escape") {
      e.preventDefault();
      fecharPainel(true);
    } else if (e.key === "Tab") {
      const lista = focaveis();
      const primeiro = lista[0];
      const ultimo = lista[lista.length - 1];
      if (!primeiro || !ultimo) return;
      if (e.shiftKey && document.activeElement === primeiro) {
        e.preventDefault();
        ultimo.focus();
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault();
        primeiro.focus();
      }
    }
  };
  function abrirPainel(): void {
    if (app.classList.contains("menu-aberto")) return;
    app.classList.add("menu-aberto");
    fundo = document.createElement("div");
    fundo.className = "scrim-menu";
    fundo.addEventListener("click", () => fecharPainel(true));
    document.body.appendChild(fundo);
    abrirMenu?.setAttribute("aria-expanded", "true");
    document.addEventListener("keydown", aoTeclar);
    focaveis()[0]?.focus();
  }
  function fecharPainel(devolverFoco: boolean): void {
    if (!app.classList.contains("menu-aberto")) return;
    app.classList.remove("menu-aberto");
    fundo?.remove();
    fundo = null;
    abrirMenu?.setAttribute("aria-expanded", "false");
    document.removeEventListener("keydown", aoTeclar);
    if (devolverFoco) abrirMenu?.focus();
  }
  abrirMenu?.addEventListener("click", abrirPainel);
  // Escolher uma tela fecha o painel (a navegação em si é tratada em eventos.ts)
  lateral.addEventListener("click", (e) => {
    if ((e.target as Element).closest("a[data-go]")) fecharPainel(false);
  });
  matchMedia(CONSULTA_CELULAR).addEventListener("change", (e) => {
    if (!e.matches) fecharPainel(false);
  });
}
