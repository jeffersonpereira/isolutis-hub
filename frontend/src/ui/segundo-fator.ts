import { api } from "@/api/endpoints";
import { ErroApi, sessaoToken } from "@/api/http";
import type { Usuario } from "@/api/tipos";
import { obrigatorio } from "@/core/dom";

/** Rota da etapa de código do 2FA. Fica fora do login para ter URL própria. */
export const ROTA_2FA = "/login/2fa";
const ROTA_LOGIN = "/login";

/**
 * Token temporário do login em duas etapas. Vive só em memória: nunca vai à URL,
 * a localStorage nem a sessionStorage. Recarregar a página o descarta (volta ao login).
 */
let tokenPendente: string | null = null;
export const tokenSegundoFator = {
  definir(valor: string): void {
    tokenPendente = valor;
  },
  obter: (): string | null => tokenPendente,
  existe: (): boolean => tokenPendente !== null,
  limpar(): void {
    tokenPendente = null;
  },
};

/** Mostra uma mensagem de estado (ou erro) na área de status do login. */
type Aviso = (texto: string, erro?: boolean) => void;

/** Erros em que o token temporário não serve mais: é preciso entrar de novo. */
const ENCERRAM_O_FLUXO = new Set([401, 429]);

/**
 * Mostra a etapa de código em `/login/2fa`. Resolve com o usuário quando o código é aceito
 * e com `null` se a pessoa voltar ao login (botão, voltar do navegador) ou o token deixar de valer.
 */
export function abrirSegundoFator(aviso: Aviso): Promise<Usuario | null> {
  const entrar = obrigatorio<HTMLFormElement>("#lgEntrar");
  if (!tokenSegundoFator.existe()) {
    history.replaceState(null, "", ROTA_LOGIN);
    return Promise.resolve(null);
  }

  const form = document.createElement("form");
  form.id = "lg2fa";
  form.className = "lg-form";
  form.noValidate = true;
  form.innerHTML = `
    <h1>Verificação em duas etapas</h1>
    <p class="sub" id="lg2faAjuda" style="margin:0"></p>
    <label for="lg2faCodigo" id="lg2faRotulo"></label>
    <input id="lg2faCodigo" class="lg-codigo" name="codigo" autocomplete="one-time-code" required aria-describedby="lg2faAjuda">
    <button class="btn primary" type="submit" id="lg2faBotao">Verificar</button>
    <button class="lg-link" type="button" id="lg2faAlternar"></button>
    <button class="lg-link" type="button" id="lg2faVoltar">Voltar ao login</button>`;
  entrar.hidden = true;
  entrar.after(form);
  // Guarda o endereço de onde a pessoa veio (ex.: um link direto para /clientes/abc) para voltar a ele depois do código.
  const destino = /^\/(login|convite)(\/|$)/.test(location.pathname) ? "/" : location.pathname;
  history.pushState(null, "", ROTA_2FA);

  const campo = form.querySelector<HTMLInputElement>("#lg2faCodigo")!;
  const botao = form.querySelector<HTMLButtonElement>("#lg2faBotao")!;
  const alternar = form.querySelector<HTMLButtonElement>("#lg2faAlternar")!;
  let usandoBackup = false;

  const ajustarModo = (): void => {
    form.querySelector("#lg2faAjuda")!.textContent = usandoBackup
      ? "Digite um dos códigos de backup que você guardou. Cada código só vale uma vez."
      : "Digite o código de 6 dígitos do seu aplicativo autenticador.";
    form.querySelector("#lg2faRotulo")!.textContent = usandoBackup ? "Código de backup" : "Código do aplicativo";
    campo.inputMode = usandoBackup ? "text" : "numeric";
    campo.maxLength = usandoBackup ? 12 : 6;
    campo.placeholder = usandoBackup ? "" : "000000";
    campo.classList.toggle("lg-codigo-backup", usandoBackup);
    alternar.textContent = usandoBackup ? "Usar código do aplicativo" : "Usar código de backup";
    campo.value = "";
    campo.focus();
  };

  return new Promise((resolve) => {
    let encerrado = false;

    const encerrar = (resultado: Usuario | null, texto = "", erro = false): void => {
      if (encerrado) return;
      encerrado = true;
      window.removeEventListener("popstate", aoVoltar);
      tokenSegundoFator.limpar();
      form.remove();
      entrar.hidden = false;
      if (location.pathname === ROTA_2FA) history.replaceState(null, "", resultado ? destino : ROTA_LOGIN);
      aviso(texto, erro);
      if (!resultado) setTimeout(() => obrigatorio<HTMLInputElement>("#lgEmail").focus(), 50);
      resolve(resultado);
    };

    // Voltar do navegador já mudou a URL: só encerra o fluxo e descarta o token.
    function aoVoltar(): void {
      if (location.pathname !== ROTA_2FA) encerrar(null);
    }
    window.addEventListener("popstate", aoVoltar);

    form.querySelector("#lg2faVoltar")!.addEventListener("click", () => encerrar(null));
    alternar.addEventListener("click", () => {
      usandoBackup = !usandoBackup;
      aviso("");
      ajustarModo();
    });

    form.onsubmit = async (e) => {
      e.preventDefault();
      const codigo = campo.value.trim().replace(/\s/g, "");
      const token = tokenSegundoFator.obter();
      if (!token) return encerrar(null);
      if (codigo.length < 6) return aviso(usandoBackup ? "Digite o código de backup." : "Digite os 6 dígitos.", true);
      botao.disabled = true;
      form.setAttribute("aria-busy", "true");
      aviso("Verificando…");
      try {
        const r = await api.auth.totp.verificar({ token_temporario: token, codigo });
        sessaoToken.definir(r.access_token);
        encerrar(r.usuario);
      } catch (err) {
        if (err instanceof ErroApi && ENCERRAM_O_FLUXO.has(err.status)) return encerrar(null, err.message, true);
        aviso(err instanceof ErroApi ? err.message : "Código inválido. Tente de novo.", true);
        campo.value = "";
        campo.focus();
      } finally {
        botao.disabled = false;
        form.removeAttribute("aria-busy");
      }
    };

    ajustarModo();
  });
}
