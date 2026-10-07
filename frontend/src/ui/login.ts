import { api } from "@/api/endpoints";
import { ErroApi, sessaoToken } from "@/api/http";
import type { Usuario } from "@/api/tipos";
import { obrigatorio } from "@/core/dom";

/** Telas de entrada e de troca de senha (mesmo visual do sistema anterior). */
const el = <T extends HTMLElement>(id: string): T => obrigatorio<T>(`#${id}`);

function mensagem(texto: string, erro = false): void {
  const m = el("lgMsg");
  m.textContent = texto;
  m.classList.toggle("erro", erro);
}

function mostrar(qual: "lgEntrar" | "lgNova"): void {
  el("login").hidden = false;
  (["lgEntrar", "lgNova"] as const).forEach((id) => (el(id).hidden = id !== qual));
}

export const esconderLogin = (): void => {
  el("login").hidden = true;
  mensagem("");
};

// ─── 2FA ─────────────────────────────────────────────────────────────────────

/**
 * Exibe o formulário de código 2FA sobre o formulário de login.
 * Resolve com o usuário autenticado quando o código for verificado.
 */
function mostrarTela2FA(tokenTemporario: string): Promise<Usuario> {
  const lgEntrar = el("lgEntrar");

  // Injeta o formulário de 2FA dentro da caixa de login existente
  const conteiner = document.createElement("div");
  conteiner.id = "lg2fa";
  conteiner.innerHTML = `
    <form id="lg2faForm" novalidate style="display:flex;flex-direction:column;gap:12px">
      <h2 style="margin:0;font-size:1rem;font-weight:600">Autenticação em dois fatores</h2>
      <p style="margin:0;font-size:var(--text-xs);color:var(--muted)">
        Digite o código de 6 dígitos do seu aplicativo autenticador.
      </p>
      <div class="field">
        <label for="lg2faCodigo">Código</label>
        <input id="lg2faCodigo" name="codigo" inputmode="numeric" maxlength="6"
          autocomplete="one-time-code" placeholder="000000" required
          style="font-size:1.25rem;letter-spacing:.2em;text-align:center">
      </div>
      <p id="lg2faMsg" class="lg-msg" role="status" style="margin:0"></p>
      <button class="btn primary" type="submit" id="lg2faBotao">Verificar</button>
      <button class="btn ghost" type="button" id="lg2faVoltar" style="text-align:center">
        Voltar ao login
      </button>
      <button class="btn ghost" type="button" id="lg2faBackup"
        style="font-size:var(--text-xs);text-align:center">
        Usar código de backup
      </button>
    </form>`;

  lgEntrar.hidden = true;
  lgEntrar.parentElement?.insertBefore(conteiner, lgEntrar.nextSibling);

  const form2fa = document.getElementById("lg2faForm") as HTMLFormElement;
  const campoCodigo = document.getElementById("lg2faCodigo") as HTMLInputElement;
  const botao2fa = document.getElementById("lg2faBotao") as HTMLButtonElement;

  const msg2fa = (texto: string, erro = false): void => {
    const m = document.getElementById("lg2faMsg");
    if (!m) return;
    m.textContent = texto;
    m.classList.toggle("erro", erro);
  };

  setTimeout(() => campoCodigo.focus(), 50);

  let usandoBackup = false;
  document.getElementById("lg2faBackup")?.addEventListener("click", () => {
    usandoBackup = !usandoBackup;
    if (usandoBackup) {
      campoCodigo.removeAttribute("inputmode");
      campoCodigo.removeAttribute("maxlength");
      campoCodigo.placeholder = "Código de backup";
      campoCodigo.style.letterSpacing = "normal";
      campoCodigo.style.fontSize = "1rem";
      (document.getElementById("lg2faBackup") as HTMLButtonElement).textContent = "Usar código do app";
    } else {
      campoCodigo.setAttribute("inputmode", "numeric");
      campoCodigo.setAttribute("maxlength", "6");
      campoCodigo.placeholder = "000000";
      campoCodigo.style.letterSpacing = ".2em";
      campoCodigo.style.fontSize = "1.25rem";
      (document.getElementById("lg2faBackup") as HTMLButtonElement).textContent = "Usar código de backup";
    }
    campoCodigo.value = "";
    campoCodigo.focus();
  });

  return new Promise((resolve) => {
    document.getElementById("lg2faVoltar")?.addEventListener("click", () => {
      conteiner.remove();
      lgEntrar.hidden = false;
      mensagem("");
      setTimeout(() => el("lgEmail").focus(), 50);
      // Registrar novamente o handler de submit para permitir nova tentativa
      // (a promise ficará sem resolução; o caller de pedirLogin recria o handler via onsubmit)
    });

    form2fa.onsubmit = async (e) => {
      e.preventDefault();
      const codigo = campoCodigo.value.trim().replace(/\s/g, "");
      if (!codigo) return msg2fa("Digite o código.", true);
      botao2fa.disabled = true;
      msg2fa("Verificando…");
      try {
        const r = await api.auth.totp.verificar({ token_temporario: tokenTemporario, codigo });
        sessaoToken.definir(r.access_token);
        conteiner.remove();
        lgEntrar.hidden = false;
        mensagem("");
        resolve(r.usuario);
      } catch (err) {
        msg2fa(err instanceof ErroApi ? err.message : "Código inválido. Tente de novo.", true);
        campoCodigo.value = "";
        campoCodigo.focus();
        botao2fa.disabled = false;
      }
    };
  });
}

/** Mostra o login e resolve com o usuário quando a pessoa entra. */
export function pedirLogin(aviso?: string): Promise<Usuario> {
  mostrar("lgEntrar");
  mensagem(aviso ?? "", !!aviso);
  setTimeout(() => el("lgEmail").focus(), 50);
  return new Promise((resolve) => {
    el<HTMLFormElement>("lgEntrar").onsubmit = async (e) => {
      e.preventDefault();
      const email = el<HTMLInputElement>("lgEmail").value.trim();
      const senha = el<HTMLInputElement>("lgSenha").value;
      if (!email || !senha) return mensagem("Preencha o e-mail e a senha.", true);
      const botao = el<HTMLButtonElement>("lgBotao");
      botao.disabled = true;
      mensagem("Entrando…");
      try {
        const r = await api.auth.login(email, senha);

        if (r.requer_2fa && r.token_temporario) {
          // 2FA requerido: limpar senha e mostrar tela de código
          el<HTMLInputElement>("lgSenha").value = "";
          mensagem("");
          botao.disabled = false;
          const usuario = await mostrarTela2FA(r.token_temporario);
          resolve(usuario);
          return;
        }

        sessaoToken.definir(r.access_token);
        el<HTMLInputElement>("lgSenha").value = "";
        mensagem("");
        resolve(r.usuario);
      } catch (err) {
        mensagem(err instanceof ErroApi ? err.message : "Não foi possível entrar agora.", true);
      } finally {
        botao.disabled = false;
      }
    };
  });
}

/** Troca de senha de quem já está logado; resolve ao salvar ou cancelar. */
export function trocarSenha(): Promise<void> {
  mostrar("lgNova");
  mensagem("");
  setTimeout(() => el("lgAtual").focus(), 50);
  return new Promise((resolve) => {
    const fechar = (): void => {
      ["lgAtual", "lgNova1", "lgNova2"].forEach((id) => (el<HTMLInputElement>(id).value = ""));
      esconderLogin();
      resolve();
    };
    el("lgCancelar").onclick = fechar;
    el<HTMLFormElement>("lgNova").onsubmit = async (e) => {
      e.preventDefault();
      const atual = el<HTMLInputElement>("lgAtual").value;
      const a = el<HTMLInputElement>("lgNova1").value;
      const b = el<HTMLInputElement>("lgNova2").value;
      if (a.length < 8) return mensagem("A senha precisa ter pelo menos 8 caracteres.", true);
      if (a !== b) return mensagem("As duas senhas não são iguais.", true);
      try {
        await api.auth.trocarSenha(atual, a);
        mensagem("Senha salva.");
        setTimeout(fechar, 600);
      } catch (err) {
        mensagem(err instanceof ErroApi ? err.message : "Não foi possível salvar a senha.", true);
      }
    };
  });
}

// ─── Setup de 2FA (usado em configurações/equipe) ────────────────────────────

/**
 * Abre o fluxo completo de ativação de 2FA num elemento container fornecido.
 * Resolve `true` quando ativado com sucesso, `false` se cancelado.
 */
export async function fluxoAtivar2FA(container: HTMLElement): Promise<boolean> {
  container.innerHTML = `<p style="color:var(--muted);font-size:var(--text-xs)">Carregando configuração…</p>`;

  let setup;
  try {
    setup = await api.auth.totp.setup();
  } catch (err) {
    container.innerHTML = `<p class="sub" style="color:var(--bad)">${err instanceof ErroApi ? err.message : "Não foi possível iniciar o setup."}</p>`;
    return false;
  }

  return new Promise((resolve) => {
    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:16px;max-width:420px">
        <img src="${setup.qr_code}"
             alt="QR Code para configurar o autenticador"
             style="width:200px;height:200px;border:1px solid var(--line);border-radius:8px;padding:8px;background:#fff;align-self:center">
        <p style="margin:0;font-size:var(--text-xs);color:var(--muted)">
          Escaneie este QR code com Google Authenticator, Authy ou outro app TOTP.
          Depois, confirme com o código gerado pelo aplicativo.
        </p>
        <div class="field">
          <label for="totpConfirmCodigo">Código de 6 dígitos do app</label>
          <input id="totpConfirmCodigo" inputmode="numeric" maxlength="6"
            autocomplete="one-time-code" placeholder="000000"
            style="font-size:1.25rem;letter-spacing:.2em;text-align:center">
        </div>
        <p id="totpConfirmMsg" style="margin:0;min-height:1.2em;font-size:var(--text-xs);color:var(--bad)"></p>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn primary" id="totpConfirmBotao">Confirmar ativação</button>
          <button class="btn ghost" id="totpConfirmCancelar">Cancelar</button>
        </div>
        <details style="font-size:var(--text-xs)">
          <summary style="cursor:pointer;color:var(--muted)">Códigos de backup (guarde em lugar seguro)</summary>
          <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">
            ${setup.backup_codes.map((c) => `<code style="background:var(--sunk);border-radius:4px;padding:2px 8px">${c}</code>`).join("")}
          </div>
        </details>
      </div>`;

    const campoCodigo = document.getElementById("totpConfirmCodigo") as HTMLInputElement;
    const botaoConfirmar = document.getElementById("totpConfirmBotao") as HTMLButtonElement;
    const msgEl = document.getElementById("totpConfirmMsg") as HTMLElement;

    setTimeout(() => campoCodigo.focus(), 50);

    const setMsg = (t: string): void => { msgEl.textContent = t; };

    document.getElementById("totpConfirmCancelar")?.addEventListener("click", () => {
      container.innerHTML = "";
      resolve(false);
    });

    botaoConfirmar.addEventListener("click", async () => {
      const codigo = campoCodigo.value.trim().replace(/\s/g, "");
      if (codigo.length !== 6) return setMsg("Digite os 6 dígitos do código.");
      botaoConfirmar.disabled = true;
      setMsg("");
      try {
        const resultado = await api.auth.totp.confirmar({ codigo, backup_codes: setup.backup_codes });
        // Atualiza o token pois versao_sessao foi incrementada ao ativar 2FA
        sessaoToken.definir(resultado.access_token);
        container.innerHTML = `<p style="color:var(--ok);font-weight:600">2FA ativado com sucesso.</p>`;
        resolve(true);
      } catch (err) {
        setMsg(err instanceof ErroApi ? err.message : "Código inválido. Tente de novo.");
        campoCodigo.value = "";
        campoCodigo.focus();
        botaoConfirmar.disabled = false;
      }
    });
  });
}

/**
 * Fluxo de desativação de 2FA: pede código atual e chama DELETE /auth/2fa.
 * Resolve `true` se desativado, `false` se cancelado.
 */
export async function fluxoDesativar2FA(container: HTMLElement): Promise<boolean> {
  return new Promise((resolve) => {
    container.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:12px;max-width:420px">
        <p style="margin:0;font-size:var(--text-xs);color:var(--muted)">
          Para desativar o 2FA, confirme com o código atual do seu app autenticador.
        </p>
        <div class="field">
          <label for="totpDesatCodigo">Código do app</label>
          <input id="totpDesatCodigo" inputmode="numeric" maxlength="6"
            autocomplete="one-time-code" placeholder="000000"
            style="font-size:1.25rem;letter-spacing:.2em;text-align:center">
        </div>
        <p id="totpDesatMsg" style="margin:0;min-height:1.2em;font-size:var(--text-xs);color:var(--bad)"></p>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn danger" id="totpDesatBotao">Desativar 2FA</button>
          <button class="btn ghost" id="totpDesatCancelar">Cancelar</button>
        </div>
      </div>`;

    const campoCodigo = document.getElementById("totpDesatCodigo") as HTMLInputElement;
    const botaoDesat = document.getElementById("totpDesatBotao") as HTMLButtonElement;
    const msgEl = document.getElementById("totpDesatMsg") as HTMLElement;
    const setMsg = (t: string): void => { msgEl.textContent = t; };

    setTimeout(() => campoCodigo.focus(), 50);

    document.getElementById("totpDesatCancelar")?.addEventListener("click", () => {
      container.innerHTML = "";
      resolve(false);
    });

    botaoDesat.addEventListener("click", async () => {
      const codigo = campoCodigo.value.trim().replace(/\s/g, "");
      if (!codigo) return setMsg("Digite o código.");
      botaoDesat.disabled = true;
      setMsg("");
      try {
        await api.auth.totp.desativar(codigo);
        container.innerHTML = `<p style="color:var(--muted)">2FA desativado.</p>`;
        resolve(true);
      } catch (err) {
        setMsg(err instanceof ErroApi ? err.message : "Não foi possível desativar o 2FA.");
        campoCodigo.value = "";
        campoCodigo.focus();
        botaoDesat.disabled = false;
      }
    });
  });
}
