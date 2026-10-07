import "./styles/index.css";

import { api } from "@/api/endpoints";
import { sessaoToken } from "@/api/http";
import type { Usuario } from "@/api/tipos";
import { $, obrigatorio } from "@/core/dom";
import { conexao, eu, ui } from "@/state/estado";
import { abaSalva, carregarTudo, definirAtual, observarNavegacao, recarregar, render } from "@/state/nucleo";
import { tempoReal } from "@/state/realtime";
import { desenharOnline, indicarSincronizacao, mostrarConta } from "@/ui/casca";
import { iniciarAvisoDeConflito } from "@/ui/conflito";
import { detectarRotaConvite, iniciarTelaConvite } from "@/ui/convite";
import { iniciarEventos } from "@/ui/eventos";
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
  Object.assign(eu, { id: usuario.id, nome: usuario.nome, email: usuario.email, admin: usuario.admin });
  mostrarConta();
}

async function iniciarApp(usuario: Usuario): Promise<void> {
  iniciarSessaoNaTela(usuario);
  esconderLogin();
  definirAtual(abaSalva());
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

/** Retorna a empresa ativa e se o usuário é admin. */
async function selecionarEmpresa(): Promise<{ admin: boolean; empresa: { id: string; nome: string; onboarding_concluido?: boolean } }> {
  const empresas = await api.empresas.listar();
  const primeiraEmpresa = empresas[0];
  if (!primeiraEmpresa) throw new Error("Usuário sem associação ativa a uma empresa.");
  const seletor = obrigatorio<HTMLSelectElement>("#empresaAtiva");
  seletor.replaceChildren(...empresas.map((e) => {
    const opcao = document.createElement("option");
    opcao.value = e.id;
    opcao.textContent = e.nome;
    return opcao;
  }));
  const ativa = empresas.find((empresa) => empresa.id === sessaoToken.empresa()) ?? primeiraEmpresa;
  seletor.value = ativa.id;
  sessaoToken.definirEmpresa(seletor.value);
  seletor.hidden = empresas.length < 2;
  seletor.addEventListener("change", () => {
    sessaoToken.definirEmpresa(seletor.value);
    location.reload();
  });
  return { admin: ativa.papel === "admin", empresa: ativa };
}

async function principal(): Promise<void> {
  // /login/2fa só faz sentido logo após a senha; aberta direto ou recarregada, volta ao login.
  if (location.pathname === ROTA_2FA && !tokenSegundoFator.existe()) {
    history.replaceState(null, "", sessaoToken.obter() ? "/" : "/login");
  }
  iniciarEventos();
  ligarBuscas();
  iniciarAvisoDeConflito();
  obrigatorio("#sair").addEventListener("click", () => {
    tempoReal.parar();
    sessaoToken.definir(null);
    location.replace(location.pathname);
  });
  obrigatorio("#trocarSenha").addEventListener("click", () => void trocarSenha());
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

  let selecao: Awaited<ReturnType<typeof selecionarEmpresa>>;
  try {
    selecao = await selecionarEmpresa();
  } catch (erro) {
    console.error(erro);
    sessaoToken.definir(null);
    usuario = await pedirLogin("Não foi possível selecionar uma empresa para esta conta.");
    selecao = await selecionarEmpresa();
  }
  usuario.admin = selecao.admin;

  // Wizard de onboarding: exibido para admins de empresa nova antes de montar o app.
  if (detectarOnboarding({ usuario, empresa: selecao.empresa })) {
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
