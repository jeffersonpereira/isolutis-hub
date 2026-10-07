import { api } from "@/api/endpoints";
import { sessaoToken } from "@/api/http";
import { $ } from "@/core/dom";
import { html, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { cabecalhoDePagina, estadoDeErro } from "@/ui/componentes";
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
  return html`${cabecalhoDePagina({ titulo: "Dados da empresa", descricao: "Atualize o nome usado no Hub e nos registros da empresa." })}
    ${tela.erro ? estadoDeErro({ mensagem: tela.erro, acaoRepetir: "recarregarEmpresa" }) : ""}
    ${tela.empresa ? html`<section class="panel estreita"><div class="fields">
      <div class="field full"><label for="nomeEmpresa">Nome da empresa</label><input id="nomeEmpresa" maxlength="150" value="${tela.empresa.nome}" autocomplete="organization" required></div>
    </div><div class="tools fim"><button class="btn primary" data-act="salvarEmpresa">Salvar alterações</button></div></section>` : ""}`;
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

registrarAcao("recarregarEmpresa", async () => {
  await carregar();
  render();
});
