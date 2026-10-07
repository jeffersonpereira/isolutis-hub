import { api } from "@/api/endpoints";
import { html, raw, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { fluxoAtivar2FA, fluxoDesativar2FA, trocarSenha } from "@/ui/login";
import { toast } from "@/ui/toast";

/** Preferências pessoais do usuário logado. Acessível a qualquer papel: só afeta a própria conta. */
const tela: {
  totp2fa: boolean | null; // null = ainda carregando
  erro: string;
} = { totp2fa: null, erro: "" };

async function carregar(): Promise<void> {
  try {
    tela.totp2fa = (await api.auth.eu()).totp_ativo;
    tela.erro = "";
  } catch (e) {
    tela.erro = e instanceof Error ? e.message : "Não foi possível carregar os dados da sua conta.";
  }
}

function secaoDoisFatores(): Safe {
  if (tela.erro) {
    return html`<div class="banner" style="background:var(--bad-bg);color:var(--bad)">${tela.erro}</div>
      <button class="btn" data-act="recarregarConta">Tentar de novo</button>`;
  }
  const ativo = tela.totp2fa;
  if (ativo === null) return html`<p class="sub">Carregando…</p>`;
  return html`<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
      <span>Situação:
        ${ativo ? raw(`<span class="pill ok">Ativado ✓</span>`) : raw(`<span class="pill">Desativado</span>`)}
      </span>
      ${ativo
        ? html`<button class="btn danger" data-act="desativar2fa">Desativar 2FA</button>`
        : html`<button class="btn primary" data-act="ativar2fa">Ativar 2FA</button>`}
    </div>
    <div id="container2fa" style="margin-top:16px"></div>`;
}

function vista(): Safe {
  return html`<div class="head"><div><h1>Minha conta</h1><p>Preferências pessoais de acesso e segurança. Valem só para o seu usuário.</p></div></div>
    <section class="panel" style="max-width:680px">
      <h2 style="font-size:1rem;margin:0 0 4px">Autenticação em dois fatores</h2>
      <p class="sub" style="margin:0 0 12px">Pede um código do aplicativo autenticador, além da senha, a cada login.</p>
      ${secaoDoisFatores()}
    </section>
    <section class="panel" style="max-width:680px;margin-top:16px">
      <h2 style="font-size:1rem;margin:0 0 12px">Senha</h2>
      <button class="btn" data-act="trocarMinhaSenha">Trocar senha</button>
    </section>`;
}

registrarVista({ id: "conta", nome: "Minha conta", carregar, desenhar: vista });

registrarAcao("recarregarConta", async () => {
  tela.erro = "";
  tela.totp2fa = null;
  render();
  await carregar();
  render();
});

registrarAcao("trocarMinhaSenha", () => void trocarSenha());

registrarAcao("ativar2fa", async () => {
  const container = document.getElementById("container2fa");
  if (!container) return;
  if (await fluxoAtivar2FA(container)) {
    tela.totp2fa = true;
    render();
    toast("2FA ativado com sucesso.");
  }
});

registrarAcao("desativar2fa", async () => {
  const container = document.getElementById("container2fa");
  if (!container) return;
  if (await fluxoDesativar2FA(container)) {
    tela.totp2fa = false;
    render();
    toast("2FA desativado.");
  }
});
