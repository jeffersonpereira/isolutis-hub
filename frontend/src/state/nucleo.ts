/**
 * Núcleo da interface: registro de vistas (telas), navegação, renderização e recarga de dados.
 * Cada funcionalidade registra a sua vista; este módulo não conhece nenhuma delas.
 */
import { api } from "@/api/endpoints";
import type { Recurso } from "@/api/tipos";
import { $, obrigatorio } from "@/core/dom";
import { html, type Safe } from "@/core/html";
import { registrarAcao } from "@/ui/acoes";
import { conexao, dados, eu } from "./estado";

export interface Vista {
  id: string;
  nome: string;
  /** Número exibido ao lado do nome no menu. */
  contagem?: () => number | "";
  /** Carrega dados próprios da tela (ex.: faturamento do ano). Chamado ao entrar e quando o servidor avisa de mudanças. */
  carregar?: () => Promise<void>;
  /** Recursos cuja mudança exige recarregar `carregar` (o painel depende de quase tudo). */
  depende?: readonly string[];
  desenhar: () => Safe;
  somenteAdmin?: boolean;
  /** Agrupa a vista num submenu recolhível do menu lateral (ex.: "Financeiro"). */
  grupo?: string;
}

const vistas = new Map<string, Vista>();
let atual = "painel";
const CHAVE_ABA = "hub.aba";

/** Ordem do menu lateral (independe da ordem em que os módulos são importados). */
const ORDEM_MENU = [
  "painel", "clientes", "negocios", "orcamentos", "projetos", "tarefas", "produtos",
  "fin-plano", "fin-contas", "fin-parceiros", "fin-titulos", "fin-fluxo", "faturamento", "equipe",
];  // fmt: skip
const posicao = (id: string): number => {
  const i = ORDEM_MENU.indexOf(id);
  return i === -1 ? ORDEM_MENU.length : i;
};

export const registrarVista = (v: Vista): void => {
  vistas.set(v.id, v);
};
export const vistaAtual = (): string => atual;

const carregadores: Record<string, () => Promise<void>> = {
  clientes: async () => void (dados.clientes = await api.clientes.listar()),
  negocios: async () => void (dados.negocios = await api.negocios.listar()),
  orcamentos: async () => void (dados.orcamentos = await api.orcamentos.listar()),
  produtos: async () => void (dados.produtos = await api.produtos.listar()),
  projetos: async () => void (dados.projetos = await api.projetos.listar()),
  tarefas: async () => void (dados.tarefas = await api.tarefas.listar()),
  equipe: async () => void (dados.equipe = await api.equipe.listar()),
};
export const RECURSOS_EM_MEMORIA = Object.keys(carregadores) as Recurso[];

type AoRecarregar = (recurso: string) => void;
const ouvintes: AoRecarregar[] = [];
/** Avisa quem precisa reagir a um recurso recarregado (ex.: gaveta aberta checando conflito de edição). */
export const aoRecarregar = (fn: AoRecarregar): void => void ouvintes.push(fn);

/** Recarrega recursos do servidor e redesenha. Chamado após cada gravação e quando o servidor avisa de mudanças. */
export async function recarregar(...recursos: string[]): Promise<void> {
  const unicos = [...new Set(recursos)];
  await Promise.all(unicos.map((r) => carregadores[r]?.().catch((e: unknown) => console.error(r, e))));
  const v = vistas.get(atual);
  if (v?.carregar && (v.depende ?? []).some((d) => unicos.includes(d))) await v.carregar().catch((e: unknown) => console.error(e));
  render();
  unicos.forEach((r) => ouvintes.forEach((fn) => fn(r)));
}

export async function carregarTudo(): Promise<void> {
  await Promise.all(Object.values(carregadores).map((c) => c()));
  await vistas.get(atual)?.carregar?.().catch((e: unknown) => console.error(e));
}

/** Recarrega os dados próprios da tela atual (ex.: ao trocar o ano) e redesenha. */
export async function recarregarVista(): Promise<void> {
  const id = atual;
  render();
  await vistas.get(id)?.carregar?.().catch((e: unknown) => console.error(e));
  if (atual === id) render();
}

/** Estado do menu: quais grupos o usuário clicou para abrir (Map <grupo, true = aberto>). */
const estadoGrupos = new Map<string, boolean>();

registrarAcao("alternarGrupo", (alvo) => {
  const grupo = alvo.dataset.valor ?? "";
  if (!grupo) return;
  const estaAberto = estadoGrupos.get(grupo) ?? false;
  estadoGrupos.set(grupo, !estaAberto);
  renderMenu();
});

export function renderMenu(): void {
  const itens = [...vistas.values()].filter((v) => !v.somenteAdmin || eu.admin).sort((a, b) => posicao(a.id) - posicao(b.id));
  const botao = (v: Vista, sub: boolean): Safe => {
    const c = v.contagem?.() ?? "";
    return html`<button class="${sub ? "item-sub" : ""}" data-go="${v.id}" aria-current="${atual === v.id}">${v.nome}<span class="count">${c}</span></button>`;
  };
  const desenhados = new Set<string>();
  const blocos: Safe[] = [];
  for (const v of itens) {
    if (!v.grupo) {
      blocos.push(botao(v, false));
      continue;
    }
    if (desenhados.has(v.grupo)) continue;
    desenhados.add(v.grupo);
    const filhos = itens.filter((x) => x.grupo === v.grupo);
    const usuarioExplicitouEstado = estadoGrupos.has(v.grupo);
    const usuarioQuerAberto = estadoGrupos.get(v.grupo) ?? false;
    const voceEstaEmUmFilho = filhos.some((x) => x.id === atual);
    // Abre se: (1) usuário clicou para abrir OU (2) você está em um filho e usuário não explicitamente fechou
    const aberto = usuarioQuerAberto || (voceEstaEmUmFilho && !usuarioExplicitouEstado);
    blocos.push(html`<button class="nav-grupo" data-act="alternarGrupo" data-valor="${v.grupo}" aria-expanded="${aberto}">${v.grupo}<span class="seta" aria-hidden="true">›</span></button>${filhos.map((x) => html`<span class="nav-sub${aberto ? "" : " fechado"}">${botao(x, true)}</span>`)}`);
  }
  obrigatorio("#nav").innerHTML = String(html`${blocos}`);
}

export function render(): void {
  renderMenu();
  const el = $("#view");
  if (!el) return;
  const vista = vistas.get(atual) ?? vistas.get("painel");
  const aviso = conexao.semDados
    ? html`<div class="banner"><b>Os dados não carregaram.</b> Verifique a conexão com a internet e recarregue a página. Se continuar, saia e entre de novo com seu e-mail e senha.</div>`
    : conexao.somenteLeitura
      ? html`<div class="banner">Você está vendo o Hub Comercial em modo leitura.</div>`
      : "";
  el.innerHTML = String(html`${aviso}${vista?.desenhar()}`);
}

let aoNavegar: (id: string) => void = () => {};
export const observarNavegacao = (fn: (id: string) => void): void => {
  aoNavegar = fn;
};

export async function ir(id: string): Promise<void> {
  if (!vistas.has(id)) id = "painel";
  atual = id;
  try {
    localStorage.setItem(CHAVE_ABA, id);
  } catch {
    /* sem armazenamento: só não lembra a aba */
  }
  aoNavegar(id);
  render();
  window.scrollTo(0, 0);
  const v = vistas.get(id);
  if (v?.carregar) {
    await v.carregar().catch((e: unknown) => console.error(e));
    if (atual === id) render();
  }
}

export function abaSalva(): string {
  try {
    const salva = localStorage.getItem(CHAVE_ABA);
    if (salva && vistas.has(salva)) return salva;
  } catch {
    /* ignora */
  }
  return "painel";
}
export const definirAtual = (id: string): void => {
  atual = id;
};
