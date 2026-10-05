import { api } from "@/api/endpoints";
import type { Lancamento, LancamentoEntrada, ResumoFaturamento } from "@/api/tipos";
import { $ } from "@/core/dom";
import { MES3, MESES, brl, dataBR, hoje, addMeses } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { numero, paraCampo } from "@/core/numero";
import { OPCOES_REPETICAO, TIPOS } from "@/domain/constantes";
import { dados, podeEscrever, ui } from "@/state/estado";
import { recarregar, registrarVista } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco, ligarNovoCliente, resolverCliente, seletorCliente } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { avisar, toast } from "@/ui/toast";
import { melhorarFormulario } from "@/ui/acessibilidade";
import { botaoNovo } from "./comum";
import { graficoFaturamento, legendaFaturamento } from "./grafico";
import { registrarFormulario, type VendaFechada } from "./ponte";

/** Dados da tela (por ano): resumo mensal calculado no servidor e a lista de lançamentos. */
const pagina: { ano: number; resumo: ResumoFaturamento | null; lancamentos: Lancamento[] } = { ano: 0, resumo: null, lancamentos: [] };

registrarConsulta("faturamento", (id) => pagina.lancamentos.find((l) => l.id === id));

async function carregar(): Promise<void> {
  const ano = ui.ano;
  const [resumo, lancamentos] = await Promise.all([api.faturamento.resumo(ano), api.faturamento.listar(ano)]);
  if (ano !== ui.ano) return; // a pessoa trocou de ano enquanto carregava
  Object.assign(pagina, { ano, resumo, lancamentos });
}

function vista(): Safe {
  const r = pagina.resumo;
  if (!r || pagina.ano !== ui.ano) return html`<div class="head"><div><h1>Faturamento mês a mês</h1></div></div><p class="sub">Carregando…</p>`;
  const ano = ui.ano;
  const mesAtual = new Date().getFullYear() === ano ? new Date().getMonth() + 1 : 0;
  const lista = pagina.lancamentos.filter((l) => !ui.mes || Number(l.vencimento.slice(5, 7)) === ui.mes);
  let acumulado = 0;
  const escrever = podeEscrever();
  return html`<div class="head"><div><h1>Faturamento mês a mês</h1><p>Recebido em ${ano}: <b class="num">${brl(r.total_recebido)}</b> · ainda previsto: <b class="num">${brl(r.total_previsto)}</b></p></div>
    <div class="tools"><div class="field" style="flex-direction:row;align-items:center;gap:6px"><label for="ano">Ano</label><select id="ano" data-act="mudarAno">${r.anos_disponiveis.map((a) => html`<option${a === ano ? " selected" : ""}>${a}</option>`)}</select></div>
    ${pagina.lancamentos.length ? html`<button class="btn" data-act="csv">Baixar planilha (.csv)</button>` : ""}${botaoNovo("novoLanc", "Novo lançamento")}</div></div>
  <div class="panel chart" style="margin-bottom:16px">${graficoFaturamento(r.meses.map((m) => ({ rotulo: MES3[m.mes - 1] ?? "", recebido: m.recebido, previsto: m.previsto, atual: m.mes === mesAtual })))}${legendaFaturamento}</div>
  <div class="two">
    <div class="tbl-wrap"><table style="min-width:480px"><thead><tr><th>Mês</th><th class="r">Recebido</th><th class="r">Previsto</th><th class="r">Recorrente</th><th class="r">Acumulado</th></tr></thead><tbody>
      ${r.meses.map((m) => {
        acumulado += m.recebido + m.previsto;
        return html`<tr tabindex="0" data-act="mes" data-valor="${m.mes}" style="${ui.mes === m.mes ? "background:var(--gold-soft)" : ""}"><td>${MESES[m.mes - 1]}${m.mes === mesAtual ? html` <span class="pill gold">atual</span>` : ""}</td><td class="r num">${m.recebido ? brl(m.recebido) : "—"}</td><td class="r num">${m.previsto ? brl(m.previsto) : "—"}</td><td class="r num">${m.recorrente ? brl(m.recorrente) : "—"}</td><td class="r num sub">${brl(acumulado)}</td></tr>`;
      })}
    </tbody><tfoot><tr><td>Total ${ano}</td><td class="r num">${brl(r.total_recebido)}</td><td class="r num">${brl(r.total_previsto)}</td><td class="r num">${brl(r.total_recorrente)}</td><td class="r num">${brl(r.total_recebido + r.total_previsto)}</td></tr></tfoot></table></div>
    <div class="panel"><h2>${ui.mes ? html`Lançamentos de ${MESES[ui.mes - 1]?.toLowerCase()} <button class="btn ghost" data-act="limparMes">ver o ano todo</button>` : `Lançamentos de ${ano}`}</h2>
      ${
        lista.length
          ? html`<div class="list">${lista.map(
              (l) => html`<div class="li" data-open="lanc:${l.id}" tabindex="0"><div><div class="t">${l.cliente_nome}</div><div class="sub">${dataBR(l.vencimento)} · ${l.descricao || TIPOS[l.tipo] || ""}</div></div>
              <div style="text-align:right"><div class="num">${brl(l.valor)}</div>${l.status === "recebido" ? html`<span class="pill ok">Recebido</span>` : html`<span class="pill">Previsto</span>${escrever ? html` <button class="btn ghost" data-act="receber" data-id="${l.id}" style="padding:0 4px;font-size:12px">marcar recebido</button>` : ""}`}</div></div>`,
            )}</div>`
          : html`<p class="sub">Nenhum lançamento ${ui.mes ? "neste mês" : "neste ano"}. Os lançamentos entram quando um orçamento é aprovado, quando um negócio é ganho, ou pelo botão Novo lançamento.</p>`
      }
    </div>
  </div>`;
}

registrarVista({ id: "faturamento", nome: "Faturamento", carregar, depende: ["faturamento", "negocios"], desenhar: vista });

function formLanc(l?: Lancamento): void {
  abrirGaveta({
    titulo: l ? "Lançamento" : "Novo lançamento",
    registro: l ? { recurso: "faturamento", id: l.id, versao: l.versao } : null,
    autoria: linhaAutoria(l),
    corpo: html`<div class="fields">
      ${seletorCliente(l?.cliente_id)}${campo("Tipo", sel("tipo", Object.entries(TIPOS), l?.tipo ?? "projeto"))}
      ${campo("Descrição", inp("descricao", l?.descricao, 'placeholder="Ex.: Parcela 1/2 do portal do cliente"'), true)}
      ${campo("Valor (R$)", inp("valor", paraCampo(l?.valor), 'inputmode="decimal" placeholder="0,00"'))}${campo("Data de vencimento", inp("vencimento", l?.vencimento ?? hoje(), 'type="date"'))}
      ${campo("Situação", sel("status", [["previsto", "Previsto"], ["recebido", "Recebido"]], l?.status ?? "previsto"))}
      ${l ? "" : campo("Repetir todo mês por", sel("repetir", OPCOES_REPETICAO.map((n) => [n, n === 1 ? "Não repetir" : `${n} meses`] as const), 1))}
      ${campo("Nota fiscal / observação", inp("nf", l?.nf), true)}</div>`,
    rodape: html`${botaoSalvar()}${espaco}${botaoExcluir(!!l)}`,
    montar: (f, fechar, L) => {
      melhorarFormulario(f);
      ligarNovoCliente(f);
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;
        const textoOriginal = botao.textContent;

        // Validação
        if (!fv(f, "cliente_id")) {
          toast("Escolha o cliente.");
          return;
        }
        if (!numero(fv(f, "valor"))) {
          toast("Informe o valor.");
          return;
        }

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        botao.innerHTML = '<span class="spinner"></span> Salvando…';

        try {
          const clienteId = await resolverCliente(f);
          if (!clienteId) {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Salvar";
            return;
          }
          const base = {
            cliente_id: clienteId, tipo: fv(f, "tipo") as LancamentoEntrada["tipo"], descricao: fv(f, "descricao") || TIPOS[fv(f, "tipo")] || "Lançamento",
            valor: numero(fv(f, "valor")), vencimento: fv(f, "vencimento") || hoje(), status: fv(f, "status") as LancamentoEntrada["status"], nf: fv(f, "nf") || null,
          };
          const repetir = Number(fv(f, "repetir")) || 1;
          await gravar({
            recarregar: ["faturamento", "clientes"], fechar,
            mensagem: l ? "Lançamento salvo" : repetir > 1 ? `${repetir} lançamentos criados` : "Lançamento criado",
            operacao: async () => (l ? await api.faturamento.atualizar(l.id, { ...base, versao: l.versao }) : await api.faturamento.criar({ ...base, repetir })),
          });
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Salvar";
        }
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (l) void excluir({ recarregar: ["faturamento", "clientes"], mensagem: "Lançamento excluído", fechar, operacao: () => api.faturamento.excluir(l.id) });
      });
    },
  });
}

/** Venda fechada (negócio ganho / orçamento aprovado): lança as parcelas do projeto e as mensalidades de uma vez. */
function gerarFaturamento(g: VendaFechada): void {
  if (!podeEscrever()) return;
  const h = hoje();
  const cliente = dados.clientes.find((c) => c.id === g.cliente_id);
  abrirGaveta({
    titulo: "Lançar faturamento",
    corpo: html`<p style="margin:0">Venda fechada com <b>${cliente?.nome ?? "—"}</b>${g.titulo ? " · " + g.titulo : ""}. Confira como o valor entra no faturamento.</p>
    <div class="gen"><label class="check"><input type="checkbox" name="usaUnico" id="f-usaUnico"${g.unico ? " checked" : ""}> Projeto</label>
      <div class="fields">${campo("Valor total (R$)", inp("unico", paraCampo(g.unico), 'inputmode="decimal"'))}${campo("Parcelas", inp("parcelas", 1, 'type="number" min="1" max="24"'))}${campo("Primeiro vencimento", inp("dataU", h, 'type="date"'))}</div></div>
    <div class="gen"><label class="check"><input type="checkbox" name="usaMensal" id="f-usaMensal"${g.mensal ? " checked" : ""}> Manutenção mensal</label>
      <div class="fields">${campo("Valor por mês (R$)", inp("mensal", paraCampo(g.mensal), 'inputmode="decimal"'))}${campo("Quantos meses lançar", inp("meses", 12, 'type="number" min="1" max="36"'))}${campo("Primeira mensalidade", inp("dataM", addMeses(h, 1), 'type="date"'))}</div></div>
    <p class="sub" id="resumoGen" style="margin:0"></p>`,
    rodape: html`<button class="btn primary" data-salvar>Lançar no faturamento</button><button class="btn" data-fechar>Agora não</button>`,
    montar: (f, fechar, L) => {
      melhorarFormulario(f);
      const marcado = (n: string): boolean => (f.elements.namedItem(n) as HTMLInputElement).checked;
      const plano = (): Pick<Parameters<typeof api.faturamento.lote>[0], "projeto" | "mensal"> => ({
        projeto: marcado("usaUnico") && numero(fv(f, "unico")) ? { valor: numero(fv(f, "unico")), parcelas: Math.max(1, Math.round(numero(fv(f, "parcelas")))), primeiro_vencimento: fv(f, "dataU") || h } : null,
        mensal: marcado("usaMensal") && numero(fv(f, "mensal")) ? { valor: numero(fv(f, "mensal")), meses: Math.max(1, Math.round(numero(fv(f, "meses")))), primeira_mensalidade: fv(f, "dataM") || h } : null,
      });
      const resumir = (): void => {
        const { projeto, mensal } = plano();
        const partes: string[] = [];
        if (projeto) partes.push(`${projeto.parcelas}× ${brl(numero(projeto.valor) / projeto.parcelas)} de projeto`);
        if (mensal) partes.push(`${mensal.meses} mensalidades de ${brl(mensal.valor)}`);
        $("#resumoGen", L)!.textContent = partes.length ? "Serão criados: " + partes.join(" e ") + ", todos como Previsto." : "Nada marcado para lançar.";
      };
      f.addEventListener("input", resumir);
      resumir();
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const { projeto, mensal } = plano();
        if (!projeto && !mensal) return void avisar("Nada marcado para lançar.");
        const botao = e.target as HTMLButtonElement;
        const textoOriginal = botao.textContent;

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        botao.innerHTML = '<span class="spinner"></span> Lançando…';

        try {
          const criados = await gravar({
            recarregar: ["faturamento", "negocios", "clientes"], mensagem: "", fechar,
            operacao: () => api.faturamento.lote({ cliente_id: g.cliente_id, titulo: g.titulo, negocio_id: g.negocio_id ?? null, orcamento_id: g.orcamento_id ?? null, projeto, mensal }),
          });
          if (criados) toast(`${criados.length} ${criados.length === 1 ? "lançamento criado" : "lançamentos criados"}`);
          else {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Lançar no faturamento";
          }
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Lançar no faturamento";
        }
      });
    },
  });
}

registrarFormulario("faturamento", gerarFaturamento);
registrarAcao("novoLanc", () => formLanc());
registrarAcao("receber", async (alvo) => {
  const id = alvo.dataset.id;
  if (!id) return;
  if ((await tentar(() => api.faturamento.receber(id))) !== null) {
    await recarregar("faturamento", "clientes");
    toast("Marcado como recebido");
  }
});
registrarAcao("csv", async () => {
  if ((await tentar(() => api.faturamento.exportar(ui.ano))) === null) toast("Não foi possível baixar a planilha agora.");
});
registrarAbertura("lanc", (id) => {
  const l = pagina.lancamentos.find((x) => x.id === id);
  if (l) formLanc(l);
});
