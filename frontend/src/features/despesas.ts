import { api } from "@/api/endpoints";
import type { Despesa, DespesaEntrada, Investimento, InvestimentoEntrada, OpcoesDespesa, ResumoDespesas } from "@/api/tipos";
import { $, $$ } from "@/core/dom";
import { MESES, brl, dataBR, hoje } from "@/core/formato";
import { html, raw, type Safe } from "@/core/html";
import { numero, paraCampo } from "@/core/numero";
import { FORMAS_INVEST, OPCOES_REPETICAO } from "@/domain/constantes";
import { podeEscrever, ui } from "@/state/estado";
import { recarregar, registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { toast } from "@/ui/toast";

const pagina: { ano: number; resumo: ResumoDespesas | null; despesas: Despesa[]; investimentos: Investimento[]; opcoes: OpcoesDespesa | null } = {
  ano: 0, resumo: null, despesas: [], investimentos: [], opcoes: null,
};

registrarConsulta("despesas", (id) => pagina.despesas.find((d) => d.id === id) ?? pagina.investimentos.find((i) => i.id === id));

async function carregar(): Promise<void> {
  const ano = ui.ano;
  const [resumo, despesas, investimentos, opcoes] = await Promise.all([api.despesas.resumo(ano), api.despesas.listar(ano), api.investimentos.listar(ano), api.despesas.opcoes()]);
  if (ano !== ui.ano) return;
  Object.assign(pagina, { ano, resumo, despesas, investimentos, opcoes });
}

type Linha = { tipo: "despesa"; d: Despesa } | { tipo: "investimento"; i: Investimento };

function vista(): Safe {
  const r = pagina.resumo;
  if (!r || pagina.ano !== ui.ano) return html`<div class="head"><div><h1>Despesas e investimentos</h1></div></div><p class="sub">Carregando…</p>`;
  const ano = ui.ano;
  const mesAtual = new Date().getFullYear() === ano ? new Date().getMonth() + 1 : 0;
  const escrever = podeEscrever();
  const filtro = ui.despTipo;
  const linhas: Linha[] = [
    ...(filtro === "investimento" ? [] : pagina.despesas.map((d): Linha => ({ tipo: "despesa", d }))),
    ...(filtro === "despesa" ? [] : pagina.investimentos.map((i): Linha => ({ tipo: "investimento", i }))),
  ]
    .filter((l) => !ui.mes || Number((l.tipo === "despesa" ? l.d.data : l.i.data).slice(5, 7)) === ui.mes)
    .sort((a, b) => (a.tipo === "despesa" ? a.d.data : a.i.data).localeCompare(b.tipo === "despesa" ? b.d.data : b.i.data));
  const maxP = Math.max(1, ...r.investidores.map((p) => p.total));
  const vazio = !pagina.despesas.length && !pagina.investimentos.length && !r.recebido_no_ano;
  const totalDespesas = r.despesas_pagas + r.despesas_a_pagar;

  return html`<div class="head"><div><h1>Despesas e investimentos</h1><p>O que sai do caixa, o que os sócios colocaram na empresa e quanto sobra do que foi recebido.</p></div>
    <div class="tools"><div class="field" style="flex-direction:row;align-items:center;gap:6px"><label for="ano">Ano</label><select id="ano" data-act="mudarAno">${r.anos_disponiveis.map((a) => html`<option${a === ano ? " selected" : ""}>${a}</option>`)}</select></div>
    ${escrever ? html`<button class="btn" data-act="novoInvest">Novo investimento</button><button class="btn primary" data-act="novaDespesa">Nova despesa</button>` : ""}</div></div>
  ${vazio ? html`<div class="empty" style="margin-bottom:16px"><b>Nenhuma despesa ou investimento registrado</b>Registre as despesas da empresa (servidores, softwares, contador, impostos) e os aportes de cada sócio. O resultado do ano é calculado com o faturamento recebido.${escrever ? html`<br><button class="btn primary" data-act="novaDespesa">Registrar despesa</button> <button class="btn" data-act="novoInvest">Registrar investimento</button>` : ""}</div>` : ""}
  <div class="kpis">
    <div class="kpi"><span class="l">Recebido em ${ano}</span><span class="v">${brl(r.recebido_no_ano)}</span><span class="s">faturamento marcado como recebido</span></div>
    <div class="kpi"><span class="l">Despesas pagas</span><span class="v">${brl(r.despesas_pagas)}</span><span class="s">${r.despesas_a_pagar ? brl(r.despesas_a_pagar) + " ainda a pagar" : "nada pendente"}</span></div>
    <div class="kpi"><span class="l">Resultado</span><span class="v" style="color:${r.resultado < 0 ? "var(--bad)" : "var(--ok)"}">${brl(r.resultado)}</span><span class="s">recebido menos despesas pagas</span></div>
    <div class="kpi"><span class="l">Investido em ${ano}</span><span class="v">${brl(r.investido_no_ano)}</span><span class="s">${brl(r.investido_total)} desde o início</span></div>
  </div>
  <div class="two">
    <div class="tbl-wrap"><table style="min-width:520px"><thead><tr><th>Mês</th><th class="r">Recebido</th><th class="r">Despesas</th><th class="r">Resultado</th><th class="r">Investimentos</th></tr></thead><tbody>
      ${r.meses.map(
        (m) => html`<tr tabindex="0" data-act="mes" data-valor="${m.mes}" style="${ui.mes === m.mes ? "background:var(--gold-soft)" : ""}"><td>${MESES[m.mes - 1]}${m.mes === mesAtual ? html` <span class="pill gold">atual</span>` : ""}</td><td class="r num">${m.recebido ? brl(m.recebido) : "—"}</td><td class="r num">${m.despesas ? brl(m.despesas) : "—"}</td>
        <td class="r num" style="${m.resultado < 0 ? "color:var(--bad)" : ""}">${m.recebido || m.despesas ? brl(m.resultado) : "—"}</td><td class="r num">${m.investimentos ? brl(m.investimentos) : "—"}</td></tr>`,
      )}
    </tbody><tfoot><tr><td>Total ${ano}</td><td class="r num">${brl(r.recebido_no_ano)}</td><td class="r num">${brl(totalDespesas)}</td><td class="r num">${brl(r.recebido_no_ano - totalDespesas)}</td><td class="r num">${brl(r.investido_no_ano)}</td></tr></tfoot></table></div>
    <div class="panel"><h2>Quem investiu</h2>
      ${
        r.investidores.length
          ? html`<div class="funnel">${r.investidores.map(
              (p) => html`<div class="frow"><span>${p.nome}</span><div class="fbar"><i style="width:${Math.max(3, (100 * p.total) / maxP)}%"></i></div><span class="num">${brl(p.total)}</span></div><div class="sub" style="margin:-6px 0 4px">${p.no_ano ? brl(p.no_ano) + " em " + ano + " · " : ""}${r.investido_total ? p.percentual + "% do total investido" : ""}</div>`,
            )}</div>`
          : html`<p class="sub">Cada investimento registra quem colocou o dinheiro. O total de cada pessoa aparece aqui.</p>`
      }
    </div>
  </div>
  <div class="panel" style="margin-top:16px">
    <div class="head" style="margin-bottom:10px"><h2 style="margin:0">${ui.mes ? html`Lançamentos de ${MESES[ui.mes - 1]?.toLowerCase()} <button class="btn ghost" data-act="limparMes">ver o ano todo</button>` : `Lançamentos de ${ano}`}</h2>
      <div class="seg" role="group" aria-label="Filtrar">${[["todos", "Todos"], ["despesa", "Despesas"], ["investimento", "Investimentos"]].map(([k, rot]) => html`<button data-act="filtroDesp" data-valor="${k}" aria-pressed="${filtro === k}">${rot}</button>`)}</div></div>
    ${
      linhas.length
        ? html`<div class="list">${linhas.map((l) => (l.tipo === "despesa" ? linhaDespesa(l.d, escrever) : linhaInvestimento(l.i)))}</div>`
        : html`<p class="sub">Nenhum lançamento ${ui.mes ? "neste mês" : "neste ano"} com esse filtro.</p>`
    }
  </div>`;
}

const linhaDespesa = (d: Despesa, escrever: boolean): Safe => html`<div class="li" data-open="desp:${d.id}" tabindex="0"><div><div class="t">${d.descricao || d.categoria_nome || "Despesa"}</div><div class="sub">${dataBR(d.data)} · ${d.categoria_nome}${d.fornecedor ? " · " + d.fornecedor : ""}</div></div>
  <div style="text-align:right"><div class="num">− ${brl(d.valor)}</div>${d.status === "a_pagar" ? html`<span class="pill warn">A pagar</span>${escrever ? html` <button class="btn ghost" data-act="pagar" data-id="${d.id}" style="padding:0 4px;font-size:12px">marcar pago</button>` : ""}` : html`<span class="pill">Paga</span>`}</div></div>`;

const linhaInvestimento = (i: Investimento): Safe => html`<div class="li" data-open="invest:${i.id}" tabindex="0"><div><div class="t">${i.descricao || "Investimento"}</div><div class="sub">${dataBR(i.data)} · Investido por <b>${i.investidor_nome}</b>${i.forma ? " · " + i.forma : ""}</div></div>
  <div style="text-align:right"><div class="num">${brl(i.valor)}</div><span class="pill info">Investimento</span></div></div>`;

registrarVista({ id: "despesas", nome: "Despesas e investimentos", carregar, depende: ["despesas", "faturamento"], desenhar: vista });

type Tipo = "despesa" | "investimento";

function formLancamento(tipoInicial: Tipo, d?: Despesa, inv?: Investimento): void {
  const editando = !!(d ?? inv);
  const reg = d ?? inv;
  const op = pagina.opcoes ?? { categorias: [], investidores: [], fornecedores: [] };
  const titulo = (t: Tipo): string => (editando ? (t === "investimento" ? "Investimento" : "Despesa") : t === "investimento" ? "Novo investimento" : "Nova despesa");
  abrirGaveta({
    titulo: titulo(tipoInicial),
    registro: reg ? { recurso: "despesas", id: reg.id, versao: reg.versao } : null,
    autoria: linhaAutoria(reg),
    corpo: html`<div class="fields">
      ${campo("Tipo", raw(`<select name="tipo" id="f-tipo"${editando ? " disabled" : ""}><option value="despesa"${tipoInicial === "despesa" ? " selected" : ""}>Despesa</option><option value="investimento"${tipoInicial === "investimento" ? " selected" : ""}>Investimento</option></select>`))}
      ${campo("Data", inp("data", (d ?? inv)?.data ?? hoje(), 'type="date"'))}
      ${campo("Descrição", inp("descricao", reg ? (d ?? inv)?.descricao : "", `placeholder="${tipoInicial === "investimento" ? "Ex.: Aporte para compra de notebooks" : "Ex.: Hospedagem dos sistemas dos clientes"}"`), true)}
      ${campo("Valor (R$)", inp("valor", paraCampo((d ?? inv)?.valor), 'inputmode="decimal" placeholder="0,00"'))}
      <div class="field so-inv"${tipoInicial === "investimento" ? "" : " hidden"}><label for="f-investidor">Quem investiu</label>${inp("investidor", inv?.investidor_nome, 'list="investidores" placeholder="Nome de quem colocou o dinheiro"')}<datalist id="investidores">${op.investidores.map((n) => html`<option value="${n}">`)}</datalist></div>
      <div class="field so-inv"${tipoInicial === "investimento" ? "" : " hidden"}><label for="f-forma">Forma</label>${sel("forma", FORMAS_INVEST.map((f) => [f, f] as const), inv?.forma ?? FORMAS_INVEST[0])}</div>
      <div class="field so-desp"${tipoInicial === "investimento" ? " hidden" : ""}><label for="f-categoria_id">Categoria</label>${sel("categoria_id", op.categorias.map((c) => [c.id, c.nome] as const), d?.categoria_id ?? op.categorias[0]?.id)}</div>
      <div class="field so-desp"${tipoInicial === "investimento" ? " hidden" : ""}><label for="f-status">Situação</label>${sel("status", [["pago", "Paga"], ["a_pagar", "A pagar"]], d?.status ?? "pago")}</div>
      <div class="field so-desp"${tipoInicial === "investimento" ? " hidden" : ""}><label for="f-fornecedor">Fornecedor</label>${inp("fornecedor", d?.fornecedor, 'list="fornecedores" placeholder="Ex.: AWS, contador, Google"')}<datalist id="fornecedores">${op.fornecedores.map((n) => html`<option value="${n}">`)}</datalist></div>
      ${editando ? "" : html`<div class="field so-desp"${tipoInicial === "investimento" ? " hidden" : ""}><label for="f-repetir">Repetir todo mês por</label>${sel("repetir", OPCOES_REPETICAO.map((n) => [n, n === 1 ? "Não repetir" : `${n} meses`] as const), 1)}</div>`}
      ${campo("Observação", area("obs", (d ?? inv)?.obs, tipoInicial === "investimento" ? "Ex.: devolver quando a empresa tiver caixa, entra como participação…" : "Nota fiscal, forma de pagamento…"), true)}</div>`,
    rodape: html`${botaoSalvar()}${espaco}${botaoExcluir(editando)}`,
    montar: (f, fechar, L) => {
      const tipoSel = f.elements.namedItem("tipo") as HTMLSelectElement;
      tipoSel.addEventListener("change", () => {
        const inv_ = tipoSel.value === "investimento";
        $$(".so-inv", f).forEach((e) => (e.hidden = !inv_));
        $$(".so-desp", f).forEach((e) => (e.hidden = inv_));
        $(".drawer header h2", L)!.textContent = titulo(inv_ ? "investimento" : "despesa");
      });
      $("[data-salvar]", L)?.addEventListener("click", async () => {
        const tipo = (editando ? tipoInicial : tipoSel.value) as Tipo;
        if (!numero(fv(f, "valor"))) return void toast("Informe o valor.");
        const base = { data: fv(f, "data") || hoje(), descricao: fv(f, "descricao"), valor: numero(fv(f, "valor")), obs: fv(f, "obs") || null };
        if (tipo === "investimento") {
          if (!fv(f, "investidor")) return void toast("Informe quem investiu.");
          if (!base.descricao) base.descricao = "Investimento";
          const corpo: InvestimentoEntrada = { ...base, investidor: fv(f, "investidor"), forma: fv(f, "forma") as InvestimentoEntrada["forma"] };
          await gravar({
            recarregar: ["despesas"], fechar, mensagem: editando ? "Investimento salvo" : "Investimento registrado",
            operacao: () => (inv ? api.investimentos.atualizar(inv.id, { ...corpo, versao: inv.versao }) : api.investimentos.criar(corpo)),
          });
          return;
        }
        if (!base.descricao) base.descricao = op.categorias.find((c) => c.id === fv(f, "categoria_id"))?.nome ?? "Despesa";
        const corpo: Omit<DespesaEntrada, "repetir"> = { ...base, categoria_id: fv(f, "categoria_id"), status: fv(f, "status") as DespesaEntrada["status"], fornecedor: fv(f, "fornecedor") || null };
        const repetir = Number(fv(f, "repetir")) || 1;
        await gravar({
          recarregar: ["despesas"], fechar, mensagem: editando ? "Despesa salva" : repetir > 1 ? `${repetir} despesas criadas` : "Despesa registrada",
          operacao: async () => (d ? await api.despesas.atualizar(d.id, { ...corpo, versao: d.versao }) : await api.despesas.criar({ ...corpo, repetir })),
        });
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (d) void excluir({ recarregar: ["despesas"], mensagem: "Lançamento excluído", fechar, operacao: () => api.despesas.excluir(d.id) });
        if (inv) void excluir({ recarregar: ["despesas"], mensagem: "Lançamento excluído", fechar, operacao: () => api.investimentos.excluir(inv.id) });
      });
    },
  });
}

registrarAcao("novaDespesa", () => formLancamento("despesa"));
registrarAcao("novoInvest", () => formLancamento("investimento"));
registrarAcao("filtroDesp", (alvo) => {
  ui.despTipo = alvo.dataset.valor ?? "todos";
  render();
});
registrarAcao("pagar", async (alvo) => {
  const id = alvo.dataset.id;
  if (id && (await tentar(() => api.despesas.pagar(id))) !== null) {
    await recarregar("despesas");
    toast("Despesa marcada como paga");
  }
});
registrarAbertura("desp", (id) => {
  const d = pagina.despesas.find((x) => x.id === id);
  if (d) formLancamento("despesa", d);
});
registrarAbertura("invest", (id) => {
  const i = pagina.investimentos.find((x) => x.id === id);
  if (i) formLancamento("investimento", undefined, i);
});
