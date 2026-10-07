import { api } from "@/api/endpoints";
import { sessaoToken } from "@/api/http";
import { $ } from "@/core/dom";
import { html, raw, type Safe } from "@/core/html";
import { eu } from "@/state/estado";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { fluxoAtivar2FA, fluxoDesativar2FA } from "@/ui/login";
import { toast } from "@/ui/toast";

type Empresa = { id: string; nome: string; papel: "admin" | "membro" };
const tela: {
  empresa: Empresa | null;
  erro: string;
  totp2fa: boolean | null; // null = não carregado
} = { empresa: null, erro: "", totp2fa: null };

async function carregar(): Promise<void> {
  try {
    const empresas = await api.empresas.listar();
    tela.empresa = empresas.find((empresa) => empresa.id === sessaoToken.empresa()) ?? null;
    tela.erro = tela.empresa ? "" : "Não foi possível localizar a empresa ativa.";
  } catch (e) {
    tela.empresa = null;
    tela.erro = e instanceof Error ? e.message : "Não foi possível carregar os dados da empresa.";
  }
}

function vistaSecurity(): Safe {
  const ativo = tela.totp2fa;
  if (ativo === null) {
    // Ainda não carregamos o status — botão para verificar
    return html`
      <section class="panel" style="max-width:680px;margin-top:16px">
        <h2 style="font-size:1rem;margin:0 0 12px">Segurança</h2>
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
          <span>Autenticação em dois fatores: <b>—</b></span>
          <button class="btn" data-act="verificarStatus2fa">Verificar status</button>
        </div>
      </section>`;
  }
  return html`
    <section class="panel" style="max-width:680px;margin-top:16px">
      <h2 style="font-size:1rem;margin:0 0 12px">Segurança</h2>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <span>Autenticação em dois fatores:
          ${ativo
            ? raw(`<span class="pill ok">Ativado ✓</span>`)
            : raw(`<span class="pill">Desativado</span>`)}
        </span>
        ${ativo
          ? html`<button class="btn danger" data-act="desativar2fa">Desativar 2FA</button>`
          : html`<button class="btn primary" data-act="ativar2fa">Ativar 2FA</button>`}
      </div>
      <div id="container2fa" style="margin-top:16px"></div>
    </section>`;
}

function vista(): Safe {
  return html`<div class="head"><div><h1>Dados da empresa</h1><p>Atualize o nome usado no Hub e nos registros da empresa.</p></div></div>
    ${tela.erro ? html`<div class="banner" style="background:var(--bad-bg);color:var(--bad)">${tela.erro}</div>` : ""}
    ${tela.empresa ? html`<section class="panel" style="max-width:680px"><div class="fields">
      <div class="field full"><label for="nomeEmpresa">Nome da empresa</label><input id="nomeEmpresa" maxlength="150" value="${tela.empresa.nome}" autocomplete="organization" required></div>
    </div><div class="tools" style="justify-content:flex-end;margin-top:16px"><button class="btn primary" data-act="salvarEmpresa">Salvar alterações</button></div></section>` : ""}
    ${eu.id ? vistaSecurity() : ""}`;
}

registrarVista({ id: "empresa", nome: "Dados da empresa", grupo: "Administração", somenteAdmin: true, carregar, depende: ["empresa"], desenhar: vista });

registrarAcao("salvarEmpresa", async () => {
  const empresa = tela.empresa;
  const input = $("#nomeEmpresa") as HTMLInputElement | null;
  const nome = input?.value.trim() ?? "";
  if (!empresa) return;
  if (!nome) return void toast("Informe o nome da empresa.");
  try {
    await api.empresas.atualizar(nome);
    tela.empresa = { ...empresa, nome };
    toast("Dados da empresa atualizados.");
    render();
  } catch {
    toast("Não foi possível salvar.");
  }
});

registrarAcao("verificarStatus2fa", async () => {
  try {
    const me = await api.auth.eu();
    tela.totp2fa = me.totp_ativo;
  } catch {
    tela.totp2fa = false;
  }
  render();
});

registrarAcao("ativar2fa", async () => {
  const container = document.getElementById("container2fa");
  if (!container) return;
  const ativado = await fluxoAtivar2FA(container);
  if (ativado) {
    tela.totp2fa = true;
    render();
    toast("2FA ativado com sucesso.");
  }
});

registrarAcao("desativar2fa", async () => {
  const container = document.getElementById("container2fa");
  if (!container) return;
  const desativado = await fluxoDesativar2FA(container);
  if (desativado) {
    tela.totp2fa = false;
    render();
    toast("2FA desativado.");
  }
});
