import { api } from "@/api/endpoints";
import type { Convite, Usuario } from "@/api/tipos";
import { $ } from "@/core/dom";
import { compararTexto, primeiroNome, quando, quandoCompleto } from "@/core/formato";
import { html, raw, type Safe } from "@/core/html";
import { eu } from "@/state/estado";
import { recarregar, registrarVista } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { espaco } from "@/ui/formularios";
import { excluir } from "@/ui/gravacao";
import { toast } from "@/ui/toast";

const pagina: { lista: Usuario[] | null; convites: Convite[] | null; erro: string } = {
  lista: null,
  convites: null,
  erro: "",
};

registrarConsulta("equipe", (id) => pagina.lista?.find((u) => u.id === id) && { id, versao: pagina.lista.find((u) => u.id === id)!.versao, atualizado_por: null });

async function carregar(): Promise<void> {
  try {
    [pagina.lista, pagina.convites] = await Promise.all([api.usuarios.listar(), api.convites.listar().catch(() => [])]);
    pagina.erro = "";
  } catch (e) {
    pagina.erro = e instanceof Error ? e.message : "Não foi possível carregar a equipe.";
  }
}

function vistaConvitesPendentes(): Safe {
  const convites = pagina.convites;
  if (!convites || convites.length === 0) return html``;
  return html`<section style="margin-top:32px">
    <h2 style="font-size:1rem;margin-bottom:12px">Convites pendentes</h2>
    <div class="tbl-wrap"><table><thead><tr><th>E-mail</th><th>Papel</th><th>Enviado em</th><th>Expira em</th><th></th></tr></thead><tbody>
      ${convites.map(
        (c) => html`<tr>
          <td class="num">${c.email}</td>
          <td>${c.papel === "admin" ? html`<span class="pill info">Administrador</span>` : html`<span class="pill">Membro</span>`}</td>
          <td class="sub">${quando(c.criado_em)}</td>
          <td class="sub">${quando(c.expira_em)}</td>
          <td><button class="btn" data-act="cancelarConvite" data-valor="${c.id}">Cancelar</button></td>
        </tr>`,
      )}
    </tbody></table></div>
  </section>`;
}

function vista(): Safe {
  const cabecalho = html`<div class="head"><div><h1>Equipe</h1><p>Quem pode entrar no Hub. Aqui você convida pessoas, define e troca senhas e escolhe quem é administrador.</p></div>
    <div class="tools"><button class="btn" data-act="recarregarEquipe">Atualizar</button><button class="btn" data-act="novoUsuario">Novo usuário</button><button class="btn primary" data-act="convidarMembro">Convidar membro</button></div></div>`;
  if (pagina.erro) return html`${cabecalho}<div class="banner" style="background:var(--bad-bg);color:var(--bad-texto)">${pagina.erro}</div>`;
  if (!pagina.lista) return html`${cabecalho}<p class="sub">Carregando a equipe…</p>`;
  const lista = [...pagina.lista].sort((a, b) => Number(b.ativo) - Number(a.ativo) || Number(b.admin) - Number(a.admin) || compararTexto(a.nome, b.nome));
  return html`${cabecalho}<div class="tbl-wrap"><table><thead><tr><th>Nome</th><th>E-mail</th><th>Acesso</th><th>Login</th><th>Último acesso</th></tr></thead><tbody>
    ${lista.map(
      (u) => html`<tr tabindex="0" data-open="usuario:${u.id}"><td><b>${u.nome}</b>${u.id === eu.id ? html` <span class="pill teal-mid">você</span>` : ""}</td><td class="num">${u.email}</td>
      <td>${!u.ativo ? html`<span class="pill">Removido</span>` : u.admin ? html`<span class="pill info">Administrador</span>` : html`<span class="pill">Membro</span>`}</td>
      <td>${u.senha_definida ? html`<span class="pill ok">Ativo</span>` : html`<span class="pill warn">Sem senha</span>`}</td><td class="sub">${quandoCompleto(u.ultimo_acesso)}</td></tr>`,
    )}
  </tbody></table></div>${vistaConvitesPendentes()}`;
}

registrarVista({ id: "equipe", nome: "Equipe", somenteAdmin: true, carregar, depende: ["equipe"], desenhar: vista });

const SENHA_CARACTERES = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
export function senhaAleatoria(tamanho = 12): string {
  const a = new Uint32Array(tamanho);
  crypto.getRandomValues(a);
  return [...a].map((n) => SENHA_CARACTERES[n % SENHA_CARACTERES.length]).join("");
}

function formUsuario(u?: Usuario): void {
  const novo = !u;
  const souEu = u?.id === eu.id;
  abrirGaveta({
    titulo: u ? u.nome : "Novo usuário",
    corpo: html`<div class="fields">
      ${campo("Nome", inp("nome", u?.nome, 'placeholder="Como aparece no Hub"'))}
      ${campo("E-mail", inp("email", u?.email, novo ? 'type="email" placeholder="email@empresa.com.br"' : 'type="email" readonly'))}
      <div class="field full"><label for="f-senha">${novo ? "Senha" : "Nova senha"}</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap"><input name="senha" id="f-senha" type="text" autocomplete="off" style="flex:1 1 180px" placeholder="${novo ? "Mínimo de 8 caracteres" : "Deixe em branco para não trocar"}"><button class="btn" type="button" id="gerarSenha">Gerar senha</button></div>
        <span class="sub">${novo ? 'A pessoa entra com este e-mail e esta senha. Ela pode trocar depois, em "Trocar senha".' : "A senha atual deixa de valer assim que você salvar. Avise a pessoa."}</span></div>
      <label class="check full"><input type="checkbox" name="admin" id="f-admin"${raw(u?.admin ? " checked" : "")}${raw(souEu ? " disabled" : "")}> Administrador (pode gerenciar a equipe)</label>
      ${u && !u.ativo ? html`<label class="check full"><input type="checkbox" name="ativo" id="f-ativo"> Reativar acesso desta pessoa</label>` : ""}
    </div>
    <div class="banner" id="senhaFeita" hidden style="background:var(--ok-bg);color:var(--ok-texto)"></div>`,
    rodape: html`<button class="btn primary" data-salvar>${novo ? "Criar usuário" : "Salvar"}</button>${espaco}${u && !souEu && u.ativo ? html`<button class="btn danger" data-excluir>Remover da equipe</button>` : ""}`,
    montar: (f, fechar, L) => {
      $("#gerarSenha", L)?.addEventListener("click", () => {
        (f.elements.namedItem("senha") as HTMLInputElement).value = senhaAleatoria();
      });
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;
        const nome = fv(f, "nome");
        const email = fv(f, "email").toLowerCase();
        const senha = fv(f, "senha");
        if (!nome) return void toast("Informe o nome.");
        if (novo && !email) return void toast("Informe o e-mail.");
        if (novo && !senha) return void toast('Defina uma senha ou clique em "Gerar senha".');
        if (senha && senha.length < 8) return void toast("A senha precisa ter pelo menos 8 caracteres.");
        botao.disabled = true;
        const admin = souEu ? true : (f.elements.namedItem("admin") as HTMLInputElement).checked;
        const ok = await tentar(() =>
          u
            ? api.usuarios.atualizar(u.id, { nome, admin, ativo: u.ativo || !!(f.elements.namedItem("ativo") as HTMLInputElement | null)?.checked, senha: senha || null, versao: u.versao })
            : api.usuarios.criar({ nome, email, senha, admin }),
        );
        if (!ok) {
          botao.disabled = false;
          return;
        }
        await recarregar("equipe");
        if (senha) {
          const caixa = $("#senhaFeita", L)!;
          caixa.hidden = false;
          const endereco = location.origin;
          caixa.innerHTML = `<b>${novo ? "Usuário criado." : "Senha alterada."}</b> Envie para <span id="nomeSenha"></span>: endereço <b id="endSenha"></b>, e-mail <b id="emailSenha"></b> e senha <b class="num" id="valSenha"></b>. <button class="btn" type="button" id="copiarAcesso" style="margin-left:6px">Copiar</button>`;
          $("#nomeSenha", L)!.textContent = primeiroNome(nome);
          $("#endSenha", L)!.textContent = endereco;
          $("#emailSenha", L)!.textContent = ok.email;
          $("#valSenha", L)!.textContent = senha;
          $("#copiarAcesso", L)?.addEventListener("click", async () => {
            const texto = `Hub Comercial iSolutis\nEndereço: ${endereco}\nE-mail: ${ok.email}\nSenha: ${senha}\nVocê pode trocar a senha depois, em "Trocar senha".`;
            try {
              await navigator.clipboard.writeText(texto);
              toast("Copiado");
            } catch {
              toast("Não foi possível copiar. Selecione o texto e copie.");
            }
          });
          botao.textContent = "Salvo";
          return;
        }
        toast("Salvo");
        fechar();
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (u) void excluir({ recarregar: ["equipe"], mensagem: `${u.nome} removido da equipe`, fechar, operacao: () => api.usuarios.remover(u.id) });
      });
    },
  });
}

function formConvite(): void {
  abrirGaveta({
    titulo: "Convidar membro",
    corpo: html`<div class="fields">
      ${campo("Nome", inp("nome", "", 'placeholder="Como aparece no Hub"'))}
      ${campo("E-mail", inp("email", "", 'type="email" placeholder="email@empresa.com.br"'))}
      ${campo("Papel", sel("papel", [["membro", "Membro"], ["admin", "Administrador"]], "membro"))}
    </div>`,
    rodape: html`<button class="btn primary" data-salvar>Enviar convite</button>`,
    montar: (f, fechar, L) => {
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;
        const nome = fv(f, "nome");
        const email = fv(f, "email").toLowerCase();
        const papel = fv(f, "papel") as "admin" | "membro";
        if (!nome) return void toast("Informe o nome do convidado.");
        if (!email) return void toast("Informe o e-mail do convidado.");
        botao.disabled = true;
        const ok = await tentar(() => api.convites.criar({ nome, email, papel }));
        if (!ok) {
          botao.disabled = false;
          return;
        }
        toast(`Convite enviado para ${email}`);
        await recarregar("equipe");
        fechar();
      });
    },
  });
}

registrarAcao("novoUsuario", () => formUsuario());
registrarAcao("convidarMembro", () => formConvite());
registrarAcao("recarregarEquipe", async () => {
  await recarregar("equipe");
});
registrarAcao("cancelarConvite", async (alvo) => {
  const id = Number(alvo.dataset.valor);
  if (!id) return;
  const ok = await tentar(() => api.convites.cancelar(id));
  if (ok !== null) {
    toast("Convite cancelado.");
    await recarregar("equipe");
  }
});
registrarAbertura("usuario", (id) => {
  const u = pagina.lista?.find((x) => x.id === id);
  if (u) formUsuario(u);
});
