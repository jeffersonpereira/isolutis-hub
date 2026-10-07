import { api } from "@/api/endpoints";
import { ErroApi, sessaoToken } from "@/api/http";
import type { Usuario } from "@/api/tipos";
import { obrigatorio } from "@/core/dom";
import { abrirSegundoFator, tokenSegundoFator } from "@/ui/segundo-fator";

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
          // 2FA requerido: a etapa do código tem rota própria; cancelar devolve ao formulário
          el<HTMLInputElement>("lgSenha").value = "";
          mensagem("");
          tokenSegundoFator.definir(r.token_temporario);
          const usuario = await abrirSegundoFator(mensagem);
          if (usuario) resolve(usuario);
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
    container.innerHTML = `<p class="sub" style="color:var(--bad-texto)">${err instanceof ErroApi ? err.message : "Não foi possível iniciar o setup."}</p>`;
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
        <p id="totpConfirmMsg" style="margin:0;min-height:1.2em;font-size:var(--text-xs);color:var(--bad-texto)"></p>
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
        container.innerHTML = `<p style="color:var(--ok-texto);font-weight:600">2FA ativado com sucesso.</p>`;
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
        <p id="totpDesatMsg" style="margin:0;min-height:1.2em;font-size:var(--text-xs);color:var(--bad-texto)"></p>
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
