import { api } from "@/api/endpoints";
import type { ItemEntrada, Orcamento, OrcamentoEntrada } from "@/api/tipos";
import { $ } from "@/core/dom";
import { brl, dataBR, hoje } from "@/core/formato";
import { esc, html, raw, type Safe } from "@/core/html";
import { numero } from "@/core/numero";
import { ORC_STATUS, etapaNome } from "@/domain/constantes";
import { textoWhatsapp, totais, type ItemDigitado } from "@/domain/orcamento";
import { ICONE_WA, numeroWa, urlWa } from "@/domain/whatsapp";
import { dados, podeEscrever, ui } from "@/state/estado";
import { recarregar, registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco, ligarNovoCliente, resolverCliente, seletorCliente } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { avisar, toast } from "@/ui/toast";
import { botaoNovo } from "./comum";
import { abrirFormulario, registrarFormulario } from "./ponte";

registrarConsulta("orcamentos", (id) => dados.orcamentos.find((o) => o.id === id));

function vista(): Safe {
  const filtro = ui.orcStatus;
  const lista = dados.orcamentos.filter((o) => filtro === "todos" || o.status_exibido === filtro);
  const segs: Array<[string, string]> = [["todos", "Todos"], ...Object.entries(ORC_STATUS).map(([k, v]): [string, string] => [k, v[0]])];
  return html`<div class="head"><div><h1>Orçamentos gerados</h1><p>Monte o orçamento com os produtos cadastrados, baixe o documento para enviar e registre a resposta do cliente.</p></div>
    <div class="tools"><div class="seg" role="group" aria-label="Filtrar por status">${segs.map(([k, r]) => html`<button data-act="filtroOrc" data-valor="${k}" aria-pressed="${filtro === k}">${r}</button>`)}</div>${botaoNovo("novoOrcamento", "Novo orçamento")}</div></div>
  ${
    !dados.orcamentos.length
      ? html`<div class="empty"><b>Nenhum orçamento gerado</b>O orçamento separa o valor do projeto e o valor da manutenção mensal. Quando o cliente aprova, o negócio vira Ganho e o faturamento é lançado.${podeEscrever() ? html`<br><button class="btn primary" data-act="novoOrcamento">Gerar o primeiro orçamento</button>` : ""}</div>`
      : html`<div class="tbl-wrap"><table><thead><tr><th>Nº</th><th>Cliente</th><th>Data</th><th>Status</th><th class="r">Projeto</th><th class="r">Mensal</th></tr></thead><tbody>
    ${lista.map((o) => {
      const [rot, cls] = ORC_STATUS[o.status_exibido] ?? ["", ""];
      const neg = dados.negocios.find((n) => n.id === o.negocio_id);
      return html`<tr tabindex="0" data-open="orcamento:${o.id}"><td class="num"><b>${o.numero}</b></td><td>${o.cliente_nome}${neg ? html`<div class="sub">${neg.titulo}</div>` : ""}</td><td class="num">${dataBR(o.data)}</td>
        <td><span class="pill ${cls}">${rot}</span></td><td class="r num">${brl(o.total_projeto)}</td><td class="r num">${o.total_mensal ? brl(o.total_mensal) : "—"}</td></tr>`;
    })}
    ${!lista.length ? html`<tr><td colspan="6" class="sub">Nenhum orçamento com esse status.</td></tr>` : ""}
  </tbody></table></div>`
  }`;
}

registrarVista({ id: "orcamentos", nome: "Orçamentos", contagem: () => dados.orcamentos.length, desenhar: vista });

const itemVazio = (): ItemDigitado & { id?: string; produto_id: string } => ({ produto_id: "", descricao: "", qtd: 1, preco_unitario: 0, mensal: false });
type ItemTela = ReturnType<typeof itemVazio>;

export function formOrcamento(inicial: Partial<OrcamentoEntrada> = {}, existente?: Orcamento): void {
  let atual = existente;
  const o = existente;
  const itens: ItemTela[] = (o?.itens ?? []).map((i) => ({ id: i.id, produto_id: i.produto_id ?? "", descricao: i.descricao, qtd: i.qtd, preco_unitario: i.preco_unitario, mensal: i.mensal }));
  if (!itens.length) itens.push(itemVazio());
  const prods = dados.produtos.filter((p) => p.ativo);
  const status = o?.status ?? inicial.status ?? "rascunho";
  const clienteInicial = o?.cliente_id ?? inicial.cliente_id ?? "";
  const negocioInicial = o?.negocio_id ?? inicial.negocio_id ?? "";
  const podeAprovar = !!o && podeEscrever() && o.status !== "aprovado";

  abrirGaveta({
    titulo: o ? `Orçamento Nº ${o.numero}` : "Novo orçamento",
    registro: o ? { recurso: "orcamentos", id: o.id, versao: o.versao } : null,
    autoria: linhaAutoria(o),
    corpo: html`<div class="fields">
      ${campo("Número", raw(`<input value="${esc(o?.numero ?? "Gerado ao salvar")}" readonly aria-readonly="true">`))}${campo("Status", sel("status", Object.entries(ORC_STATUS).filter(([k]) => k !== "vencido").map(([k, v]) => [k, v[0]] as const), status))}
      ${seletorCliente(clienteInicial)}<div class="field"><label for="f-negocio_id">Negócio</label><select name="negocio_id" id="f-negocio_id"></select></div>
      ${campo("Data", inp("data", o?.data ?? inicial.data ?? hoje(), 'type="date"'))}${campo("Validade (dias)", inp("validade_dias", o?.validade_dias ?? inicial.validade_dias ?? 15, 'type="number" min="1"'))}
    </div>
    <div><h2 style="margin-bottom:6px">Itens</h2>${!prods.length ? html`<p class="sub" style="margin:0 0 6px">Cadastre produtos para preencher os itens com um clique. Você também pode digitar a descrição livremente.</p>` : ""}
      <div style="overflow-x:auto"><table class="items" style="min-width:560px"><thead><tr><th style="width:30%">Produto</th><th>Descrição</th><th style="width:60px">Qtd</th><th style="width:110px">Valor unit.</th><th style="width:54px">Mensal</th><th style="width:30px"></th></tr></thead><tbody id="itens"></tbody></table></div>
      <button class="btn" type="button" id="addItem" style="margin-top:8px">Adicionar item</button></div>
    <div class="fields">${campo("Desconto no projeto (R$)", inp("desconto", o?.desconto ? String(o.desconto).replace(".", ",") : "", 'inputmode="decimal" placeholder="0,00"'))}<div class="totals" id="totais"></div>
      ${campo("Condições e observações", area("obs", o?.obs ?? inicial.obs, "Forma de pagamento, prazo de entrega, o que está fora do escopo…"), true)}</div>`,
    rodape: html`${botaoSalvar()}<a class="btn wa" id="waOrc" target="_blank" rel="noopener" href="#">${ICONE_WA}Enviar pelo WhatsApp</a>${podeAprovar ? html`<button class="btn" data-aprovar>Cliente aprovou</button>` : ""}${o ? html`<button class="btn" data-baixar>Baixar orçamento</button>` : html`<button class="btn" data-baixar>Salvar e baixar</button>`}${espaco}${botaoExcluir(!!o)}`,
    montar: (f, fechar, L) => {
      ligarNovoCliente(f);
      const clienteSel = f.elements.namedItem("cliente_id") as HTMLSelectElement;
      const negSel = f.elements.namedItem("negocio_id") as HTMLSelectElement;
      const popularNegocios = (): void => {
        const ns = dados.negocios.filter((n) => n.cliente_id === clienteSel.value);
        negSel.innerHTML = String(html`<option value="">Sem negócio vinculado</option>${ns.map((n) => html`<option value="${n.id}"${raw(n.id === negocioInicial ? " selected" : "")}>${n.titulo} (${etapaNome(n.etapa)})</option>`)}`);
      };
      popularNegocios();
      clienteSel.addEventListener("change", popularNegocios);

      const tb = $("#itens", L) as HTMLElement;
      const desconto = () => numero(fv(f, "desconto"));
      const mostrarTotais = (): void => {
        const t = totais(itens, desconto());
        $("#totais", L)!.innerHTML = String(html`<span class="sub">Projeto</span><span class="big num">${brl(t.projeto)}</span>${t.mensal ? html`<span class="sub">Manutenção mensal</span><span class="num" style="font-weight:600">${brl(t.mensal)}/mês</span>` : ""}`);
      };
      const desenhar = (): void => {
        tb.innerHTML = String(
          html`${itens.map(
            (it, i) => html`<tr data-i="${i}">
          <td><select data-k="produto_id" aria-label="Produto"><option value="">Livre</option>${prods.map((p) => html`<option value="${p.id}"${raw(p.id === it.produto_id ? " selected" : "")}>${p.nome}</option>`)}</select></td>
          <td><input data-k="descricao" value="${it.descricao}" aria-label="Descrição"></td>
          <td><input data-k="qtd" value="${it.qtd}" inputmode="decimal" aria-label="Quantidade"></td>
          <td><input data-k="preco_unitario" value="${it.preco_unitario ? String(it.preco_unitario).replace(".", ",") : ""}" inputmode="decimal" placeholder="0,00" aria-label="Valor unitário"></td>
          <td style="text-align:center"><input type="checkbox" data-k="mensal"${raw(it.mensal ? " checked" : "")} aria-label="Cobrança mensal"></td>
          <td><button type="button" class="btn ghost" data-rm="${i}" aria-label="Remover item" style="padding:2px 6px">×</button></td></tr>`,
          )}`,
        );
        mostrarTotais();
      };
      const itemDe = (el: Element): ItemTela | undefined => itens[Number(el.closest<HTMLElement>("tr")?.dataset.i)];
      tb.addEventListener("input", (e) => {
        const el = e.target as HTMLInputElement;
        const k = el.dataset.k;
        const it = itemDe(el);
        if (!it || !k || k === "produto_id" || k === "mensal") return;
        if (k === "descricao") it.descricao = el.value;
        else if (k === "qtd") it.qtd = numero(el.value);
        else if (k === "preco_unitario") it.preco_unitario = numero(el.value);
        mostrarTotais();
      });
      tb.addEventListener("change", (e) => {
        const el = e.target as HTMLInputElement;
        const it = itemDe(el);
        if (!it) return;
        if (el.dataset.k === "mensal") {
          it.mensal = el.checked;
          mostrarTotais();
        }
        if (el.dataset.k === "produto_id") {
          const p = dados.produtos.find((x) => x.id === el.value);
          it.produto_id = el.value;
          if (p) {
            it.descricao = p.descricao ? `${p.nome} — ${p.descricao}` : p.nome;
            it.preco_unitario = numero(p.preco);
            it.mensal = p.tipo === "mensal";
          }
          desenhar();
        }
      });
      tb.addEventListener("click", (e) => {
        const b = (e.target as Element).closest<HTMLElement>("[data-rm]");
        if (!b) return;
        itens.splice(Number(b.dataset.rm), 1);
        if (!itens.length) itens.push(itemVazio());
        desenhar();
      });
      $("#addItem", L)?.addEventListener("click", () => {
        itens.push(itemVazio());
        desenhar();
      });
      (f.elements.namedItem("desconto") as HTMLInputElement).addEventListener("input", mostrarTotais);
      desenhar();

      // WhatsApp: o texto é montado com o que está na tela (mesmo antes de salvar)
      const wa = $<HTMLAnchorElement>("#waOrc", L)!;
      const atualizarWa = (): void => {
        const c = dados.clientes.find((x) => x.id === clienteSel.value);
        const ok = !!numeroWa(c?.telefone);
        wa.setAttribute("aria-disabled", String(!ok));
        wa.title = ok ? "Abre o WhatsApp com o orçamento escrito na mensagem" : c ? "Cadastre o WhatsApp deste cliente para enviar" : "Escolha um cliente com WhatsApp cadastrado";
        wa.href = ok ? urlWa(c?.telefone, textoWhatsapp({ numero: atual?.numero ?? null, data: fv(f, "data"), validade: numero(fv(f, "validade_dias")), desconto: desconto(), itens, obs: fv(f, "obs") }, c)) : "#";
      };
      atualizarWa();
      f.addEventListener("input", atualizarWa);
      f.addEventListener("change", atualizarWa);
      wa.addEventListener("pointerdown", atualizarWa);
      wa.addEventListener("focus", atualizarWa);
      wa.addEventListener("click", (e) => {
        atualizarWa();
        if (wa.getAttribute("aria-disabled") === "true") {
          e.preventDefault();
          toast(wa.title + ".");
          return;
        }
        const st = f.elements.namedItem("status") as HTMLSelectElement;
        if (st.value === "rascunho" && podeEscrever()) {
          st.value = "enviado";
          toast("Status mudou para Enviado. Clique em Salvar para registrar.");
        }
      });

      /** Valida a tela e monta o payload (null = faltou algo; já avisou). */
      const coletar = async (): Promise<OrcamentoEntrada | null> => {
        if (!fv(f, "cliente_id")) return avisar("Escolha o cliente do orçamento.");
        const validos = itens.filter((i) => i.descricao || numero(i.preco_unitario));
        if (!validos.length) return avisar("Inclua pelo menos um item.");
        const clienteId = await resolverCliente(f);
        if (!clienteId) return null;
        const lista: ItemEntrada[] = validos.map((i) => ({
          id: i.id ?? null, produto_id: i.produto_id || null, descricao: i.descricao || "Item", qtd: numero(i.qtd) || 1, preco_unitario: numero(i.preco_unitario), mensal: !!i.mensal,
        }));
        return {
          cliente_id: clienteId, negocio_id: negSel.value || null, data: fv(f, "data") || hoje(), validade_dias: numero(fv(f, "validade_dias")) || 15,
          status: fv(f, "status") as OrcamentoEntrada["status"], desconto: desconto(), obs: fv(f, "obs") || null, itens: lista,
        };
      };
      /** Grava (cria ou atualiza) sem fechar; devolve o orçamento salvo. */
      const persistir = async (corpo: OrcamentoEntrada, mensagem: string): Promise<Orcamento | null> => {
        const salvo = await gravar({
          recarregar: ["orcamentos", "negocios", "clientes"], mensagem,
          operacao: () => (atual ? api.orcamentos.atualizar(atual.id, { ...corpo, versao: atual.versao }) : api.orcamentos.criar(corpo)),
        });
        if (salvo) {
          atual = salvo;
          itens.splice(0, itens.length, ...salvo.itens.map((i) => ({ id: i.id, produto_id: i.produto_id ?? "", descricao: i.descricao, qtd: i.qtd, preco_unitario: i.preco_unitario, mensal: i.mensal })));
          const num = $<HTMLInputElement>("input[readonly]", f);
          if (num) num.value = salvo.numero;
        }
        return salvo;
      };

      $("[data-salvar]", L)?.addEventListener("click", async () => {
        const corpo = await coletar();
        if (corpo && (await persistir(corpo, `Orçamento salvo`))) fechar();
      });
      $("[data-aprovar]", L)?.addEventListener("click", async () => {
        const corpo = await coletar();
        if (!corpo) return;
        const salvo = await persistir(corpo, "");
        if (!salvo) return;
        const r = await tentar(() => api.orcamentos.aprovar(salvo.id));
        if (!r) return;
        await recarregar("orcamentos", "negocios");
        toast("Orçamento aprovado");
        fechar();
        abrirFormulario("faturamento", {
          cliente_id: r.orcamento.cliente_id, titulo: "Orçamento " + r.orcamento.numero, unico: r.orcamento.total_projeto, mensal: r.orcamento.total_mensal,
          negocio_id: r.negocio_id, orcamento_id: r.orcamento.id,
        });
      });
      $("[data-baixar]", L)?.addEventListener("click", async () => {
        const corpo = await coletar();
        if (!corpo) return;
        const salvo = await persistir(corpo, "");
        if (!salvo) return;
        if ((await tentar(() => api.orcamentos.baixar(salvo.id))) !== null) toast("Orçamento salvo e baixado. Abra no navegador e use Imprimir → Salvar como PDF.");
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (o) void excluir({ recarregar: ["orcamentos", "clientes"], mensagem: "Orçamento excluído", fechar, operacao: () => api.orcamentos.excluir(o.id) });
      });

    },
  });
}

registrarFormulario("orcamento", (inicial) => formOrcamento(inicial));
registrarAcao("novoOrcamento", () => formOrcamento());
registrarAcao("filtroOrc", (alvo) => {
  ui.orcStatus = alvo.dataset.valor ?? "todos";
  render();
});
registrarAbertura("orcamento", (id) => {
  const o = dados.orcamentos.find((x) => x.id === id);
  if (o) formOrcamento({}, o);
});

