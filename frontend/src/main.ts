import "./styles/index.css";

import { api } from "@/api/endpoints";
import { sessaoToken } from "@/api/http";
import type { Usuario } from "@/api/tipos";
import { $, obrigatorio } from "@/core/dom";
import type { EmpresaAcesso } from "@/api/tipos";
import { decidirEmpresa } from "@/state/empresa-ativa";
import { escolherEmpresa, telaSemAcesso } from "@/ui/escolha-empresa";
import { acesso, conexao, eu, ui } from "@/state/estado";
import { abaSalva, atualizarUrl, carregarTudo, definirAtual, observarNavegacao, recarregar, render } from "@/state/nucleo";
import { aplicarRegistroDaRota, iniciarRoteador, resolverRotaInicial } from "@/state/roteador";
import { tempoReal } from "@/state/realtime";
import { desenharOnline, indicarSincronizacao, iniciarBarraLateral } from "@/ui/casca";
import { iniciarBarraSuperior, mostrarUsuario } from "@/ui/barra-superior";
import { iniciarAvisoDeConflito } from "@/ui/conflito";
import { detectarRotaConvite, iniciarTelaConvite } from "@/ui/convite";
import { concluirConvitePendente, convitePendente } from "@/ui/convite-pendente";
import { iniciarEventos } from "@/ui/eventos";
import { abrirPaleta, ligarAtalhoDaPaleta } from "@/ui/paleta";
import { montarSprite } from "@/ui/icones";
import { observarGaveta } from "@/ui/gaveta";
import { esconderLogin, pedirLogin, trocarSenha } from "@/ui/login";
import { detectarOnboarding, iniciarWizardOnboarding } from "@/ui/onboarding";
import { ROTA_2FA, tokenSegundoFator } from "@/ui/segundo-fator";

// As funcionalidades se registram ao serem importadas; a ordem define a ordem do menu.
import "@/features/painel";
import "@/features/clientes";
import "@/features/negocios";
import "@/features/orcamentos";
import "@/features/projetos";
import "@/features/tarefas";
import "@/features/produtos";
import "@/features/financeiro";
import "@/features/despesas";
import "@/features/faturamento";
import "@/features/relatorios";
import "@/features/equipe";
import "@/features/empresa";
import "@/features/conta";
import "@/features/periodo";

/** Busca nas listas: refaz a tela a cada tecla e devolve o foco ao campo. */
function ligarBuscas(): void {
  obrigatorio("#view").addEventListener("input", (e) => {
    const campo = e.target as HTMLInputElement;
    const chave = campo.dataset.busca as "busca" | "tarefaBusca" | "buscaFin" | undefined;
    if (!chave) return;
    ui[chave] = campo.value;
    const pos = campo.selectionStart ?? campo.value.length;
    render();
    const novo = $<HTMLInputElement>(`[data-busca="${chave}"]`);
    novo?.focus();
    novo?.setSelectionRange(pos, pos);
  });
}

function iniciarSessaoNaTela(usuario: Usuario): void {
  Object.assign(eu, { id: usuario.id, nome: usuario.nome, email: usuario.email });
  mostrarUsuario();
}

async function iniciarApp(usuario: Usuario): Promise<void> {
  iniciarSessaoNaTela(usuario);
  esconderLogin();
  const inicial = resolverRotaInicial();
  definirAtual(inicial.vista);
  if (inicial.corrigir) atualizarUrl(inicial.corrigir, "replace");
  render();
  try {
    await carregarTudo();
    conexao.semDados = false;
  } catch (e) {
    console.error(e);
    conexao.semDados = true;
    indicarSincronizacao("off", "Sem conexão com o banco de dados");
  }
  render();
  aplicarRegistroDaRota(inicial.registro);
  iniciarRoteador();

  let recargaPendente: number | undefined;
  const pendentes = new Set<string>();
  tempoReal.iniciar({
    presenca: desenharOnline,
    conexao: (conectado) => {
      if (!conexao.semDados) indicarSincronizacao(conectado ? "on" : "off", conectado ? "Dados da equipe sincronizados" : "Conexão interrompida. Reconectando…");
    },
    // O servidor avisa quais recursos mudaram; junta os avisos próximos e recarrega uma vez.
    alterado: (recursos) => {
      recursos.forEach((r) => pendentes.add(r));
      window.clearTimeout(recargaPendente);
      recargaPendente = window.setTimeout(() => {
        const lote = [...pendentes];
        pendentes.clear();
        void recarregar(...lote);
      }, 120);
    },
  });
  observarNavegacao((id) => tempoReal.presenca({ area: id }));
  observarGaveta((titulo, editando) => tempoReal.presenca({ editando: editando ? titulo : null }));
  tempoReal.presenca({ area: abaSalva(), editando: null });
}

/** Sai da sessão: nada da escolha de empresa pode sobrar para a próxima pessoa no mesmo navegador. */
function sair(): void {
  tempoReal.parar();
  sessaoToken.definir(null);
  sessaoToken.limparEmpresas();
  convitePendente.limpar();
  location.replace(location.pathname);
}

/** Descarta a empresa desta aba e recarrega: a tela de escolha reaparece e nenhum dado da empresa anterior fica em memória. */
function trocarEmpresa(): void {
  tempoReal.parar();
  sessaoToken.esquecerEmpresaDaAba();
  location.reload();
}

/**
 * Define a empresa ativa desta aba: mantém a guardada se o usuário ainda tem acesso a ela, senão mostra a tela de escolha
 * (a última usada vem pré-selecionada). Sem nenhuma empresa, explica e só oferece sair; nada é carregado.
 */
async function selecionarEmpresa(): Promise<EmpresaAcesso> {
  const empresas = await api.empresas.listar();
  const decisao = decidirEmpresa(empresas, sessaoToken.empresa(), sessaoToken.ultimaEmpresa());
  if (decisao.tipo === "nenhuma") {
    sessaoToken.esquecerEmpresaDaAba();
    telaSemAcesso(sair);
    return new Promise<EmpresaAcesso>(() => {}); // a aplicação não segue
  }
  const ativa = decisao.tipo === "seguir" ? decisao.empresa : await escolherEmpresa(empresas, decisao.sugerida, sair);
  sessaoToken.definirEmpresa(ativa.id);
  acesso.empresaId = ativa.id;
  acesso.empresaNome = ativa.nome;
  acesso.papel = ativa.papel;
  acesso.permissoes = ativa.permissoes;
  return ativa;
}

async function principal(): Promise<void> {
  // /login/2fa só faz sentido logo após a senha; aberta direto ou recarregada, volta ao login.
  if (location.pathname === ROTA_2FA && !tokenSegundoFator.existe()) {
    history.replaceState(null, "", sessaoToken.obter() ? "/" : "/login");
  }
  iniciarEventos();
  ligarBuscas();
  iniciarAvisoDeConflito();
  montarSprite();
  // "Pular para o conteúdo" leva o foco à área principal sem mexer no endereço
  document.querySelector(".pular")?.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("view")?.focus();
  });
  iniciarBarraLateral();
  iniciarBarraSuperior({
    aoSair: sair,
    aoTrocarEmpresa: trocarEmpresa,
    aoTrocarSenha: () => void trocarSenha(),
    aoAbrirPaleta: abrirPaleta,
  });
  ligarAtalhoDaPaleta();
  // Se o servidor recusar a empresa ativa (acesso removido durante a sessão), a aba volta à escolha de empresa.
  sessaoToken.aoPerderEmpresa(() => {
    tempoReal.parar();
    location.reload();
  });
  sessaoToken.aoExpirar(() => {
    tempoReal.parar();
    void pedirLogin("Sua sessão expirou. Entre de novo para continuar.").then(() => location.reload());
  });

  let usuario: Usuario | null = null;
  if (sessaoToken.obter()) {
    try {
      usuario = await api.auth.eu();
    } catch {
      sessaoToken.definir(null);
    }
  }
  if (!usuario) usuario = await pedirLogin();

  // Convite de quem já tinha conta: conclui o aceite agora que o login (e o 2FA) aconteceu.
  await concluirConvitePendente();

  let empresaAtiva: EmpresaAcesso;
  try {
    empresaAtiva = await selecionarEmpresa();
  } catch (erro) {
    console.error(erro);
    sessaoToken.definir(null);
    usuario = await pedirLogin("Não foi possível selecionar uma empresa para esta conta.");
    empresaAtiva = await selecionarEmpresa();
  }

  // Wizard de onboarding: exibido para administradores de empresa nova antes de montar o app.
  if (detectarOnboarding({ usuario, empresa: empresaAtiva, permissoes: empresaAtiva.permissoes })) {
    await iniciarWizardOnboarding();
  }

  if (location.pathname.startsWith("/login")) history.replaceState(null, "", "/");
  await iniciarApp(usuario);
}

// Rota pública de convite: se a URL for /convite/:token, exibe a tela de aceitação.
const tokenConvite = detectarRotaConvite();
if (tokenConvite) {
  void iniciarTelaConvite(tokenConvite);
} else {
  void principal();
}
