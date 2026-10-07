import { api } from "@/api/endpoints";
import { sessaoToken } from "@/api/http";
import { $ } from "@/core/dom";
import { html, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { toast } from "@/ui/toast";

type Empresa = { id: string; nome: string; papel: "admin" | "membro" };
const tela: { empresa: Empresa | null; erro: string } = { empresa: null, erro: "" };

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

function vista(): Safe {
  return html`<div class="head"><div><h1>Dados da empresa</h1><p>Atualize o nome usado no Hub e nos registros da empresa.</p></div></div>
    ${tela.erro ? html`<div class="banner" style="background:var(--bad-bg);color:var(--bad)">${tela.erro}</div>` : ""}
    ${tela.empresa ? html`<section class="panel" style="max-width:680px"><div class="fields">
      <div class="field full"><label for="nomeEmpresa">Nome da empresa</label><input id="nomeEmpresa" maxlength="150" value="${tela.empresa.nome}" autocomplete="organization" required></div>
    </div><div class="tools" style="justify-content:flex-end;margin-top:16px"><button class="btn primary" data-act="salvarEmpresa">Salvar alterações</button></div></section>` : ""}`;
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
