import { $, $$ } from "@/core/dom";
import { brl, dataBR, hoje } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { numero } from "@/core/numero";
import { gravarConsulta } from "@/state/consulta-url";
import { recarregarVista, registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, inpMoeda, sel } from "@/ui/campos";
import { chipsDeFiltro as chipsDeFiltroUi } from "@/ui/chips-filtro";
import { combobox, comboboxDe, type OpcaoCombobox } from "@/ui/combobox";
import { estadoDeErro } from "@/ui/componentes";
import { paginacao } from "@/ui/paginacao";
import { tentar } from "@/ui/erros";
import { abrirGaveta } from "@/ui/gaveta";
import { espaco } from "@/ui/formularios";
import { gravar } from "@/ui/gravacao";
import { avisar } from "@/ui/toast";
import { apiFinanceiro, type ContaBancaria, type PaginaTitulos, type Parceiro, type PlanoConta, type Titulo, type TituloEntrada } from "./api";
import { acoesDaLinha, confirmarExclusao, contasDoPlanoParaTitulo, GRUPO, parceirosParaTitulo } from "./comum";
import { opcaoDaConta, prepararCadastroDeConta } from "./contas-bancarias";
import {
  aplicarAtalho, atalhoAtivo, chipsDeFiltro, contarAvancados, FILTROS_AVANCADOS, filtrosDaApi, lerConsultaTitulos, limparChaves, PADROES_TITULOS, TAMANHOS_DE_PAGINA, ultimaPagina, valorParaConsulta,
  type Atalho, type ConsultaTitulos, type NomesDeApoio,
} from "./titulos-consulta";
import { opcaoDoParceiro, prepararCadastroDeParceiro } from "../parceiros/cadastro-rapido";

const STATUS: Record<string, readonly [string, string]> = { A: ["Aberto", "info"], Q: ["Quitado", "ok"], C: ["Cancelado", ""] };
const TIPO: Record<string, string> = { P: "A pagar", R: "A receber" };

interface Apoio {
  parceiros: Parceiro[];
  plano: PlanoConta[];
  contas: ContaBancaria[];
}
const tela: { pagina: PaginaTitulos | null; consulta: ConsultaTitulos; apoio: Apoio | null; falhou: boolean } = {
  pagina: null,
  consulta: { ...PADROES_TITULOS },
  apoio: null,
  falhou: false,
};
/** Só a resposta da última consulta vale (uma busca digitada depressa não pode ser sobrescrita por outra mais lenta). */
let consultaEmCurso = 0;

const nomeDe = <T extends { id: string }>(lista: readonly T[] | undefined, id: string, rotulo: (x: T) => string): string => {
  const x = lista?.find((i) => i.id === id);
  return x ? rotulo(x) : "…";
};
const NOMES: NomesDeApoio = {
  parceiro: (id) => nomeDe(tela.apoio?.parceiros, id, (p) => p.nome),
  plano: (id) => nomeDe(tela.apoio?.plano, id, (c) => `${c.codigo} ${c.nome}`),
  conta: (id) => nomeDe(tela.apoio?.contas, id, (c) => c.nome),
};

/** Listas de apoio (parceiros, plano e contas) para a gaveta e para os nomes dos chips; buscadas na hora, sem cache. */
const buscarApoio = async (): Promise<Apoio> => {
  const [parceiros, plano, contas] = await Promise.all([apiFinanceiro.parceiros.listar(), apiFinanceiro.plano.listar(), apiFinanceiro.contas.listar()]);
  return { parceiros, plano, contas };
};

/** Busca a página da consulta atual; se ela ficou além do fim (exclusão, filtro mais estreito), recua para a última. */
async function buscarPagina(): Promise<void> {
  const minha = ++consultaEmCurso;
  const pedir = (c: ConsultaTitulos): Promise<PaginaTitulos> => apiFinanceiro.titulos.listar({ ...filtrosDaApi(c), pagina: Number(c.pag), tamanho: Number(c.tam) });
  const c = tela.consulta;
  let pagina = await pedir(c);
  const ultima = ultimaPagina(pagina.total, Number(c.tam));
  let consulta = c;
  if (Number(c.pag) > ultima) {
    consulta = { ...c, pag: String(ultima) };
    pagina = await pedir(consulta);
  }
  if (minha !== consultaEmCurso) return;
  if (consulta !== c) {
    tela.consulta = consulta;
    gravarConsulta(PADROES_TITULOS, consulta, "replace");
  }
  tela.pagina = pagina;
  tela.falhou = false;
}

/** Ao abrir a tela (e quando o servidor avisa de mudanças): o estado vem da URL. */
async function carregar(): Promise<void> {
  tela.consulta = lerConsultaTitulos(location.search);
  const c = tela.consulta;
  const precisaDeNomes = !tela.apoio && !!(c.parceiro || c.plano || c.conta);
  try {
    await Promise.all([buscarPagina(), precisaDeNomes ? buscarApoio().then((a) => void (tela.apoio = a)) : undefined]);
  } catch (e) {
    tela.falhou = true;
    throw e;
  }
}

/** Troca a consulta, grava na URL (`push` só ao mudar de página) e busca de novo. */
async function aplicar(nova: ConsultaTitulos, modo: "push" | "replace" = "replace"): Promise<void> {
  tela.consulta = nova;
  gravarConsulta(PADROES_TITULOS, nova, modo);
  render();
  await tentar(async () => {
    await buscarPagina();
    if (!tela.apoio && (nova.parceiro || nova.plano || nova.conta)) tela.apoio = await buscarApoio();
  });
  render();
}

const mudar = (campos: Partial<ConsultaTitulos>, modo: "push" | "replace" = "replace"): Promise<void> => aplicar({ ...tela.consulta, pag: "1", ...campos }, modo);

function vista(): Safe {
  const c = tela.consulta;
  const cabeca = (descricao: Safe | string): Safe => html`<div class="head"><div><h1>Títulos financeiros</h1><p>${descricao}</p></div>
    <div class="tools"><button class="btn" data-act="novaRecorrencia">Nova recorrência</button><button class="btn primary" data-act="novoTitulo">Novo título</button></div></div>`;
  if (!tela.pagina) {
    return tela.falhou
      ? html`${cabeca("Contas a pagar e a receber")}${estadoDeErro({ mensagem: "Não foi possível carregar os títulos.", acaoRepetir: "finRecarregar" })}`
      : html`<div class="head"><div><h1>Títulos financeiros</h1></div></div><p class="sub">Carregando…</p>`;
  }
  const { itens, total, totais } = tela.pagina;
  const h = hoje();
  const chips = chipsDeFiltro(c, NOMES);
  const filtrado = chips.length > 0 || c.tipo !== "todos" || c.status !== "todos";
  const nAvancados = contarAvancados(c);
  const atalho = atalhoAtivo(c, h);
  const seg = (acao: string, atual: string, opcoes: Array<[string, string]>): Safe =>
    html`<div class="seg" role="group">${opcoes.map(([k, r]) => html`<button data-act="${acao}" data-valor="${k}" aria-pressed="${atual === k}">${r}</button>`)}</div>`;
  const ordenavel = (chave: string, rotulo: string, classe = ""): Safe => {
    const ativa = c.ordem === chave;
    return html`<th class="${classe}" aria-sort="${ativa ? (c.sentido === "asc" ? "ascending" : "descending") : "none"}"><button type="button" class="th-ordem" data-act="finOrdenar" data-valor="${chave}">${rotulo}<span aria-hidden="true">${ativa ? (c.sentido === "asc" ? " ▲" : " ▼") : ""}</span></button></th>`;
  };
  const resumo = html`${filtrado ? "No filtro" : "Em aberto"}: <b class="num">${brl(totais.a_receber)}</b> a receber, <b class="num">${brl(totais.a_pagar)}</b> a pagar em aberto`;
  return html`${cabeca(html`Contas a pagar e a receber · ${resumo}`)}
  <div class="fin-filtros">${seg("filtroFinTipo", c.tipo, [["todos", "Todos"], ["R", "A receber"], ["P", "A pagar"]])}${seg("filtroFinStatus", c.status, [["todos", "Todos"], ["A", "Abertos"], ["Q", "Quitados"], ["C", "Cancelados"]])}
    <button type="button" class="chip" data-act="finAtalho" data-valor="atrasados" aria-pressed="${atalho === "atrasados"}">Atrasados</button>
    <button type="button" class="chip" data-act="finAtalho" data-valor="semana" aria-pressed="${atalho === "semana"}">Vence nos próximos 7 dias</button>
    <input class="search" type="search" data-fin-busca aria-label="Buscar por parceiro" placeholder="Buscar por parceiro" value="${c.q}">
    <button type="button" class="btn" data-act="finFiltros" aria-haspopup="dialog">${nAvancados ? `Filtros (${nAvancados})` : "Filtros"}</button>
    <button type="button" class="btn" data-act="finExportar"${total ? "" : " disabled"}>Exportar CSV</button></div>
  ${chipsDeFiltroUi({ rotulos: chips.map((x) => x.rotulo), acaoRemover: "finRemoverChip", acaoLimpar: "finLimparChips" })}
  ${
    total || filtrado
      ? html`<div class="tbl-wrap"><table style="min-width:860px"><thead><tr>${ordenavel("vencimento", "Vencimento")}<th>Tipo</th>${ordenavel("parceiro", "Parceiro")}<th>Conta do plano</th><th>Conta bancária</th>${ordenavel("valor", "Valor devido", "r")}<th>Situação</th><th></th></tr></thead><tbody>
      ${itens.map((t) => {
        const [rot, cls] = STATUS[t.status] ?? ["", ""];
        const atrasado = t.status === "A" && t.data_vencimento < h;
        return html`<tr><td class="num">${dataBR(t.data_vencimento)}${atrasado ? html`<div class="sub" style="color:var(--bad-texto)">atrasado</div>` : ""}</td><td><span class="pill ${t.tipo_conta === "R" ? "ok" : "bad"}">${TIPO[t.tipo_conta]}</span></td>
        <td><b>${t.parceiro_nome}</b>${t.recorrencia_id ? html` <a class="pill info" href="/fin-recorrencias" data-go="fin-recorrencias" title="Título gerado por uma recorrência">Recorrente</a>` : ""}</td><td><span class="num sub">${t.plano_conta_codigo}</span> ${t.plano_conta_nome}</td><td>${t.conta_bancaria_nome}</td>
        <td class="r num">${brl(t.valor_devido)}${t.status === "Q" && t.valor_quitacao !== t.valor_devido ? html`<div class="sub">pago ${brl(t.valor_quitacao)}</div>` : ""}</td><td><span class="pill ${cls}">${rot}</span>${t.data_pagamento ? html`<div class="sub num">${dataBR(t.data_pagamento)}</div>` : ""}</td><td class="r">${acoesDaLinha("titulo", t.id)}</td></tr>`;
      })}
      ${!itens.length ? html`<tr><td colspan="8" class="sub">Nenhum título com esses filtros.</td></tr>` : ""}
    </tbody></table></div>
    ${paginacao({ pagina: Number(c.pag), tamanho: Number(c.tam), total, tamanhos: TAMANHOS_DE_PAGINA, acaoPagina: "finPagina", acaoTamanho: "finTamanho" })}`
      : html`<div class="empty"><b>Nenhum título lançado</b>Antes de lançar, cadastre o plano de contas, uma conta bancária e o parceiro.<br><button class="btn primary" data-act="novoTitulo">Lançar o primeiro título</button></div>`
  }`;
}

registrarVista({ id: "fin-titulos", nome: "Títulos Financeiros", grupo: GRUPO, permissao: "financeiro", carregar, depende: ["financeiro"], desenhar: vista });

async function formTitulo(t?: Titulo): Promise<void> {
  // as listas de apoio são buscadas na hora, para refletir cadastros feitos há pouco
  const apoio = await tentar(() =>
    Promise.all([apiFinanceiro.plano.listar(), apiFinanceiro.contas.listar(), apiFinanceiro.parceiros.listar(), prepararCadastroDeParceiro(), prepararCadastroDeConta()]),
  );
  if (!apoio) return;
  const [plano, contas, parceiros]: [PlanoConta[], ContaBancaria[], Parceiro[], void, void] = apoio;
  const tipoInicial = t?.tipo_conta ?? "R";
  /** RN04: contas a pagar mostram só despesas; a receber, só receitas. */
  const contasDoTipo = (tipo: string): PlanoConta[] => contasDoPlanoParaTitulo(plano, tipo);
  const nomeDoPlano = new Map(plano.map((c) => [c.id, `${c.codigo} ${c.nome}`]));
  const opcoesPlano = (tipo: string): OpcaoCombobox[] =>
    contasDoTipo(tipo).map((c) => ({ id: c.id, codigo: c.codigo, rotulo: c.nome, grupo: c.plano_pai_id ? nomeDoPlano.get(c.plano_pai_id) : undefined }));
  const campoPlano = (tipo: string, atual?: string | null): Safe =>
    combobox({ nome: "plano_conta_id", rotulo: "Conta do plano de contas", opcoes: opcoesPlano(tipo), valor: atual, vazio: contasDoTipo(tipo).length ? "Digite para buscar…" : "Nenhuma conta disponível" });

  /** Parceiros do tipo de título e da conta escolhidos (a conta de aporte só aceita sócios); o atual sempre fica na lista. */
  const opcoesParceiro = (tipo: string, planoId: string, atual?: string): OpcaoCombobox[] => {
    const aporte = plano.find((c) => c.id === planoId)?.aporte_socio ?? false;
    const lista = parceirosParaTitulo(parceiros, tipo, aporte);
    const atualFora = parceiros.find((p) => p.id === atual && !lista.some((x) => x.id === p.id));
    return [...lista, ...(atualFora ? [atualFora] : [])].map(opcaoDoParceiro);
  };
  /** Formulário montado (o contexto do cadastro rápido lê o tipo e a conta escolhidos na hora). */
  let form: HTMLFormElement | null = null;
  const contextoParceiro = () => ({
    tipoConta: form ? fv(form, "tipo_conta") : tipoInicial,
    aporte: plano.find((c) => c.id === (form ? fv(form, "plano_conta_id") : t?.plano_conta_id))?.aporte_socio ?? false,
  });

  abrirGaveta({
    titulo: t ? `Título · ${t.parceiro_nome}` : "Novo título financeiro",
    corpo: html`<div class="fields">
      ${campo("Tipo", sel("tipo_conta", [["R", "A receber (receita)"], ["P", "A pagar (despesa)"]], tipoInicial))}
      ${campo("Situação", sel("status", [["A", "Aberto"], ["Q", "Quitado"], ["C", "Cancelado"]], t?.status ?? "A"))}
      <div class="field full"><label for="f-plano_conta_id">Conta do plano de contas</label>${campoPlano(tipoInicial, t?.plano_conta_id)}<span class="sub" id="dicaPlano"></span></div>
      ${campo("Conta bancária", combobox({ nome: "conta_bancaria_id", rotulo: "Conta bancária", opcoes: contas.map(opcaoDaConta), valor: t?.conta_bancaria_id, cadastroRapido: { tipo: "conta-bancaria" } }))}
      ${campo("Parceiro de negócio", combobox({ nome: "parceiro_id", rotulo: "Parceiro de negócio", opcoes: opcoesParceiro(tipoInicial, t?.plano_conta_id ?? "", t?.parceiro_id), valor: t?.parceiro_id, cadastroRapido: { tipo: "parceiro", contexto: contextoParceiro, aoCriar: (c) => parceiros.push(c.item as Parceiro) } }))}
      ${campo("Data de emissão", inp("data_emissao", t?.data_emissao, 'type="date"'))}${campo("Data de vencimento", inp("data_vencimento", t?.data_vencimento ?? hoje(), 'type="date"'))}
      ${campo("Valor do título (R$)", inpMoeda("valor_titulo", t?.valor_titulo))}${campo("Desconto (R$)", inpMoeda("valor_desconto", t?.valor_desconto))}
      ${campo("Multa (R$)", inpMoeda("valor_multa", t?.valor_multa))}${campo("Juros (R$)", inpMoeda("valor_juros", t?.valor_juros))}
      <div class="field full"><span class="sub">Valor devido: <b class="num" id="devido">R$ 0,00</b></span></div>
      <div class="field quitacao"${t?.status === "Q" ? "" : " hidden"}><label for="f-data_pagamento">Data de pagamento</label>${inp("data_pagamento", t?.data_pagamento, 'type="date"')}</div>
      <div class="field quitacao"${t?.status === "Q" ? "" : " hidden"}><label for="f-valor_quitacao">Valor pago (R$)</label>${inpMoeda("valor_quitacao", t?.status === "Q" ? t?.valor_quitacao : "", "vazio = valor devido")}</div>
      ${campo("Anotação", area("anotacao", t?.anotacao), true)}
    </div>`,
    rodape: html`<button class="btn primary" data-salvar>Salvar</button>${espaco}`,
    montar: (f, fechar, L) => {
      form = f;
      const tipo = f.elements.namedItem("tipo_conta") as HTMLSelectElement;
      const planoSel = f.elements.namedItem("plano_conta_id") as HTMLInputElement;
      const status = f.elements.namedItem("status") as HTMLSelectElement;
      const dica = $("#dicaPlano", L)!;
      const mostrarDica = (): void => {
        dica.textContent = contasDoTipo(tipo.value).length ? `Somente contas analíticas de ${tipo.value === "P" ? "despesa" : "receita"}.` : `Não há conta analítica de ${tipo.value === "P" ? "despesa" : "receita"} no plano de contas. Cadastre uma antes.`;
      };
      const parceiroCbx = comboboxDe(f, "parceiro_id")!;
      const refazerParceiros = (): void => {
        parceiroCbx.definirOpcoes(opcoesParceiro(tipo.value, planoSel.value, fv(f, "parceiro_id")), { valor: fv(f, "parceiro_id") });
      };
      tipo.addEventListener("change", () => {
        comboboxDe(f, "plano_conta_id")?.definirOpcoes(opcoesPlano(tipo.value), { valor: fv(f, "plano_conta_id") });
        mostrarDica();
        refazerParceiros();
      });
      planoSel.addEventListener("change", refazerParceiros);
      mostrarDica();
      const atualizar = (): void => {
        $$(".quitacao", L).forEach((e) => (e.hidden = status.value !== "Q"));
        const devido = numero(fv(f, "valor_titulo")) - numero(fv(f, "valor_desconto")) + numero(fv(f, "valor_multa")) + numero(fv(f, "valor_juros"));
        $("#devido", L)!.textContent = brl(devido);
      };
      f.addEventListener("input", atualizar);
      f.addEventListener("change", atualizar);
      atualizar();

      $("[data-salvar]", L)?.addEventListener("click", async () => {
        if (!fv(f, "plano_conta_id")) return void avisar("Escolha a conta do plano de contas.");
        if (!fv(f, "conta_bancaria_id")) return void avisar("Escolha a conta bancária.");
        if (!fv(f, "parceiro_id")) return void avisar("Escolha o parceiro de negócio.");
        if (!numero(fv(f, "valor_titulo"))) return void avisar("Informe o valor do título.");
        if (status.value === "Q" && !fv(f, "data_pagamento")) return void avisar("Informe a data de pagamento do título quitado.");
        const corpo: TituloEntrada = {
          tipo_conta: tipo.value as "P" | "R", conta_bancaria_id: fv(f, "conta_bancaria_id"), plano_conta_id: fv(f, "plano_conta_id"), parceiro_id: fv(f, "parceiro_id"),
          data_emissao: fv(f, "data_emissao") || null, data_vencimento: fv(f, "data_vencimento"), valor_titulo: numero(fv(f, "valor_titulo")),
          valor_desconto: numero(fv(f, "valor_desconto")), valor_multa: numero(fv(f, "valor_multa")), valor_juros: numero(fv(f, "valor_juros")),
          status: status.value as "A" | "Q" | "C", data_pagamento: status.value === "Q" ? fv(f, "data_pagamento") || null : null,
          valor_quitacao: status.value === "Q" && numero(fv(f, "valor_quitacao")) ? numero(fv(f, "valor_quitacao")) : null, anotacao: fv(f, "anotacao") || null,
        };
        await gravar({
          recarregar: ["financeiro"], mensagem: "Título salvo", fechar,
          operacao: () => (t ? apiFinanceiro.titulos.atualizar(t.id, corpo) : apiFinanceiro.titulos.criar(corpo)),
        });
      });
    },
  });
}

const porId = (id?: string): Titulo | undefined => tela.pagina?.itens.find((t) => t.id === id);

registrarAcao("novoTitulo", () => void formTitulo());
registrarAcao("tituloEditar", (alvo) => {
  const t = porId(alvo.dataset.id);
  if (t) void formTitulo(t);
});
registrarAcao("tituloExcluir", (alvo) => {
  const t = porId(alvo.dataset.id);
  if (t) confirmarExclusao({ titulo: "Excluir título", mensagem: `Excluir o título de ${t.parceiro_nome} com vencimento em ${dataBR(t.data_vencimento)} (${brl(t.valor_devido)})?`, sucesso: "Título excluído", operacao: () => apiFinanceiro.titulos.excluir(t.id) });
});
registrarAcao("filtroFinTipo", (alvo) => void mudar({ tipo: alvo.dataset.valor ?? "todos" }));
registrarAcao("filtroFinStatus", (alvo) => void mudar({ status: alvo.dataset.valor ?? "todos" }));
registrarAcao("finAtalho", (alvo) => {
  const atalho = alvo.dataset.valor as Atalho;
  // clicar no atalho já ativo o desliga (volta a Situação e ao vencimento do padrão)
  if (atalhoAtivo(tela.consulta, hoje()) === atalho) return void aplicar(limparChaves({ ...tela.consulta, status: "todos" }, ["venc_de", "venc_ate"]));
  void aplicar(aplicarAtalho(tela.consulta, atalho, hoje()));
});
registrarAcao("finOrdenar", (alvo) => {
  const ordem = alvo.dataset.valor ?? "vencimento";
  void mudar({ ordem, sentido: tela.consulta.ordem === ordem && tela.consulta.sentido === "asc" ? "desc" : "asc" });
});
registrarAcao("finPagina", (alvo) => {
  const pagina = Number(alvo.dataset.valor);
  if (pagina >= 1) void aplicar({ ...tela.consulta, pag: String(pagina) }, "push");
});
registrarAcao("finTamanho", (alvo) => void mudar({ tam: (alvo as HTMLSelectElement).value }));
registrarAcao("finRemoverChip", (alvo) => {
  const chip = chipsDeFiltro(tela.consulta, NOMES)[Number(alvo.dataset.i)];
  if (chip) void aplicar(limparChaves(tela.consulta, chip.chaves));
});
registrarAcao("finLimparChips", () => void aplicar(limparChaves(tela.consulta, chipsDeFiltro(tela.consulta, NOMES).flatMap((c) => c.chaves))));
registrarAcao("finExportar", () => void tentar(() => apiFinanceiro.titulos.exportar(filtrosDaApi(tela.consulta))));
registrarAcao("finRecarregar", () => void recarregarVista());
registrarAcao("finFiltros", () => void abrirFiltros());

/** Busca por parceiro: espera a pessoa parar de digitar, consulta o servidor e devolve o foco ao campo (a tela é refeita). */
let esperaDaBusca: ReturnType<typeof setTimeout> | undefined;
document.addEventListener("input", (e) => {
  const campo = e.target as HTMLInputElement;
  if (!campo.matches?.("[data-fin-busca]")) return;
  clearTimeout(esperaDaBusca);
  esperaDaBusca = setTimeout(async () => {
    const digitado = campo.value.trim();
    if (digitado === tela.consulta.q) return;
    const tinhaFoco = document.activeElement === campo;
    await mudar({ q: digitado });
    const novo = $<HTMLInputElement>("[data-fin-busca]");
    if (!novo || !tinhaFoco) return;
    novo.focus();
    novo.setSelectionRange(novo.value.length, novo.value.length);
  }, 300);
});

/** Gaveta dos filtros avançados: preenche com a consulta atual e, ao aplicar, volta à primeira página. */
async function abrirFiltros(): Promise<void> {
  const apoio = await tentar(buscarApoio);
  if (!apoio) return;
  tela.apoio = apoio;
  const c = tela.consulta;
  const nomeDoPai = new Map(apoio.plano.map((x) => [x.id, `${x.codigo} ${x.nome}`]));
  const analiticas: OpcaoCombobox[] = apoio.plano
    .filter((x) => x.tipo_conta === "A")
    .map((x) => ({ id: x.id, codigo: x.codigo, rotulo: x.nome, grupo: x.plano_pai_id ? nomeDoPai.get(x.plano_pai_id) : undefined }));
  abrirGaveta({
    titulo: "Filtros avançados",
    corpo: html`<div class="fields">
      <div class="field full"><label for="f-parceiro">Parceiro</label>${combobox({ nome: "parceiro", rotulo: "Parceiro", opcoes: apoio.parceiros.map(opcaoDoParceiro), valor: c.parceiro, vazio: "Todos os parceiros" })}</div>
      <div class="field full"><label for="f-plano">Conta do plano de contas</label>${combobox({ nome: "plano", rotulo: "Conta do plano de contas", opcoes: analiticas, valor: c.plano, vazio: "Todas as contas" })}</div>
      <div class="field full"><label for="f-conta">Conta bancária</label>${combobox({ nome: "conta", rotulo: "Conta bancária", opcoes: apoio.contas.map(opcaoDaConta), valor: c.conta, vazio: "Todas as contas" })}</div>
      ${campo("Vencimento a partir de", inp("venc_de", c.venc_de, 'type="date"'))}${campo("Vencimento até", inp("venc_ate", c.venc_ate, 'type="date"'))}
      ${campo("Pagamento a partir de", inp("pago_de", c.pago_de, 'type="date"'))}${campo("Pagamento até", inp("pago_ate", c.pago_ate, 'type="date"'))}
      ${campo("Valor devido mínimo (R$)", inpMoeda("vmin", c.vmin))}${campo("Valor devido máximo (R$)", inpMoeda("vmax", c.vmax))}
      ${campo("Origem", sel("origem", [["todas", "Todos"], ["recorrentes", "Só recorrentes"], ["avulsos", "Só avulsos"]], c.origem), true)}
    </div>`,
    rodape: html`<button class="btn primary" data-aplicar>Aplicar</button><button class="btn" data-limpar>Limpar</button>${espaco}`,
    montar: (f, fechar, L) => {
      $("[data-aplicar]", L)?.addEventListener("click", () => {
        const novo = {
          ...c, pag: "1", parceiro: fv(f, "parceiro"), plano: fv(f, "plano"), conta: fv(f, "conta"),
          venc_de: fv(f, "venc_de"), venc_ate: fv(f, "venc_ate"), pago_de: fv(f, "pago_de"), pago_ate: fv(f, "pago_ate"),
          vmin: valorParaConsulta(fv(f, "vmin")), vmax: valorParaConsulta(fv(f, "vmax")), origem: fv(f, "origem") || "todas",
        };
        if (novo.venc_de && novo.venc_ate && novo.venc_de > novo.venc_ate) return void avisar("O vencimento inicial não pode ser depois do final.");
        if (novo.pago_de && novo.pago_ate && novo.pago_de > novo.pago_ate) return void avisar("O pagamento inicial não pode ser depois do final.");
        if (novo.vmin && novo.vmax && Number(novo.vmin) > Number(novo.vmax)) return void avisar("O valor mínimo não pode ser maior que o máximo.");
        fechar();
        void aplicar(novo);
      });
      $("[data-limpar]", L)?.addEventListener("click", () => {
        fechar();
        void aplicar(limparChaves(c, FILTROS_AVANCADOS));
      });
    },
  });
}
