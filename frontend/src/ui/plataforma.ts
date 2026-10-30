/**
 * Área da plataforma (operador da AIME Tech): empresas, administrador inicial e membros.
 *
 * Fica fora do Hub: é uma página própria (`/plataforma`), sem empresa ativa, e só conversa com `/plataforma/*`, que
 * não devolve nenhum dado de negócio. O servidor confere o operador em cada chamada; esta tela só esconde o que a
 * pessoa não poderia usar.
 */
import { api } from "@/api/endpoints";
import type { ConvitePlataforma, EmpresaDetalhe, EmpresaPlataforma, MembroPlataforma, Papel } from "@/api/tipos";
import { compararTexto, quando, quandoCompleto } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { OPCOES_PAPEL, rotuloDoPapel } from "@/domain/papeis";
import { confirmar } from "@/ui/confirmar";
import { tentar } from "@/ui/erros";
import { toast } from "@/ui/toast";

export const ROTA_PLATAFORMA = "/plataforma";

const ID = "plataforma";

type Tela = { tipo: "lista" } | { tipo: "nova" } | { tipo: "detalhe"; id: string };

export interface OpcoesPlataforma {
  aoSair: () => void;
  /** Abre o Hub (escolha de empresa). */
  aoVoltarAoHub: () => void;
}

/** CNPJ com máscara só para exibir; devolve os dígitos como vieram quando não são 14. */
export function formatarCnpj(inscricao: string | null | undefined): string {
  const d = (inscricao ?? "").replace(/\D/g, "");
  if (d.length !== 14) return d;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

const pilulaStatus = (e: Pick<EmpresaPlataforma, "status">): Safe =>
  e.status === "ativa" ? html`<span class="pill ok">Ativa</span>` : html`<span class="pill warn">Suspensa</span>`;

const opcoesPapel = (atual: string): Safe =>
  html`${OPCOES_PAPEL.map(([valor, rotulo]) => html`<option value="${valor}"${valor === atual ? " selected" : ""}>${rotulo}</option>`)}`;

export function abrirAreaPlataforma(opcoes: OpcoesPlataforma): void {
  document.getElementById(ID)?.remove();
  const raiz = document.createElement("div");
  raiz.id = ID;
  raiz.className = "plat";
  document.body.append(raiz);
  document.title = "Plataforma · AIME Tech Hub";

  let tela: Tela = { tipo: "lista" };
  let busca = "";
  let empresas: EmpresaPlataforma[] | null = null;
  let detalhe: EmpresaDetalhe | null = null;
  let erro = "";

  const mensagemDe = (e: unknown): string => (e instanceof Error ? e.message : "Não foi possível carregar agora.");
  const idAberto = (): string => (tela.tipo === "detalhe" ? tela.id : "");

  async function abrirLista(): Promise<void> {
    tela = { tipo: "lista" };
    empresas = null;
    erro = "";
    desenhar();
    try {
      empresas = await api.plataforma.empresas(busca.trim() || undefined);
    } catch (e) {
      erro = mensagemDe(e);
    }
    desenhar();
  }

  async function abrirDetalhe(id: string): Promise<void> {
    tela = { tipo: "detalhe", id };
    erro = "";
    if (detalhe?.empresa.id !== id) detalhe = null;
    desenhar();
    try {
      detalhe = await api.plataforma.empresa(id);
    } catch (e) {
      erro = mensagemDe(e);
    }
    desenhar();
  }

  function cabecalho(): Safe {
    return html`<header class="plat-topo">
      <div><b>Plataforma</b><span>AIME Tech Hub</span></div>
      <div class="tools"><button class="btn" data-plat="hub">Voltar ao Hub</button><button class="btn" data-plat="sair">Sair</button></div>
    </header>`;
  }

  function vistaLista(): Safe {
    const linhas = (empresas ?? []).map(
      (e) => html`<tr tabindex="0" data-plat="abrir" data-id="${e.id}">
        <td><b>${e.nome}</b></td><td class="num">${formatarCnpj(e.inscricao) || "—"}</td><td>${pilulaStatus(e)}</td>
        <td class="num">${e.membros_ativos}</td><td class="sub">${quandoCompleto(e.criado_em)}</td></tr>`,
    );
    const corpo = erro
      ? html`<div class="banner" style="background:var(--bad-bg);color:var(--bad-texto)">${erro}</div>`
      : empresas === null
        ? html`<p class="sub">Carregando as empresas…</p>`
        : empresas.length === 0
          ? html`<p class="sub">${busca.trim() ? "Nenhuma empresa encontrada para esta busca." : "Nenhuma empresa cadastrada ainda."}</p>`
          : html`<div class="tbl-wrap"><table><thead><tr><th>Empresa</th><th>CNPJ</th><th>Status</th><th>Membros ativos</th><th>Criada em</th></tr></thead><tbody>${linhas}</tbody></table></div>`;
    return html`<div class="head"><div><h1>Empresas</h1><p>Clientes da plataforma. Aqui você cria empresas e cuida de quem tem acesso; os dados de negócio de cada empresa não aparecem.</p></div>
      <div class="tools"><button class="btn primary" data-plat="nova">Nova empresa</button></div></div>
      <form class="plat-busca" data-plat-form="busca" role="search"><input name="busca" type="search" value="${busca}" placeholder="Buscar por nome ou CNPJ" aria-label="Buscar empresa"><button class="btn" type="submit">Buscar</button></form>
      ${corpo}`;
  }

  function vistaNova(): Safe {
    return html`<div class="head"><div><h1>Nova empresa</h1><p>O administrador inicial recebe um convite por e-mail e define a própria senha.</p></div>
      <div class="tools"><button class="btn" data-plat="lista">Cancelar</button></div></div>
      <form class="plat-form" data-plat-form="nova">
        <div class="field"><label for="p-nome">Nome da empresa</label><input id="p-nome" name="nome" maxlength="150" required></div>
        <div class="field"><label for="p-cnpj">CNPJ <span class="sub">(opcional)</span></label><input id="p-cnpj" name="inscricao" inputmode="numeric" maxlength="18" placeholder="00.000.000/0000-00"></div>
        <div class="field"><label for="p-adm-nome">Nome do administrador</label><input id="p-adm-nome" name="admin_nome" maxlength="200" required></div>
        <div class="field"><label for="p-adm-email">E-mail do administrador</label><input id="p-adm-email" name="admin_email" type="email" required></div>
        <div><button class="btn primary" type="submit">Criar empresa e enviar convite</button></div>
      </form>`;
  }

  function linhaMembro(m: MembroPlataforma): Safe {
    const papel = html`<select data-plat-papel data-usuario="${m.usuario_id}" aria-label="Papel de ${m.nome}"${m.ativo ? "" : " disabled"}>${opcoesPapel(m.papel)}</select>`;
    const acao = m.ativo
      ? html`<button class="btn danger" data-plat="desativar" data-usuario="${m.usuario_id}">Desativar</button>`
      : html`<button class="btn" data-plat="reativar" data-usuario="${m.usuario_id}">Reativar</button>`;
    return html`<tr><td><b>${m.nome}</b></td><td class="num">${m.email}</td><td>${papel}</td>
      <td>${m.ativo ? html`<span class="pill ok">Ativo</span>` : html`<span class="pill">Desativado</span>`}${m.usuario_ativo ? "" : html` <span class="pill bad">Conta desativada</span>`}</td>
      <td class="sub">${quandoCompleto(m.ultimo_acesso)}</td><td>${acao}</td></tr>`;
  }

  function linhaConvite(c: ConvitePlataforma): Safe {
    return html`<tr><td class="num">${c.email}</td><td><span class="pill">${rotuloDoPapel(c.papel)}</span></td>
      <td class="sub">${quando(c.criado_em)}</td><td class="sub">${quando(c.expira_em)}</td>
      <td><button class="btn" data-plat="reenviar" data-convite="${c.id}">Reenviar</button> <button class="btn" data-plat="cancelar-convite" data-convite="${c.id}">Cancelar</button></td></tr>`;
  }

  function vistaDetalhe(): Safe {
    if (erro) return html`<button class="btn" data-plat="lista">← Empresas</button><div class="banner" style="margin-top:12px;background:var(--bad-bg);color:var(--bad-texto)">${erro}</div>`;
    if (!detalhe) return html`<button class="btn" data-plat="lista">← Empresas</button><p class="sub">Carregando a empresa…</p>`;
    const { empresa, membros, convites } = detalhe;
    const suspensa = empresa.status === "suspensa";
    const ordenados = [...membros].sort((a, b) => Number(b.ativo) - Number(a.ativo) || compararTexto(a.nome, b.nome));
    return html`<button class="btn" data-plat="lista">← Empresas</button>
      <div class="head" style="margin-top:12px"><div><h1>${empresa.nome} ${pilulaStatus(empresa)}</h1><p>${formatarCnpj(empresa.inscricao) || "Sem CNPJ informado"} · ${empresa.membros_ativos} membro(s) ativo(s)</p></div>
        <div class="tools">${suspensa ? html`<button class="btn primary" data-plat="reativar-empresa">Reativar empresa</button>` : html`<button class="btn danger" data-plat="suspender-empresa">Suspender empresa</button>`}</div></div>
      ${suspensa ? html`<div class="banner" style="background:var(--warn-bg);color:var(--warn-texto)">Empresa suspensa: os membros não conseguem entrar. Os dados foram preservados.</div>` : ""}
      <section><h2>Membros</h2>
        <div class="tbl-wrap"><table><thead><tr><th>Nome</th><th>E-mail</th><th>Papel</th><th>Acesso</th><th>Último acesso</th><th></th></tr></thead><tbody>${ordenados.map(linhaMembro)}</tbody></table></div></section>
      ${convites.length > 0 ? html`<section><h2>Convites pendentes</h2><div class="tbl-wrap"><table><thead><tr><th>E-mail</th><th>Papel</th><th>Enviado em</th><th>Expira em</th><th></th></tr></thead><tbody>${convites.map(linhaConvite)}</tbody></table></div></section>` : ""}
      <section><h2>Adicionar membro</h2><p class="sub">E-mail de uma conta já existente entra direto, sem convite. E-mail novo recebe um convite por e-mail para definir a senha.</p>
        <form class="plat-form plat-form-linha" data-plat-form="convidar">
          <div class="field"><label for="c-nome">Nome</label><input id="c-nome" name="nome" maxlength="200" required></div>
          <div class="field"><label for="c-email">E-mail</label><input id="c-email" name="email" type="email" required></div>
          <div class="field"><label for="c-papel">Papel</label><select id="c-papel" name="papel">${opcoesPapel("membro")}</select></div>
          <div><button class="btn primary" type="submit">Adicionar</button></div>
        </form></section>`;
  }

  function desenhar(): void {
    const corpo = tela.tipo === "lista" ? vistaLista() : tela.tipo === "nova" ? vistaNova() : vistaDetalhe();
    const foco = document.activeElement instanceof HTMLElement ? document.activeElement.getAttribute("name") : null;
    raiz.innerHTML = String(html`${cabecalho()}<main class="plat-corpo">${corpo}</main>`);
    if (foco === "busca") raiz.querySelector<HTMLInputElement>('input[name="busca"]')?.focus();
  }

  async function mudarStatus(id: string, status: "ativa" | "suspensa"): Promise<void> {
    if (status === "suspensa") {
      const nome = detalhe?.empresa.nome ?? "a empresa";
      const ok = await confirmar({
        titulo: "Suspender empresa?",
        texto: `Ninguém de ${nome} conseguirá entrar até você reativar. Os dados ficam preservados.`,
        confirmar: "Suspender",
        cancelar: "Cancelar",
      });
      if (!ok) return;
    }
    if ((await tentar(() => api.plataforma.definirStatus(id, status))) === null) return;
    toast(status === "suspensa" ? "Empresa suspensa" : "Empresa reativada");
    await abrirDetalhe(id);
  }

  async function alterarMembro(id: string, usuarioId: string, papel: Papel, ativo: boolean, mensagem: string): Promise<void> {
    if ((await tentar(() => api.plataforma.definirMembro(id, usuarioId, { papel, ativo }))) !== null) toast(mensagem);
    await abrirDetalhe(id); // recarrega também na recusa, o que desfaz a mudança visual do select
  }

  async function aoClicar(alvo: HTMLElement): Promise<void> {
    const id = idAberto();
    const membro = detalhe?.membros.find((m) => m.usuario_id === alvo.dataset.usuario);
    switch (alvo.dataset.plat) {
      case "sair":
        return opcoes.aoSair();
      case "hub":
        return opcoes.aoVoltarAoHub();
      case "lista":
        return void abrirLista();
      case "nova":
        tela = { tipo: "nova" };
        return desenhar();
      case "abrir":
        return void abrirDetalhe(alvo.dataset.id ?? "");
      case "suspender-empresa":
        return void mudarStatus(id, "suspensa");
      case "reativar-empresa":
        return void mudarStatus(id, "ativa");
      case "desativar": {
        if (!membro) return;
        const ok = await confirmar({
          titulo: "Desativar membro?",
          texto: `${membro.nome} perde o acesso a ${detalhe?.empresa.nome ?? "esta empresa"} na próxima requisição.`,
          confirmar: "Desativar",
          cancelar: "Cancelar",
        });
        if (ok) await alterarMembro(id, membro.usuario_id, membro.papel, false, "Membro desativado");
        return;
      }
      case "reativar":
        if (membro) await alterarMembro(id, membro.usuario_id, membro.papel, true, "Membro reativado");
        return;
      case "reenviar": {
        const c = detalhe?.convites.find((x) => x.id === Number(alvo.dataset.convite));
        if (!c) return;
        const nome = c.email.split("@")[0] ?? c.email;
        const resultado = await tentar(() => api.plataforma.convidar(id, { nome, email: c.email, papel: c.papel }));
        if (resultado) toast(resultado.direto ? `${c.email} já tinha conta: acesso liberado na hora, sem convite` : `Convite reenviado para ${c.email}`);
        return void abrirDetalhe(id);
      }
      case "cancelar-convite":
        if ((await tentar(() => api.plataforma.cancelarConvite(id, Number(alvo.dataset.convite)))) !== null) toast("Convite cancelado");
        return void abrirDetalhe(id);
    }
  }

  async function aoEnviar(form: HTMLFormElement): Promise<void> {
    const dados = Object.fromEntries(new FormData(form).entries()) as Record<string, string>;
    const campo = (n: string): string => (dados[n] ?? "").trim();
    switch (form.dataset.platForm) {
      case "busca":
        busca = campo("busca");
        return void abrirLista();
      case "nova": {
        const email = campo("admin_email").toLowerCase();
        const criada = await tentar(() =>
          api.plataforma.criarEmpresa({ nome: campo("nome"), inscricao: campo("inscricao") || null, admin_nome: campo("admin_nome"), admin_email: email }),
        );
        if (!criada) return;
        toast(`Empresa criada. Convite enviado para ${email}`);
        return void abrirDetalhe(criada.id);
      }
      case "convidar": {
        const id = idAberto();
        const email = campo("email").toLowerCase();
        const resultado = await tentar(() => api.plataforma.convidar(id, { nome: campo("nome"), email, papel: campo("papel") as Papel }));
        if (!resultado) return;
        toast(resultado.direto ? `${email} já tinha conta: acesso liberado na hora, sem convite` : `Convite enviado para ${email}`);
        return void abrirDetalhe(id);
      }
    }
  }

  raiz.addEventListener("click", (e) => {
    const alvo = (e.target as HTMLElement).closest<HTMLElement>("[data-plat]");
    if (alvo) void aoClicar(alvo);
  });
  raiz.addEventListener("keydown", (e) => {
    const linha = (e.target as HTMLElement).closest<HTMLElement>('tr[data-plat="abrir"]');
    if (linha && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      void abrirDetalhe(linha.dataset.id ?? "");
    }
  });
  raiz.addEventListener("submit", (e) => {
    const form = (e.target as HTMLElement).closest<HTMLFormElement>("form[data-plat-form]");
    if (!form) return;
    e.preventDefault();
    void aoEnviar(form);
  });
  raiz.addEventListener("change", (e) => {
    const campo = e.target as HTMLSelectElement;
    if (!campo.matches("select[data-plat-papel]")) return;
    const membro = detalhe?.membros.find((m) => m.usuario_id === campo.dataset.usuario);
    if (membro) void alterarMembro(idAberto(), membro.usuario_id, campo.value as Papel, membro.ativo, "Papel atualizado");
  });

  void abrirLista();
}
