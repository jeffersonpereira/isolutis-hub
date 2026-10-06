/**
 * Tela pública de aceitação de convite.
 * Exibida quando a URL é /convite/:token — substitui toda a interface do Hub.
 */
import { api } from "@/api/endpoints";
import { ErroApi, sessaoToken } from "@/api/http";
import type { ConviteInfo } from "@/api/tipos";

function montarTela(): HTMLElement {
  const raiz = document.createElement("div");
  raiz.className = "login";
  raiz.innerHTML = `
    <div class="lg-box">
      <div class="lg-topo">
        <img src="/logo-horizontal.png" alt="iSolutis" width="200" height="77">
        <span>Hub Comercial</span>
      </div>
      <div id="cvConteudo"></div>
      <p class="lg-msg" id="cvMsg" role="status"></p>
    </div>`;
  document.body.appendChild(raiz);
  return raiz;
}

function mensagem(texto: string, erro = false): void {
  const m = document.getElementById("cvMsg");
  if (!m) return;
  m.textContent = texto;
  m.classList.toggle("erro", erro);
}

function renderValido(info: ConviteInfo, token: string): void {
  const el = document.getElementById("cvConteudo");
  if (!el) return;

  const papel = info.papel === "admin" ? "Administrador" : "Membro";
  el.innerHTML = `
    <form id="cvForm" class="lg-form" novalidate>
      <h1>Aceitar convite</h1>
      <p class="sub" style="margin:0 0 4px">
        <b>${info.criado_por_nome}</b> convidou você para entrar em
        <b>${info.empresa_nome}</b> como <b>${papel}</b>.
      </p>
      <p class="sub" style="margin:0 0 8px;font-size:12px">E-mail: ${info.email}</p>
      <label for="cvSenha">Defina uma senha</label>
      <input id="cvSenha" name="senha" type="password" autocomplete="new-password" minlength="8" placeholder="Mínimo de 8 caracteres" required>
      <label for="cvConfirmar">Confirme a senha</label>
      <input id="cvConfirmar" name="confirmar_senha" type="password" autocomplete="new-password" minlength="8" placeholder="Repita a senha" required>
      <button class="btn primary" type="submit" id="cvBotao">Entrar no Hub</button>
    </form>`;

  const form = document.getElementById("cvForm") as HTMLFormElement | null;
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const senha = (document.getElementById("cvSenha") as HTMLInputElement).value;
    const confirmar = (document.getElementById("cvConfirmar") as HTMLInputElement).value;
    const botao = document.getElementById("cvBotao") as HTMLButtonElement;

    if (senha.length < 8) return mensagem("A senha precisa ter pelo menos 8 caracteres.", true);
    if (senha !== confirmar) return mensagem("As senhas não são iguais.", true);

    botao.disabled = true;
    mensagem("Entrando…");

    try {
      const r = await api.convites.aceitar(token, { senha, confirmar_senha: confirmar });
      sessaoToken.definir(r.access_token);
      mensagem("Pronto! Redirecionando…");
      setTimeout(() => {
        location.replace("/");
      }, 800);
    } catch (err) {
      mensagem(err instanceof ErroApi ? err.message : "Não foi possível aceitar o convite agora.", true);
      botao.disabled = false;
    }
  });
}

function renderExpirado(): void {
  const el = document.getElementById("cvConteudo");
  if (!el) return;
  el.innerHTML = `
    <div class="lg-form">
      <h1>Convite expirado</h1>
      <p>Este convite expirou. Peça ao administrador que envie um novo convite.</p>
      <a href="/" class="btn" style="text-align:center;text-decoration:none;display:block">Voltar ao Hub</a>
    </div>`;
}

function renderUsado(): void {
  const el = document.getElementById("cvConteudo");
  if (!el) return;
  el.innerHTML = `
    <div class="lg-form">
      <h1>Convite já utilizado</h1>
      <p>Este convite já foi utilizado. Faça login normalmente.</p>
      <a href="/" class="btn primary" style="text-align:center;text-decoration:none;display:block">Ir para o login</a>
    </div>`;
}

function renderErro(): void {
  const el = document.getElementById("cvConteudo");
  if (!el) return;
  el.innerHTML = `
    <div class="lg-form">
      <h1>Convite inválido</h1>
      <p>Este convite não foi encontrado ou não é mais válido.</p>
      <a href="/" class="btn" style="text-align:center;text-decoration:none;display:block">Voltar ao Hub</a>
    </div>`;
}

/**
 * Detecta se a URL atual é uma rota de convite.
 * Retorna o token se for, ou null caso contrário.
 */
export function detectarRotaConvite(): string | null {
  const m = location.pathname.match(/^\/convite\/([^/]+)\/?$/);
  return m ? (m[1] ?? null) : null;
}

/**
 * Inicia a tela de aceitação de convite. Substitui toda a interface do Hub.
 * Deve ser chamada antes de montar o app principal.
 */
export async function iniciarTelaConvite(token: string): Promise<void> {
  // Esconde o app principal enquanto a tela de convite é exibida
  const appEl = document.querySelector(".app") as HTMLElement | null;
  if (appEl) appEl.hidden = true;

  montarTela();
  mensagem("Carregando convite…");

  let info: ConviteInfo;
  try {
    info = await api.convites.verificar(token);
  } catch {
    renderErro();
    mensagem("");
    return;
  }

  mensagem("");

  switch (info.estado) {
    case "valido":
      renderValido(info, token);
      break;
    case "expirado":
      renderExpirado();
      break;
    case "usado":
      renderUsado();
      break;
    default:
      renderErro();
  }
}
