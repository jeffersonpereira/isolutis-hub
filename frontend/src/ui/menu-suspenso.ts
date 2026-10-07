/**
 * Menu suspenso acionado por um botão (padrão ARIA "menu button"): "+ Novo", tema e menu do usuário.
 *
 * Teclado: Enter, Espaço e seta para baixo abrem; setas, Home e End movem o destaque; Enter executa;
 * Esc fecha e devolve o foco ao botão; Tab fecha. Clicar fora ou redimensionar a janela também fecha.
 * Só um menu fica aberto por vez.
 */
import { html, raw, type Safe } from "@/core/html";
import { icone } from "@/ui/icones";

export interface ItemMenuSuspenso {
  rotulo: string;
  icone?: string;
  aoEscolher: () => void;
  /** Para itens exclusivos (tema): mostra o visto no item em vigor. */
  marcado?: boolean;
  perigo?: boolean;
  /** Linha separadora antes do item. */
  separador?: boolean;
}

export interface OpcoesMenuSuspenso {
  botao: HTMLElement;
  /** Nome acessível do menu. */
  rotulo: string;
  itens: () => ItemMenuSuspenso[];
  /** Conteúdo acima dos itens (ex.: nome e e-mail do usuário). */
  cabecalho?: () => Safe;
  /** Chamado depois que o menu abre, para ligar eventos do cabeçalho. */
  aoAbrir?: (menu: HTMLElement) => void;
}

export interface MenuSuspenso {
  abrir(): void;
  fechar(devolverFoco?: boolean): void;
  aberto(): boolean;
}

let aberto: MenuSuspenso | null = null;

export function menuSuspenso(o: OpcoesMenuSuspenso): MenuSuspenso {
  let el: HTMLElement | null = null;
  let itens: ItemMenuSuspenso[] = [];

  const botoesDeItem = (): HTMLButtonElement[] => (el ? [...el.querySelectorAll<HTMLButtonElement>("button.it")] : []);
  const focar = (i: number): void => {
    const lista = botoesDeItem();
    if (lista.length) lista[(i + lista.length) % lista.length]?.focus();
  };

  const fora = (e: MouseEvent): void => {
    const alvo = e.target as Node;
    if (el && !el.contains(alvo) && !o.botao.contains(alvo)) fechar(false);
  };
  const aoTeclar = (e: KeyboardEvent): void => {
    if (!el) return;
    const lista = botoesDeItem();
    const i = lista.indexOf(document.activeElement as HTMLButtonElement);
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      fechar(true);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      focar(i + 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      focar(i < 0 ? -1 : i - 1);
    } else if (e.key === "Home") {
      e.preventDefault();
      focar(0);
    } else if (e.key === "End") {
      e.preventDefault();
      focar(-1);
    } else if (e.key === "Tab") {
      fechar(false);
    }
  };
  const aoRedimensionar = (): void => fechar(false);

  function fechar(devolverFoco = true): void {
    if (!el) return;
    el.remove();
    el = null;
    o.botao.setAttribute("aria-expanded", "false");
    document.removeEventListener("mousedown", fora, true);
    document.removeEventListener("keydown", aoTeclar, true);
    window.removeEventListener("resize", aoRedimensionar);
    if (aberto === self) aberto = null;
    if (devolverFoco) o.botao.focus();
  }

  function abrir(): void {
    if (el) return;
    aberto?.fechar(false);
    itens = o.itens();
    const corpo = itens.map(
      (it, k) =>
        html`${it.separador ? raw("<hr>") : ""}<button type="button" class="it${it.perigo ? " perigo" : ""}" role="${it.marcado === undefined ? "menuitem" : "menuitemradio"}"${it.marcado === undefined ? "" : raw(` aria-checked="${it.marcado}"`)} data-k="${k}">${it.icone ? icone(it.icone) : ""}<span>${it.rotulo}</span>${it.marcado === undefined ? "" : icone("check", { classe: "ck" })}</button>`,
    );
    el = document.createElement("div");
    el.className = "pop";
    el.setAttribute("role", "menu");
    el.setAttribute("aria-label", o.rotulo);
    el.innerHTML = String(html`${o.cabecalho ? o.cabecalho() : ""}${corpo}`);
    document.body.appendChild(el);

    // Posição: abaixo do botão, alinhado à direita dele, sem sair da janela
    const r = o.botao.getBoundingClientRect();
    const largura = el.offsetWidth;
    el.style.top = `${Math.round(r.bottom + 6)}px`;
    el.style.left = `${Math.max(8, Math.min(window.innerWidth - largura - 8, Math.round(r.right - largura)))}px`;

    el.addEventListener("click", (e) => {
      const b = (e.target as Element).closest<HTMLButtonElement>("button.it");
      if (!b) return;
      const item = itens[Number(b.dataset.k)];
      fechar(true);
      item?.aoEscolher();
    });
    o.botao.setAttribute("aria-expanded", "true");
    document.addEventListener("mousedown", fora, true);
    document.addEventListener("keydown", aoTeclar, true);
    window.addEventListener("resize", aoRedimensionar);
    aberto = self;
    o.aoAbrir?.(el);
    const marcado = botoesDeItem().findIndex((b) => b.getAttribute("aria-checked") === "true");
    focar(marcado >= 0 ? marcado : 0);
  }

  const self: MenuSuspenso = { abrir, fechar, aberto: () => !!el };
  o.botao.setAttribute("aria-haspopup", "menu");
  o.botao.addEventListener("click", () => (el ? fechar(true) : abrir()));
  o.botao.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" && !el) {
      e.preventDefault();
      abrir();
    }
  });
  return self;
}

/** Bloco com nome e e-mail para o topo do menu do usuário. */
export const cabecalhoDoUsuario = (iniciais: string, nome: string, email: string): Safe =>
  html`<div class="cab"><i class="av" aria-hidden="true">${iniciais}</i><div><b>${nome}</b><small>${email}</small></div></div>`;

