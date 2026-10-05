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
