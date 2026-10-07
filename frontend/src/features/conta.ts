import { api } from "@/api/endpoints";
import { html, raw, type Safe } from "@/core/html";
import { registrarVista, render, travarConteudo } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { cabecalhoDePagina, carregando, estadoDeErro } from "@/ui/componentes";
import { fluxoAtivar2FA, fluxoDesativar2FA, trocarSenha } from "@/ui/login";
import { toast } from "@/ui/toast";

/** Preferências pessoais do usuário logado. Acessível a qualquer papel: só afeta a própria conta. */
const tela: {
  totp2fa: boolean | null; // null = ainda carregando
  erro: string;
  emFluxo: boolean; // fluxo de ativar/desativar 2FA aberto: ignora novo clique e congela o redesenho
} = { totp2fa: null, erro: "", emFluxo: false };

async function carregar(): Promise<void> {
  try {
    tela.totp2fa = (await api.auth.eu()).totp_ativo;
    tela.erro = "";
  } catch (e) {
    tela.erro = e instanceof Error ? e.message : "Não foi possível carregar os dados da sua conta.";
  }
}

function secaoDoisFatores(): Safe {
  if (tela.erro) return estadoDeErro({ mensagem: tela.erro, acaoRepetir: "recarregarConta" });
  const ativo = tela.totp2fa;
  if (ativo === null) return carregando("Carregando a sua conta…");
  return html`<div class="fila">
      <span>Situação:
        ${ativo ? raw(`<span class="pill ok">Ativado</span>`) : raw(`<span class="pill">Desativado</span>`)}
      </span>
      ${ativo
        ? html`<button class="btn danger" data-act="desativar2fa">Desativar 2FA</button>`
        : html`<button class="btn primary" data-act="ativar2fa">Ativar 2FA</button>`}
    </div>
    <div id="container2fa" class="mt"></div>`;
}

function vista(): Safe {
  return html`${cabecalhoDePagina({ titulo: "Minha conta", descricao: "Preferências pessoais de acesso e segurança. Valem só para o seu usuário." })}
    <section class="panel estreita">
      <h2>Autenticação em dois fatores</h2>
      <p class="sub desc">Pede um código do aplicativo autenticador, além da senha, a cada login.</p>
      ${secaoDoisFatores()}
    </section>
    <section class="panel estreita">
      <h2>Senha</h2>
      <button class="btn" data-act="trocarMinhaSenha">Trocar senha</button>
    </section>`;
}

registrarVista({ id: "conta", nome: "Minha conta", oculta: true, carregar, desenhar: vista });

registrarAcao("recarregarConta", async () => {
  tela.erro = "";
  tela.totp2fa = null;
  render();
  await carregar();
  render();
});

registrarAcao("trocarMinhaSenha", () => void trocarSenha());

/**
 * Conduz um fluxo de 2FA dentro de `#container2fa`. Enquanto ele está aberto, o conteúdo fica travado: um
 * `recarregar()` em segundo plano redesenharia a tela e apagaria o QR code e o campo do código.
 */
async function conduzir2FA(fluxo: (container: HTMLElement) => Promise<boolean>, ativo: boolean, aviso: string): Promise<void> {
  const container = document.getElementById("container2fa");
  if (!container || tela.emFluxo) return;
  tela.emFluxo = true;
  travarConteudo(true);
  let concluido: boolean;
  try {
    concluido = await fluxo(container);
  } finally {
    travarConteudo(false);
    tela.emFluxo = false;
  }
  if (concluido) {
    tela.totp2fa = ativo;
    toast(aviso);
  }
  render();
}

registrarAcao("ativar2fa", () => conduzir2FA(fluxoAtivar2FA, true, "2FA ativado com sucesso."));
registrarAcao("desativar2fa", () => conduzir2FA(fluxoDesativar2FA, false, "2FA desativado."));
