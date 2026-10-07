/**
 * Barra superior: título da tela, "+ Novo", gatilho da paleta, tema e menu do usuário.
 * O HTML dos botões vive em `index.html` (vazios); aqui se preenche e se liga o comportamento.
 */
import { html } from "@/core/html";
import { iniciais, primeiroNome } from "@/core/formato";
import { acesso, eu } from "@/state/estado";
import { rotuloDoPapel } from "@/domain/papeis";
import { acoesRapidas, aoRenderizar, ir } from "@/state/nucleo";
import { despachar } from "@/ui/acoes";
import { icone } from "@/ui/icones";
import { cabecalhoDoUsuario, menuSuspenso } from "@/ui/menu-suspenso";
import { definirTema, iniciarTema, lerPreferencia, type PreferenciaTema } from "@/ui/tema";

export interface DependenciasDaBarra {
  aoSair: () => void;
  /** Descarta a empresa desta aba e reabre a escolha de empresa. */
  aoTrocarEmpresa: () => void;
  aoTrocarSenha: () => void;
  aoAbrirPaleta: () => void;
}

const $id = <T extends HTMLElement>(id: string): T | null => document.getElementById(id) as T | null;
const ehMac = (): boolean => /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent);
/** Texto do atalho da paleta, conforme o sistema do usuário. */
export const atalhoDaPaleta = (): string => (ehMac() ? "⌘ K" : "Ctrl K");

const ROTULO_TEMA: Record<PreferenciaTema, string> = { sistema: "Sistema", claro: "Claro", escuro: "Escuro" };
const ICONE_TEMA: Record<PreferenciaTema, string> = { sistema: "monitor", claro: "sol", escuro: "lua" };

function atualizarBotaoTema(pref: PreferenciaTema): void {
  const b = $id("btnTema");
  if (!b) return;
  b.innerHTML = String(icone(ICONE_TEMA[pref]));
  b.setAttribute("aria-label", `Tema: ${ROTULO_TEMA[pref]}`);
  b.title = `Tema: ${ROTULO_TEMA[pref]}`;
}

/** Bloco "Empresa ativa" do menu do usuário: nome da empresa e o papel do usuário nela (vêm do estado, não do DOM). */
function blocoEmpresa(): ReturnType<typeof html> {
  if (!acesso.empresaId) return html``;
  return html`<div class="emp"><label>Empresa ativa</label><b>${acesso.empresaNome}</b><span class="papel">${rotuloDoPapel(acesso.papel)}</span></div>`;
}

export function iniciarBarraSuperior(deps: DependenciasDaBarra): void {
  const menu = $id("abrirMenu");
  if (menu) menu.innerHTML = String(icone("menu"));

  const paleta = $id("abrirPaleta");
  if (paleta) {
    paleta.innerHTML = String(html`${icone("busca")}<span class="tx">Buscar telas e ações…</span><kbd>${atalhoDaPaleta()}</kbd>`);
    paleta.setAttribute("aria-label", `Abrir a paleta de comandos (${atalhoDaPaleta()})`);
    paleta.addEventListener("click", deps.aoAbrirPaleta);
  }

  const novo = $id("btnNovo");
  if (novo) {
    novo.innerHTML = String(html`${icone("mais")}<span class="tx">Novo</span>`);
    menuSuspenso({
      botao: novo,
      rotulo: "Criar novo",
      itens: () => acoesRapidas().map((a) => ({ rotulo: a.rotulo, icone: a.icone, aoEscolher: () => void despachar(a.id, document.body) })),
    });
  }

  const tema = $id("btnTema");
  if (tema) {
    menuSuspenso({
      botao: tema,
      rotulo: "Tema",
      itens: () =>
        (["sistema", "claro", "escuro"] as const).map((pref) => ({
          rotulo: ROTULO_TEMA[pref],
          icone: ICONE_TEMA[pref],
          marcado: lerPreferencia() === pref,
          aoEscolher: () => {
            definirTema(pref);
            atualizarBotaoTema(pref);
          },
        })),
    });
    iniciarTema((pref) => atualizarBotaoTema(pref));
  }

  const eu_ = $id("btnMe");
  if (eu_) {
    menuSuspenso({
      botao: eu_,
      rotulo: "Menu do usuário",
      cabecalho: () => html`${cabecalhoDoUsuario(iniciais(eu.nome), eu.nome, eu.email)}${blocoEmpresa()}<hr>`,
      itens: () => [
        { rotulo: "Minha conta", icone: "conta", aoEscolher: () => void ir("conta") },
        { rotulo: "Trocar de empresa", icone: "empresa", aoEscolher: deps.aoTrocarEmpresa },
        { rotulo: "Trocar senha", icone: "chave", aoEscolher: deps.aoTrocarSenha },
        { rotulo: "Sair", icone: "sair", separador: true, aoEscolher: deps.aoSair },
      ],
    });
  }

  // O título e a visibilidade do "+ Novo" acompanham a tela e o modo de leitura.
  aoRenderizar((nome) => {
    const t = $id("tituloTela");
    if (t) t.textContent = nome;
    document.title = `${nome} · Hub Comercial iSolutis`;
    if (novo) novo.hidden = acoesRapidas().length === 0;
  });
}

/** Mostra o botão do usuário (avatar com as iniciais e o primeiro nome) depois do login. */
export function mostrarUsuario(): void {
  const b = $id("btnMe");
  if (!b) return;
  b.innerHTML = String(html`<i class="av" aria-hidden="true">${iniciais(eu.nome)}</i><span class="nome">${primeiroNome(eu.nome)}</span>${icone("seta-b")}`);
  b.hidden = false;
}
