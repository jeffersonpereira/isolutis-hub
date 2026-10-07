/**
 * Núcleo da interface: registro de vistas (telas), navegação, renderização e recarga de dados.
 * Cada funcionalidade registra a sua vista; este módulo não conhece nenhuma delas.
 */
import { api } from "@/api/endpoints";
import type { Permissao, Recurso } from "@/api/tipos";
import { $, obrigatorio } from "@/core/dom";
import { html, raw, type Safe } from "@/core/html";
import { registrarAcao } from "@/ui/acoes";
import { icone } from "@/ui/icones";
import { conexao, dados, temPermissao } from "./estado";
import { caminhoDaTela } from "./caminhos";
import { ACOES_DAS_TELAS, ESTRUTURA_MENU, ICONES_DAS_TELAS, type AcaoRapida } from "./menu";

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
  /** Permissão que o papel precisa ter para ver a tela (menu, paleta, "+ Novo" e URL). Sem ela, vale `base`: qualquer papel. */
  permissao?: Permissao;
  /** Tela acessível por rota, paleta e menu do usuário, mas fora do menu lateral. */
  oculta?: boolean;
  /** Agrupa a vista num submenu recolhível do menu lateral (ex.: "Financeiro"). */
  grupo?: string;
}

const vistas = new Map<string, Vista>();
let atual = "painel";
const CHAVE_ABA = "hub.aba";

export const registrarVista = (v: Vista): void => {
  vistas.set(v.id, v);
};
export const vistaAtual = (): string => atual;

/** Cada recurso em memória declara a permissão que o servidor exige; o que o papel não permite nem é pedido. */
const carregadores: Record<string, { permissao: Permissao; carregar: () => Promise<void> }> = {
  clientes: { permissao: "comercial", carregar: async () => void (dados.clientes = await api.clientes.listar()) },
  referenciasClientes: { permissao: "base", carregar: async () => void (dados.referenciasClientes = await api.clientes.referencias()) },
  negocios: { permissao: "comercial", carregar: async () => void (dados.negocios = await api.negocios.listar()) },
  orcamentos: { permissao: "comercial", carregar: async () => void (dados.orcamentos = await api.orcamentos.listar()) },
  produtos: { permissao: "comercial", carregar: async () => void (dados.produtos = await api.produtos.listar()) },
  projetos: { permissao: "base", carregar: async () => void (dados.projetos = await api.projetos.listar()) },
  tarefas: { permissao: "base", carregar: async () => void (dados.tarefas = await api.tarefas.listar()) },
  equipe: { permissao: "base", carregar: async () => void (dados.equipe = await api.equipe.listar()) },
};
export const RECURSOS_EM_MEMORIA = Object.keys(carregadores) as Recurso[];

/** Recursos pedidos que o papel pode carregar. Mudar clientes também renova a lista mínima de nomes. */
function recursosPermitidos(recursos: readonly string[]): string[] {
  const todos = new Set(recursos);
  if (todos.has("clientes")) todos.add("referenciasClientes");
  return [...todos].filter((r) => {
    const c = carregadores[r];
    return c !== undefined && temPermissao(c.permissao);
  });
}

type AoRecarregar = (recurso: string) => void;
const ouvintes: AoRecarregar[] = [];
/** Avisa quem precisa reagir a um recurso recarregado (ex.: gaveta aberta checando conflito de edição). */
export const aoRecarregar = (fn: AoRecarregar): void => void ouvintes.push(fn);

/** Recarrega recursos do servidor e redesenha. Chamado após cada gravação e quando o servidor avisa de mudanças. */
export async function recarregar(...recursos: string[]): Promise<void> {
  const unicos = [...new Set(recursos)];
  await Promise.all(recursosPermitidos(unicos).map((r) => carregadores[r]?.carregar().catch((e: unknown) => console.error(r, e))));
  const v = vistas.get(atual);
  if (v?.carregar && (v.depende ?? []).some((d) => unicos.includes(d))) await v.carregar().catch((e: unknown) => console.error(e));
  render();
  unicos.forEach((r) => ouvintes.forEach((fn) => fn(r)));
}

/**
 * Carrega o que o papel permite. Uma falha isolada não impede a abertura (as outras coleções carregam);
 * só quando TODAS falham o erro sobe, e a aplicação avisa que os dados não carregaram.
 */
export async function carregarTudo(): Promise<void> {
  const pedidos = recursosPermitidos(Object.keys(carregadores));
  const resultados = await Promise.allSettled(pedidos.map((r) => carregadores[r]?.carregar()));
  const falhas = resultados.filter((r): r is PromiseRejectedResult => r.status === "rejected");
  falhas.forEach((f) => console.error(f.reason));
  if (falhas.length > 0 && falhas.length === resultados.length) throw falhas[0]?.reason;
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
  // Com a barra recolhida só há ícones: abrir o grupo expande a barra para mostrar as telas dele.
  const casca = document.getElementById("app");
  const recolhida = casca?.classList.contains("recolhida") ?? false;
  if (recolhida) document.getElementById("recolher")?.click();
  estadoGrupos.set(grupo, recolhida ? true : !(estadoGrupos.get(grupo) ?? false));
  renderMenu();
});

/** Telas que o usuário pode abrir, na ordem do catálogo do menu (as fora do catálogo vão para o fim). */
export function vistasVisiveis(): Vista[] {
  const visiveis = [...vistas.values()].filter((v) => !v.permissao || temPermissao(v.permissao));
  const ordem = ESTRUTURA_MENU.flatMap((s) => s.itens.flatMap((i) => ("id" in i ? [i.id] : i.filhos)));
  const posicao = (id: string): number => {
    const i = ordem.indexOf(id);
    return i === -1 ? ordem.length : i;
  };
  return visiveis.sort((a, b) => posicao(a.id) - posicao(b.id));
}

/** Ações de criação das telas visíveis, para o "+ Novo" e a paleta (só quando o usuário pode escrever). */
export function acoesRapidas(): AcaoRapida[] {
  if (conexao.somenteLeitura || conexao.semDados) return [];
  return vistasVisiveis().flatMap((v) => ACOES_DAS_TELAS[v.id] ?? []);
}

export const iconeDaTela = (id: string): string => ICONES_DAS_TELAS[id] ?? "pasta";

export function renderMenu(): void {
  const visiveis = vistasVisiveis().filter((v) => !v.oculta);
  const porId = new Map(visiveis.map((v) => [v.id, v]));
  const usados = new Set<string>();
  const link = (v: Vista, sub = false): Safe => {
    usados.add(v.id);
    const c = v.contagem?.() ?? "";
    const ativo = atual === v.id;
    return html`<a href="/${v.id}" data-go="${v.id}"${ativo ? raw(' aria-current="page"') : ""} title="${v.nome}">${sub ? "" : icone(iconeDaTela(v.id))}<span class="tx">${v.nome}</span>${c !== "" && c !== 0 ? html`<span class="n">${c}</span>` : ""}</a>`;
  };
  const secoes: Safe[] = [];
  for (const secao of ESTRUTURA_MENU) {
    const blocos: Safe[] = [];
    for (const item of secao.itens) {
      if ("id" in item) {
        const v = porId.get(item.id);
        if (v) blocos.push(link(v));
        continue;
      }
      const filhos = item.filhos.map((id) => porId.get(id)).filter((v): v is Vista => !!v);
      if (!filhos.length) continue;
      const ativoNoFilho = filhos.some((v) => v.id === atual);
      const aberto = estadoGrupos.get(item.grupo) ?? ativoNoFilho;
      blocos.push(html`<button type="button" class="nav-grupo" data-act="alternarGrupo" data-valor="${item.grupo}" aria-expanded="${String(aberto)}" title="${item.grupo}">${icone(item.icone)}<span class="tx">${item.grupo}</span>${icone("seta-b", { classe: "chev" })}</button>
        <div class="sub-menu${aberto ? "" : " fechado"}">${filhos.map((v) => link(v, true))}</div>`);
    }
    if (blocos.length) secoes.push(html`${secao.rotulo ? html`<div class="rot">${secao.rotulo}</div>` : ""}${blocos}`);
  }
  const sobras = visiveis.filter((v) => !usados.has(v.id) && !ESTRUTURA_MENU.some((s) => s.itens.some((i) => ("id" in i ? i.id === v.id : i.filhos.includes(v.id)))));
  if (sobras.length) secoes.push(html`<div class="rot">Outros</div>${sobras.map((v) => link(v))}`);
  obrigatorio("#nav").innerHTML = String(html`${secoes}`);
}

type AoRenderizar = (nomeDaTela: string) => void;
const ouvintesDeRender: AoRenderizar[] = [];
/** Avisa quem precisa reagir a cada redesenho (barra superior: título e ações). */
export const aoRenderizar = (fn: AoRenderizar): void => void ouvintesDeRender.push(fn);

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
  if (!conteudoTravado) el.innerHTML = String(html`${aviso}${vista?.desenhar()}`);
  ouvintesDeRender.forEach((fn) => fn(vista?.nome ?? ""));
}

let aoNavegar: (id: string) => void = () => {};
export const observarNavegacao = (fn: (id: string) => void): void => {
  aoNavegar = fn;
};

/**
 * Guarda de saída: quem tem algo a perder (formulário em página com alterações) registra uma função que
 * devolve `false` para impedir a troca de tela. Vale para o menu, a paleta e o Voltar do navegador.
 */
type Guarda = () => boolean | Promise<boolean>;
let guarda: Guarda | null = null;
let aoSairDaPagina: (() => void) | null = null;
/**
 * `aoSair` roda quando a tela realmente muda (depois da guarda): é onde o formulário em página se desfaz
 * (destrava o conteúdo, encerra a presença "editando…" e remove seus ouvintes).
 */
export const registrarGuarda = (g: Guarda | null, aoSair?: () => void): void => {
  guarda = g;
  aoSairDaPagina = aoSair ?? null;
};
export const podeSair = async (): Promise<boolean> => (guarda ? await guarda() : true);

/** Desfaz a página aberta (formulário em página), se houver: roda o `aoSair` registrado e limpa a guarda. */
export function sairDaPagina(): void {
  const limpar = aoSairDaPagina;
  guarda = null;
  aoSairDaPagina = null;
  limpar?.();
}

/** Enquanto travado, `render()` não redesenha a área principal (formulário em página aberto). */
let conteudoTravado = false;
export const travarConteudo = (travado: boolean): void => {
  conteudoTravado = travado;
};

let ultimoCaminho = typeof location === "undefined" ? "/" : location.pathname;
export const caminhoAtual = (): string => ultimoCaminho;

/** Atualiza o endereço do navegador sem recarregar. Não repete a entrada se o caminho já é o atual. */
export function atualizarUrl(caminho: string, modo: "push" | "replace" = "push"): void {
  if (location.pathname !== caminho) {
    if (modo === "replace") history.replaceState(null, "", caminho);
    else history.pushState(null, "", caminho);
  }
  ultimoCaminho = caminho;
}

export interface OpcoesIr {
  /** `push` (padrão) cria entrada no histórico; `replace` troca a atual; `nenhum` não mexe na URL (já está certa). */
  historico?: "push" | "replace" | "nenhum";
  /** A guarda de saída já foi consultada por quem chama (evita perguntar duas vezes). */
  semGuarda?: boolean;
}

export async function ir(id: string, opcoes: OpcoesIr = {}): Promise<void> {
  if (!vistas.has(id)) id = "painel";
  if (!opcoes.semGuarda && !(await podeSair())) return;
  sairDaPagina();
  atual = id;
  try {
    localStorage.setItem(CHAVE_ABA, id);
  } catch {
    /* sem armazenamento: só não lembra a aba */
  }
  const modo = opcoes.historico ?? "push";
  if (modo === "nenhum") ultimoCaminho = location.pathname;
  else atualizarUrl(caminhoDaTela(id), modo);
  aoNavegar(id);
  render();
  const area = $("#view");
  if (area) area.scrollTop = 0;
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
