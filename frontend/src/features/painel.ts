import { api } from "@/api/endpoints";
import type { Painel } from "@/api/tipos";
import { MES3, MESES, brl, brlCurto, dataBR, hoje, pluralizar, primeiroNome } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { carregando } from "@/ui/componentes";
import { etapaNome } from "@/domain/constantes";
import { eu, podeEscrever, temPermissao } from "@/state/estado";
import { registrarVista } from "@/state/nucleo";
import { botaoNovo } from "./comum";
import { graficoFaturamento, legendaFaturamento } from "./grafico";

let dadosPainel: Painel | null = null;

async function carregar(): Promise<void> {
  dadosPainel = await api.painel.obter();
}

type AlertasInfo = Painel["alertas"];

/** Cada alerta só vem quando o papel pode ver o bloco dele; o que não vier simplesmente não aparece. */
function vistaAlertas(alertas: AlertasInfo): string {
  const { lancamentos_vencidos, orcamentos_parados, projetos_atrasados } = alertas;
  const itens: string[] = [];
  if (lancamentos_vencidos && lancamentos_vencidos.quantidade > 0) {
    itens.push(`<div class="alerta bad" data-go="faturamento">${lancamentos_vencidos.quantidade} lançamento(s) vencido(s) há mais de 3 dias</div>`);
  }
  if (orcamentos_parados && orcamentos_parados.quantidade > 0) {
    itens.push(`<div class="alerta warn" data-go="orcamentos">${orcamentos_parados.quantidade} orçamento(s) sem resposta há mais de 15 dias</div>`);
  }
  if (projetos_atrasados.quantidade > 0) {
    itens.push(`<div class="alerta bad" data-go="projetos">${projetos_atrasados.quantidade} projeto(s) com entrega atrasada</div>`);
  }
  return itens.length ? `<div class="alertas-zona">${itens.join("")}</div>` : "";
}

function blocoFinanceiro(p: Painel, mesNome: string, h: string): Safe {
  if (p.recebido_no_mes == null || p.serie == null) return html``;
  const serie = p.serie.map((s, i) => ({
    rotulo: (MES3[s.mes - 1] ?? "") + (s.mes === 1 || i === 0 ? " " + String(s.ano).slice(2) : ""),
    recebido: s.recebido, previsto: s.previsto, atual: s.ano === p.ano && s.mes === p.mes,
  }));
  void h;
  return html`<div class="kpis">
    <div class="kpi"><span class="l">Recebido no mês</span><span class="v">${brl(p.recebido_no_mes)}</span><span class="s">de ${brl(p.previsto_no_mes ?? 0)} lançados para ${mesNome.toLowerCase()}</span></div>
    <div class="kpi"><span class="l">Receita recorrente</span><span class="v">${brl(p.recorrente_no_mes ?? 0)}</span><span class="s">manutenções mensais deste mês</span></div>
  </div>
  <div class="panel chart" style="margin-bottom:16px"><h2>Faturamento dos últimos 12 meses</h2>${graficoFaturamento(serie)}${legendaFaturamento}</div>`;
}

function blocoComercial(p: Painel, h: string): Safe {
  if (p.funil_abertos == null || p.por_etapa == null) return html``;
  const abertos = p.funil_abertos;
  const ganhos = p.ganhos ?? 0;
  const perdidos = p.perdidos ?? 0;
  const maxN = Math.max(1, ...p.por_etapa.map((e) => e.quantidade));
  const proximos = p.proximos_fechamentos ?? [];
  const aguardando = p.orcamentos_aguardando ?? [];
  return html`<div class="kpis">
    <div class="kpi"><span class="l">Funil em aberto</span><span class="v">${brlCurto(p.funil_valor ?? 0)}</span><span class="s">${abertos} ${pluralizar(abertos, "negócio", "negócios")}${p.funil_mensal ? " · + " + brl(p.funil_mensal) + "/mês" : ""}</span></div>
    <div class="kpi"><span class="l">Taxa de conversão</span><span class="v">${p.conversao_pct == null ? "—" : p.conversao_pct + "%"}</span><span class="s">${ganhos} ${pluralizar(ganhos, "ganho", "ganhos")} · ${perdidos} ${pluralizar(perdidos, "perdido", "perdidos")}</span></div>
    <div class="kpi"><span class="l">Orçamentos aguardando</span><span class="v">${p.orcamentos_aguardando_qtd ?? 0}</span><span class="s">${brl(p.orcamentos_aguardando_valor ?? 0)} em projetos</span></div>
  </div>
  <div class="two">
    <div class="panel"><h2>Funil por etapa</h2>
      ${
        abertos
          ? html`<div class="funnel">${p.por_etapa.map((e) => html`<div class="frow"><span>${etapaNome(e.etapa)}</span><div class="fbar"><i style="width:${e.quantidade ? Math.max(4, (100 * e.quantidade) / maxN) : 0}%"></i></div><span class="num sub">${e.quantidade}</span></div>`)}</div>
      <p class="sub" style="margin:10px 0 0">Valor em aberto considera o projeto mais 12 meses de manutenção.</p>`
          : html`<p class="sub">Nenhum negócio em aberto.</p>`
      }
    </div>
    <div class="panel"><h2>Próximos fechamentos</h2>
      ${
        proximos.length
          ? html`<div class="list">${proximos.map((n) => {
              const atrasado = n.previsao < h;
              const valor = [n.valor ? brl(n.valor) : "", n.mensal ? brl(n.mensal) + "/mês" : ""].filter(Boolean).join(" + ") || "sem valor";
              return html`<div class="li" data-open="negocio:${n.id}" tabindex="0"><div><div class="t">${n.titulo}</div><div class="sub">${n.cliente_nome} · ${etapaNome(n.etapa)}</div></div><div style="text-align:right"><div class="num">${valor}</div><div class="sub ${atrasado ? "late" : ""}" style="${atrasado ? "color:var(--bad-texto)" : ""}">${atrasado ? "atrasado · " : ""}${dataBR(n.previsao)}</div></div></div>`;
            })}</div>`
          : html`<p class="sub">Negócios com data prevista de fechamento aparecem aqui.</p>`
      }
    </div>
  </div>
  <div class="panel" style="margin-top:16px"><h2>Orçamentos aguardando resposta</h2>
    ${
      aguardando.length
        ? html`<div class="list">${aguardando.map((o) => html`<div class="li" data-open="orcamento:${o.id}" tabindex="0"><div><div class="t">Nº ${o.numero}</div><div class="sub">${o.cliente_nome} · enviado em ${dataBR(o.data)}</div></div><div class="num">${brl(o.total_projeto)}</div></div>`)}</div>`
        : html`<p class="sub">Orçamentos com status Enviado aparecem aqui até serem aprovados ou recusados.</p>`
    }
  </div>`;
}

function vista(): Safe {
  const p = dadosPainel;
  if (!p) return html`<div class="head"><div><h1>${eu.nome ? "Olá, " + primeiroNome(eu.nome) : "Painel"}</h1></div></div>${carregando("Carregando o painel…")}`;
  const h = hoje();
  const mesNome = MESES[p.mes - 1] ?? "";
  const escrever = podeEscrever();
  const comercial = temPermissao("comercial");
  return html`<div class="head"><div><h1>${eu.nome ? "Olá, " + primeiroNome(eu.nome) : "Painel"}</h1><p>Painel · ${mesNome} de ${p.ano}</p></div><div class="tools">${comercial ? botaoNovo("novoNegocio", "Novo negócio") : ""}</div></div>
  ${p.banco_vazio ? html`<div class="empty" style="margin-bottom:16px"><b>O Hub Comercial está pronto para receber os primeiros registros</b>Comece pelos produtos que a iSolutis vende, depois cadastre clientes e abra negócios no funil. O painel se preenche sozinho.<br>${escrever && comercial ? html`<button class="btn primary" data-go="produtos">Cadastrar produtos</button> <button class="btn" data-act="novoCliente">Cadastrar cliente</button>` : ""}</div>` : ""}
  ${vistaAlertas(p.alertas)}
  ${blocoFinanceiro(p, mesNome, h)}
  ${blocoComercial(p, h)}`;
}

registrarVista({
  id: "painel",
  nome: "Painel",
  carregar,
  depende: ["clientes", "negocios", "orcamentos", "faturamento", "despesas", "projetos"],
  desenhar: vista,
});
