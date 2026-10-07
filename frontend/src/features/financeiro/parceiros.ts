import { $ } from "@/core/dom";
import { html, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { ui } from "@/state/estado";
import { registrarAcao } from "@/ui/acoes";
import { abrirGaveta } from "@/ui/gaveta";
import { espaco } from "@/ui/formularios";
import { gravar } from "@/ui/gravacao";
import { camposDoParceiro, ligarCamposDoParceiro, lerCamposDoParceiro } from "../parceiros/campos";
import { apiFinanceiro, type Papel, type Parceiro } from "./api";
import { acoesDaLinha, confirmarExclusao, formatarCep, formatarDocumento, GRUPO } from "./comum";

const tela: { parceiros: Parceiro[] | null; papeis: Papel[]; filtro: string } = { parceiros: null, papeis: [], filtro: "" };

async function carregar(): Promise<void> {
  const [parceiros, papeis] = await Promise.all([apiFinanceiro.parceiros.listar(), apiFinanceiro.parceiros.papeis()]);
  tela.parceiros = parceiros;
  tela.papeis = papeis;
}

const nomeDoPapel = (codigo: string): string => tela.papeis.find((p) => p.codigo === codigo)?.nome ?? codigo;

function vista(): Safe {
  if (!tela.parceiros) return html`<div class="head"><div><h1>Parceiros de negócio</h1></div></div><p class="sub">Carregando…</p>`;
  const q = ui.buscaFin.toLowerCase();
  const digitos = q.replace(/\D/g, "");
  const lista = tela.parceiros.filter((p) => (!tela.filtro || p.papeis.includes(tela.filtro)) && (!q || p.nome.toLowerCase().includes(q) || (digitos && (p.cpf_cnpj ?? "").includes(digitos))));
  return html`<div class="head"><div><h1>Parceiros de negócio</h1><p>Cadastro único de pessoas e empresas: cada uma pode ser cliente, fornecedor, funcionário…</p></div>
    <div class="tools"><div class="seg" role="group">${[["", "Todos"] as const, ...tela.papeis.map((p) => [p.codigo, p.nome] as const)].map(([k, r]) => html`<button data-act="filtroPapel" data-valor="${k}" aria-pressed="${tela.filtro === k}">${r}</button>`)}</div>
    <input class="search" data-busca="buscaFin" type="search" placeholder="Buscar por nome ou CPF/CNPJ" value="${ui.buscaFin}"><button class="btn primary" data-act="novoParceiro">Novo parceiro</button></div></div>
  ${
    tela.parceiros.length
      ? html`<div class="tbl-wrap"><table><thead><tr><th>Nome</th><th>Papéis</th><th>Documento</th><th>Município</th><th>Endereço</th><th></th></tr></thead><tbody>
      ${lista.map((p) => html`<tr><td><b>${p.nome}</b><div class="sub">${p.tipo_pessoa === "PJ" ? "Pessoa jurídica" : "Pessoa física"}</div></td><td>${p.papeis.map((c) => html`<span class="pill">${nomeDoPapel(c)}</span> `)}</td><td class="num">${formatarDocumento(p.cpf_cnpj)}</td><td>${p.municipio_nome ? `${p.municipio_nome}/${p.uf}` : "—"}</td><td>${p.endereco ?? "—"}${p.cep ? html`<div class="sub num">${formatarCep(p.cep)}</div>` : ""}</td><td class="r">${acoesDaLinha("parceiro", p.id)}</td></tr>`)}
      ${!lista.length ? html`<tr><td colspan="6" class="sub">Nenhum parceiro encontrado.</td></tr>` : ""}
    </tbody></table></div>`
      : html`<div class="empty"><b>Nenhum parceiro cadastrado</b>Cadastre quem paga e quem recebe da empresa para lançar títulos financeiros.<br><button class="btn primary" data-act="novoParceiro">Cadastrar o primeiro parceiro</button></div>`
  }`;
}

registrarVista({ id: "fin-parceiros", nome: "Fornecedores", grupo: GRUPO, permissao: "financeiro", carregar, depende: ["financeiro", "clientes"], desenhar: vista });

function formParceiro(p?: Parceiro): void {
  abrirGaveta({
    titulo: p ? p.nome : "Novo parceiro",
    corpo: camposDoParceiro(p ?? {}, tela.papeis),
    rodape: html`<button class="btn primary" data-salvar>Salvar</button>${espaco}`,
    montar: (f, fechar, L) => {
      ligarCamposDoParceiro(f, p ?? {});
      $("[data-salvar]", L)?.addEventListener("click", async () => {
        const corpo = lerCamposDoParceiro(f);
        if (!corpo) return;
        await gravar({
          recarregar: ["financeiro", "clientes"], mensagem: "Parceiro salvo", fechar,
          operacao: () => (p ? apiFinanceiro.parceiros.atualizar(p.id, { ...corpo, versao: p.versao }) : apiFinanceiro.parceiros.criar(corpo)),
        });
      });
    },
  });
}

const porId = (id?: string): Parceiro | undefined => tela.parceiros?.find((p) => p.id === id);

registrarAcao("filtroPapel", (alvo) => {
  tela.filtro = alvo.dataset.valor ?? "";
  render();
});
registrarAcao("novoParceiro", () => formParceiro());
registrarAcao("parceiroEditar", (alvo) => {
  const p = porId(alvo.dataset.id);
  if (p) formParceiro(p);
});
registrarAcao("parceiroExcluir", (alvo) => {
  const p = porId(alvo.dataset.id);
  if (p) confirmarExclusao({ titulo: "Excluir parceiro", mensagem: `Excluir o parceiro “${p.nome}”? Parceiros com títulos lançados não podem ser excluídos.`, sucesso: "Parceiro excluído", operacao: () => apiFinanceiro.parceiros.excluir(p.id) });
});

