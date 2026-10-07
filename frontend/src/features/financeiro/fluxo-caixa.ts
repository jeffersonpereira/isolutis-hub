import { brl, MESES } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { ui } from "@/state/estado";
import { recarregarVista, registrarVista } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { apiFinanceiro, type FluxoDeCaixa } from "./api";
import { GRUPO } from "./comum";

const tela: { ano: number; fluxo: FluxoDeCaixa | null } = { ano: 0, fluxo: null };

async function carregar(): Promise<void> {
  const ano = ui.ano;
  const fluxo = await apiFinanceiro.fluxoDeCaixa(ano);
  if (ano === ui.ano) Object.assign(tela, { ano, fluxo });
}

const valorOuTraco = (v: number): string => (v ? brl(v) : "—");

function vista(): Safe {
  const f = tela.fluxo;
  if (!f || tela.ano !== ui.ano) return html`<div class="head"><div><h1>Fluxo de caixa</h1></div></div><p class="sub">Carregando…</p>`;
  const mesAtual = new Date().getFullYear() === f.ano ? new Date().getMonth() + 1 : 0;
  const saldoFinal = f.meses[11]?.saldo_acumulado ?? f.saldo_inicial;
  return html`<div class="head"><div><h1>Fluxo de caixa mensal</h1><p>Realizado = títulos quitados, pelo dia do pagamento · Previsto = títulos em aberto, pelo vencimento. Cancelados não entram.</p></div>
    <div class="tools"><div class="field" style="flex-direction:row;align-items:center;gap:6px"><label for="anoFluxo">Ano</label><select id="anoFluxo" data-act="mudarAnoFluxo">${f.anos_disponiveis.map((a) => html`<option${a === f.ano ? " selected" : ""}>${a}</option>`)}</select></div></div></div>
  <div class="kpis">
    <div class="kpi"><span class="l">Saldo inicial de ${f.ano}</span><span class="v">${brl(f.saldo_inicial)}</span><span class="s">saldos das contas + movimento anterior</span></div>
    <div class="kpi"><span class="l">Entradas no ano</span><span class="v" style="color:var(--ok-texto)">${brl(f.total_entradas)}</span><span class="s">realizadas + previstas</span></div>
    <div class="kpi"><span class="l">Saídas no ano</span><span class="v" style="color:var(--bad-texto)">${brl(f.total_saidas)}</span><span class="s">realizadas + previstas</span></div>
    <div class="kpi"><span class="l">Saldo projetado</span><span class="v" style="color:${saldoFinal < 0 ? "var(--bad)" : "var(--ink)"}">${brl(saldoFinal)}</span><span class="s">em dezembro de ${f.ano}</span></div>
  </div>
  <div class="tbl-wrap"><table class="fluxo" style="min-width:820px"><thead><tr><th>Mês</th><th class="r">Entradas realizadas</th><th class="r">Entradas previstas</th><th class="r">Saídas realizadas</th><th class="r">Saídas previstas</th><th class="r">Saldo do mês</th><th class="r">Saldo acumulado</th></tr></thead><tbody>
    ${f.meses.map(
      (m) => html`<tr><td>${MESES[m.mes - 1]}${m.mes === mesAtual ? html` <span class="pill teal-mid">atual</span>` : ""}</td><td class="r num ent">${valorOuTraco(m.entradas_realizadas)}</td><td class="r num ent">${valorOuTraco(m.entradas_previstas)}</td>
      <td class="r num sai">${valorOuTraco(m.saidas_realizadas)}</td><td class="r num sai">${valorOuTraco(m.saidas_previstas)}</td>
      <td class="r num" style="${m.saldo_do_mes < 0 ? "color:var(--bad-texto)" : ""}">${valorOuTraco(m.saldo_do_mes)}</td><td class="r num" style="${m.saldo_acumulado < 0 ? "color:var(--bad-texto)" : ""}"><b>${brl(m.saldo_acumulado)}</b></td></tr>`,
    )}
  </tbody></table></div>`;
}

registrarVista({ id: "fin-fluxo", nome: "Fluxo de Caixa", grupo: GRUPO, somenteAdmin: true, carregar, depende: ["financeiro"], desenhar: vista });

registrarAcao("mudarAnoFluxo", async (alvo) => {
  ui.ano = Number((alvo as HTMLSelectElement).value);
  await recarregarVista();
});
