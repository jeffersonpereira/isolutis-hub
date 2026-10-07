import { $ } from "@/core/dom";
import { brl } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { numero, paraCampo } from "@/core/numero";
import { registrarVista } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { campo, fv, inp, sel } from "@/ui/campos";
import { tentar } from "@/ui/erros";
import { abrirGaveta } from "@/ui/gaveta";
import { espaco } from "@/ui/formularios";
import { gravar } from "@/ui/gravacao";
import { avisar } from "@/ui/toast";
import { apiFinanceiro, type ContaBancaria, type ContaBancariaEntrada } from "./api";
import { acoesDaLinha, confirmarExclusao, GRUPO } from "./comum";

const tela: { contas: ContaBancaria[] | null } = { contas: null };

async function carregar(): Promise<void> {
  tela.contas = await apiFinanceiro.contas.listar();
}

function vista(): Safe {
  if (!tela.contas) return html`<div class="head"><div><h1>Contas bancárias</h1></div></div><p class="sub">Carregando…</p>`;
  return html`<div class="head"><div><h1>Contas bancárias</h1><p>As contas da empresa, cada uma vinculada a uma instituição financeira.</p></div>
    <div class="tools"><button class="btn primary" data-act="novaContaBancaria">Nova conta bancária</button></div></div>
  ${
    tela.contas.length
      ? html`<div class="tbl-wrap"><table><thead><tr><th>Conta</th><th>Instituição financeira</th><th class="r">Saldo inicial</th><th></th></tr></thead><tbody>
      ${tela.contas.map((c) => html`<tr><td><b>${c.nome}</b></td><td>${c.instituicao_codigo} · ${c.instituicao_nome}</td><td class="r num">${brl(c.saldo_inicial)}</td><td class="r">${acoesDaLinha("contaBancaria", c.id)}</td></tr>`)}
    </tbody></table></div>`
      : html`<div class="empty"><b>Nenhuma conta bancária</b>Cadastre as contas da empresa para poder lançar títulos a pagar e a receber.<br><button class="btn primary" data-act="novaContaBancaria">Cadastrar a primeira conta</button></div>`
  }`;
}

registrarVista({ id: "fin-contas", nome: "Conta Bancária", grupo: GRUPO, permissao: "financeiro", carregar, depende: ["financeiro"], desenhar: vista });

async function formConta(c?: ContaBancaria): Promise<void> {
  const instituicoes = await tentar(() => apiFinanceiro.instituicoes());
  if (!instituicoes) return;
  abrirGaveta({
    titulo: c ? c.nome : "Nova conta bancária",
    corpo: html`<div class="fields">
      ${campo("Instituição financeira", sel("instituicao_financeira_id", [["", "Selecione…"], ...instituicoes.map((i) => [i.id, `${i.codigo} · ${i.nome}`] as const)], c?.instituicao_financeira_id ?? ""), true)}
      ${campo("Nome da conta", inp("nome", c?.nome, 'maxlength="150" placeholder="Ex.: Conta corrente principal"'), true)}
      ${campo("Saldo inicial (R$)", inp("saldo_inicial", paraCampo(c?.saldo_inicial), 'inputmode="decimal" placeholder="0,00"'))}
    </div>`,
    rodape: html`<button class="btn primary" data-salvar>Salvar</button>${espaco}`,
    montar: (f, fechar, L) => {
      $("[data-salvar]", L)?.addEventListener("click", async () => {
        if (!fv(f, "instituicao_financeira_id")) return void avisar("Escolha a instituição financeira.");
        if (!fv(f, "nome")) return void avisar("Informe o nome da conta.");
        const corpo: ContaBancariaEntrada = { instituicao_financeira_id: fv(f, "instituicao_financeira_id"), nome: fv(f, "nome"), saldo_inicial: numero(fv(f, "saldo_inicial")) };
        await gravar({
          recarregar: ["financeiro"], mensagem: "Conta bancária salva", fechar,
          operacao: () => (c ? apiFinanceiro.contas.atualizar(c.id, corpo) : apiFinanceiro.contas.criar(corpo)),
        });
      });
    },
  });
}

const porId = (id?: string): ContaBancaria | undefined => tela.contas?.find((c) => c.id === id);

registrarAcao("novaContaBancaria", () => void formConta());
registrarAcao("contaBancariaEditar", (alvo) => {
  const c = porId(alvo.dataset.id);
  if (c) void formConta(c);
});
registrarAcao("contaBancariaExcluir", (alvo) => {
  const c = porId(alvo.dataset.id);
  if (c) confirmarExclusao({ titulo: "Excluir conta bancária", mensagem: `Excluir a conta “${c.nome}”? Contas com títulos lançados não podem ser excluídas.`, sucesso: "Conta bancária excluída", operacao: () => apiFinanceiro.contas.excluir(c.id) });
});
