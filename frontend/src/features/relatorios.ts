import { api } from "@/api/endpoints";
import type { DreItem, FluxoItem } from "@/api/tipos";
import { brl } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { ui } from "@/state/estado";
import { registrarAcao } from "@/ui/acoes";
import { tentar } from "@/ui/erros";

const pagina: {
  ano: number;
  dre: DreItem[] | null;
  fluxo: FluxoItem[] | null;
  aba: "dre" | "fluxo";
} = {
  ano: new Date().getFullYear(),
  dre: null,
  fluxo: null,
  aba: "dre",
};

// ─── Carga ────────────────────────────────────────────────────────────────────

async function carregar(): Promise<void> {
  const ano = pagina.ano;
  const [dre, fluxo] = await Promise.all([
    api.relatorios.dre(ano),
    api.relatorios.fluxoCaixa(ano),
  ]);
  if (pagina.ano !== ano) return; // troca de ano durante o carregamento
  pagina.dre = dre;
  pagina.fluxo = fluxo;
}

// ─── Controles (seletor de ano + abas + exportação) ───────────────────────────

function vistaControles(): Safe {
  const anoAtual = new Date().getFullYear();
  const anos = Array.from({ length: 5 }, (_, i) => anoAtual - i);
  return html`
    <div class="head">
      <div>
        <h1>Relatórios financeiros</h1>
        <p>DRE e fluxo de caixa da empresa</p>
      </div>
      <div class="tools">
        <div class="field" style="flex-direction:row;align-items:center;gap:6px">
          <label for="relAno">Ano</label>
          <select id="relAno" data-act="relMudarAno">
            ${anos.map((a) => html`<option${a === pagina.ano ? " selected" : ""}>${a}</option>`)}
          </select>
        </div>
        <div class="seg">
          <button aria-pressed="${pagina.aba === "dre"}" data-act="relAba" data-valor="dre">DRE</button>
          <button aria-pressed="${pagina.aba === "fluxo"}" data-act="relAba" data-valor="fluxo">Fluxo de Caixa</button>
        </div>
        <button class="btn" data-act="relExportarPdf">PDF</button>
        <button class="btn" data-act="relExportarXlsx">Excel (.xlsx)</button>
      </div>
    </div>`;
}

// ─── DRE ─────────────────────────────────────────────────────────────────────

function vistaDre(): Safe {
  if (!pagina.dre) {
    return html`<div class="skeleton skeleton-chart" style="height:320px;border-radius:var(--r)"></div>`;
  }
  const dados = pagina.dre;
  if (!dados.length) {
    return html`<div class="empty"><b>Sem dados para este período</b>Nenhum lançamento encontrado para ${pagina.ano}.</div>`;
  }

  const totalReceitas = dados.reduce((s, r) => s + r.receitas, 0);
  const totalCustos = dados.reduce((s, r) => s + r.custos, 0);
  const totalResultado = totalReceitas - totalCustos;

  return html`
    <div class="tbl-wrap">
      <table style="min-width:540px">
        <thead>
          <tr>
            <th>Mês</th>
            <th class="r">Receitas</th>
            <th class="r">Custos</th>
            <th class="r">Resultado</th>
          </tr>
        </thead>
        <tbody>
          ${dados.map((row) => html`
            <tr>
              <td>${row.nome_mes}</td>
              <td class="r num">${brl(row.receitas)}</td>
              <td class="r num">${brl(row.custos)}</td>
              <td class="r num" style="color:${row.resultado >= 0 ? "var(--ok)" : "var(--bad)"}">
                ${brl(row.resultado)}
              </td>
            </tr>`)}
        </tbody>
        <tfoot>
          <tr>
            <td>Total ${pagina.ano}</td>
            <td class="r num">${brl(totalReceitas)}</td>
            <td class="r num">${brl(totalCustos)}</td>
            <td class="r num" style="color:${totalResultado >= 0 ? "var(--ok)" : "var(--bad)"}">
              ${brl(totalResultado)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>`;
}

// ─── Fluxo de caixa ───────────────────────────────────────────────────────────

function vistaFluxo(): Safe {
  if (!pagina.fluxo) {
    return html`<div class="skeleton skeleton-chart" style="height:320px;border-radius:var(--r)"></div>`;
  }
  const dados = pagina.fluxo;
  if (!dados.length) {
    return html`<div class="empty"><b>Sem dados para este período</b>Nenhum lançamento encontrado para ${pagina.ano}.</div>`;
  }

  const totalEntradas = dados.reduce((s, r) => s + r.entradas, 0);
  const totalSaidas = dados.reduce((s, r) => s + r.saidas, 0);
  const saldoFinal = dados[dados.length - 1]?.saldo_acumulado ?? 0;

  return html`
    <div class="tbl-wrap">
      <table style="min-width:580px">
        <thead>
          <tr>
            <th>Mês</th>
            <th class="r">Entradas</th>
            <th class="r">Saídas</th>
            <th class="r">Saldo do mês</th>
            <th class="r">Saldo acumulado</th>
          </tr>
        </thead>
        <tbody>
          ${dados.map((row) => html`
            <tr>
              <td>${row.nome_mes}</td>
              <td class="r num">${brl(row.entradas)}</td>
              <td class="r num">${brl(row.saidas)}</td>
              <td class="r num" style="color:${row.saldo >= 0 ? "var(--ok)" : "var(--bad)"}">
                ${brl(row.saldo)}
              </td>
              <td class="r num" style="color:${row.saldo_acumulado >= 0 ? "var(--ok)" : "var(--bad)"}">
                ${brl(row.saldo_acumulado)}
              </td>
            </tr>`)}
        </tbody>
        <tfoot>
          <tr>
            <td>Total ${pagina.ano}</td>
            <td class="r num">${brl(totalEntradas)}</td>
            <td class="r num">${brl(totalSaidas)}</td>
            <td class="r num">${brl(totalEntradas - totalSaidas)}</td>
            <td class="r num" style="color:${saldoFinal >= 0 ? "var(--ok)" : "var(--bad)"}">
              ${brl(saldoFinal)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>`;
}

// ─── Vista principal ──────────────────────────────────────────────────────────

function vista(): Safe {
  return html`
    <div class="relatorios-tela">
      ${vistaControles()}
      ${pagina.aba === "dre" ? vistaDre() : vistaFluxo()}
    </div>`;
}

// ─── Registro ─────────────────────────────────────────────────────────────────

registrarVista({
  id: "relatorios",
  nome: "Relatórios",
  grupo: "Financeiro",
  carregar,
  desenhar: vista,
});

// ─── Ações ────────────────────────────────────────────────────────────────────

registrarAcao("relMudarAno", (alvo) => {
  const select = alvo as HTMLSelectElement;
  const novoAno = Number(select.value);
  if (!novoAno || novoAno === pagina.ano) return;
  pagina.ano = novoAno;
  pagina.dre = null;
  pagina.fluxo = null;
  ui.ano = novoAno;
  render();
  void carregar().then(render);
});

registrarAcao("relAba", (alvo) => {
  const valor = alvo.dataset.valor as "dre" | "fluxo" | undefined;
  if (!valor || valor === pagina.aba) return;
  pagina.aba = valor;
  render();
});

registrarAcao("relExportarPdf", async () => {
  const tipo = pagina.aba === "dre" ? "dre" : "fluxo-caixa";
  await tentar(() => api.relatorios.exportarPdf(tipo, pagina.ano));
});

registrarAcao("relExportarXlsx", async () => {
  const tipo = pagina.aba === "dre" ? "dre" : "fluxo-caixa";
  await tentar(() => api.relatorios.exportarXlsx(tipo, pagina.ano));
});

