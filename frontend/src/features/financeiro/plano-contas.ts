import { $ } from "@/core/dom";
import { html, raw, type Safe } from "@/core/html";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { campo, fv, inp, sel } from "@/ui/campos";
import { tentar } from "@/ui/erros";
import { abrirGaveta } from "@/ui/gaveta";
import { espaco } from "@/ui/formularios";
import { gravar } from "@/ui/gravacao";
import { avisar } from "@/ui/toast";
import { apiFinanceiro, type PlanoConta, type PlanoContaEntrada } from "./api";
import { confirmarExclusao, GRUPO } from "./comum";

/** Estado da tela: lista plana vinda do servidor (já ordenada por código), nó selecionado e nós recolhidos. */
const NATUREZAS = ["RECEITAS", "CUSTOS", "DESPESAS", "INVESTIMENTOS", "MOVIMENTAÇÕES FINANCEIRAS", "EMPRÉSTIMOS E FINANCIAMENTOS"] as const;

const tela: { contas: PlanoConta[] | null; selecionada: string | null; recolhidas: Set<string>; busca: string } = {
  contas: null,
  selecionada: null,
  recolhidas: new Set(),
  busca: "",
};

async function carregar(): Promise<void> {
  tela.contas = await apiFinanceiro.plano.listar();
  if (tela.selecionada && !tela.contas.some((c) => c.id === tela.selecionada)) tela.selecionada = null;
}

function idsVisiveis(): Set<string> | null {
  const termo = tela.busca.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
  if (!termo || !tela.contas) return null;
  const porId = new Map(tela.contas.map((c) => [c.id, c]));
  const visiveis = new Set<string>();
  const incluirDescendentes = (id: string): void => {
    for (const filha of tela.contas!.filter((c) => c.plano_pai_id === id)) {
      if (visiveis.has(filha.id)) continue;
      visiveis.add(filha.id);
      incluirDescendentes(filha.id);
    }
  };
  for (const c of tela.contas) {
    const texto = `${c.codigo} ${c.nome} ${c.natureza}`.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
    if (!texto.includes(termo)) continue;
    visiveis.add(c.id);
    let pai = c.plano_pai_id;
    while (pai) {
      visiveis.add(pai);
      pai = porId.get(pai)?.plano_pai_id ?? null;
    }
    incluirDescendentes(c.id);
  }
  return visiveis;
}

const filhasDe = (pai: string | null): PlanoConta[] => {
  const visiveis = idsVisiveis();
  return (tela.contas ?? []).filter((c) => c.plano_pai_id === pai && (!visiveis || visiveis.has(c.id)));
};
const contaSelecionada = (): PlanoConta | undefined => tela.contas?.find((c) => c.id === tela.selecionada);

function no(c: PlanoConta): Safe {
  const filhas = filhasDe(c.id);
  const aberto = !!tela.busca.trim() || !tela.recolhidas.has(c.id);
  return html`<li role="treeitem" aria-expanded="${filhas.length ? aberto : ""}">
    <div class="tree-row" tabindex="0" data-act="selecionarConta" data-id="${c.id}" aria-selected="${tela.selecionada === c.id}">
      <button class="tree-caret${filhas.length ? "" : " vazio"}" type="button" data-act="alternarNo" data-id="${c.id}" aria-expanded="${aberto}" aria-label="${aberto ? "Recolher" : "Expandir"} ${c.nome}"><i>›</i></button>
      <span class="tree-cod">${c.codigo}</span><span class="tree-nome${c.tipo_conta === "S" ? " sintetica" : ""}">${c.nome}</span>
      <span class="tree-pills"><span class="pill">${c.natureza}</span><span class="pill">${c.tipo_conta === "S" ? "Sintética" : "Analítica"}</span></span>
      <span style="display:flex;gap:5px;flex:none"><button class="btn" type="button" data-act="editarConta" data-id="${c.id}" aria-label="Editar ${c.nome}">Editar</button><button class="btn danger" type="button" data-act="excluirConta" data-id="${c.id}" aria-label="Excluir ${c.nome}">Excluir</button></span>
    </div>
    ${filhas.length && aberto ? html`<ul class="tree" role="group">${filhas.map(no)}</ul>` : ""}
  </li>`;
}

function vista(): Safe {
  if (!tela.contas) return html`<div class="head"><div><h1>Plano de contas</h1></div></div><p class="sub">Carregando…</p>`;
  const sel_ = contaSelecionada();
  const podeFilha = !sel_ || (sel_.tipo_conta === "S" && sel_.nivel < 3);
  return html`<div class="head"><div><h1>Plano de contas</h1><p>Até três níveis (1 · 1.01 · 1.01.001). Só contas analíticas recebem lançamentos.</p></div>
    <div class="tools">
      <label class="sub" for="buscaPlano">Pesquisar</label><input id="buscaPlano" type="search" data-busca-plano value="${tela.busca}" placeholder="Código, nome ou natureza" aria-label="Pesquisar contas por código, nome ou natureza">
      <button class="btn primary" data-act="novaConta"${raw(podeFilha ? "" : " disabled")}>${sel_ ? "Nova conta filha" : "Nova conta"}</button>
      <button class="btn" data-act="editarConta"${raw(sel_ ? "" : " disabled")}>Editar</button>
      <button class="btn danger" data-act="excluirConta"${raw(sel_ ? "" : " disabled")}>Excluir</button>
    </div></div>
  ${
    tela.contas.length
      ? html`<div class="panel"><ul class="tree" role="tree" aria-label="Plano de contas">${filhasDe(null).map(no)}</ul></div>
        <p class="sub" style="margin-top:10px">${tela.busca.trim() && !filhasDe(null).length ? "Nenhuma conta corresponde à pesquisa." : sel_ ? html`Selecionada: <b>${sel_.codigo} ${sel_.nome}</b>.` : "Use os botões de cada conta para editar ou excluir; “Nova conta” cria uma conta de primeiro nível."}</p>`
      : html`<div class="empty"><b>Plano de contas vazio</b>Comece pelas contas de primeiro nível, por exemplo 1 Receita e 2 Despesa, e vá abrindo os níveis.<br><button class="btn primary" data-act="novaConta">Criar a primeira conta</button></div>`
  }`;
}

registrarVista({ id: "fin-plano", nome: "Plano de Contas", grupo: GRUPO, somenteAdmin: true, carregar, depende: ["financeiro"], desenhar: vista });

function formConta(modo: "nova" | "editar", base?: PlanoConta, paiInicial?: PlanoConta): void {
  const editando = modo === "editar" && base;
  const todas = tela.contas ?? [];
  const ids_bloqueados = new Set<string>(editando ? [base.id] : []);
  const possiveisPais = todas.filter((c) => c.tipo_conta === "S" && c.nivel < 3 && !ids_bloqueados.has(c.id));
  const paiAtual = editando ? base.plano_pai_id : (paiInicial?.id ?? null);
  const temFilhas = !!base?.possui_filhas;
  const natureza = editando ? base.natureza : (paiInicial?.natureza ?? "RECEITAS");

  abrirGaveta({
    titulo: editando ? `Conta ${base.codigo}` : paiInicial ? `Nova conta em ${paiInicial.codigo}` : "Nova conta",
    corpo: html`<div class="fields">
      ${campo("Conta pai", sel("plano_pai_id", [["", "— (primeiro nível)"], ...possiveisPais.map((c) => [c.id, `${c.codigo} ${c.nome}`] as const)], paiAtual ?? ""), true)}
      <div class="field"><label for="f-codigo">Código</label><div style="display:flex;gap:6px">${inp("codigo", base?.codigo, `placeholder="Ex.: 1.01.001"${temFilhas ? " readonly" : ""}`)}${editando ? "" : html`<button class="btn" type="button" id="sugerir" title="Sugere o próximo código livre">Sugerir</button>`}</div></div>
      ${campo("Nome", inp("nome", base?.nome, 'maxlength="150"'))}
      ${campo("Tipo", sel("tipo_conta", [["A", "Analítica (recebe lançamentos)"], ["S", "Sintética (agrupa contas)"]], base?.tipo_conta ?? "A"))}
      ${campo("Natureza", sel("natureza", NATUREZAS.map((n) => [n, n] as const), natureza))}
    </div>
    <p class="sub" id="dicaConta" style="margin:0"></p>`,
    rodape: html`<button class="btn primary" data-salvar>Salvar</button>${espaco}`,
    montar: (f, fechar, L) => {
      const pai = f.elements.namedItem("plano_pai_id") as HTMLSelectElement;
      const codigo = f.elements.namedItem("codigo") as HTMLInputElement;
      const tipo = f.elements.namedItem("tipo_conta") as HTMLSelectElement;
      const nat = f.elements.namedItem("natureza") as HTMLSelectElement;
      const dica = $("#dicaConta", L)!;
      const paiEscolhido = (): PlanoConta | undefined => todas.find((c) => c.id === pai.value);

      const ajustar = (): void => {
        const p = paiEscolhido();
        if (p) nat.value = p.natureza; // a natureza é herdada da conta pai
        nat.disabled = !!p || temFilhas;
        const terceiro = (p?.nivel ?? 0) === 2;
        if (terceiro) tipo.value = "A"; // o terceiro nível é sempre analítico
        tipo.disabled = terceiro || temFilhas;
        if (temFilhas) tipo.value = "S";
        dica.textContent = terceiro ? "Contas do terceiro nível são sempre analíticas." : temFilhas ? "Esta conta tem filhas: código, natureza e tipo não podem mudar." : "";
      };
      const sugerir = async (): Promise<void> => {
        const r = await tentar(() => apiFinanceiro.plano.proximoCodigo(pai.value || null));
        if (r) codigo.value = r.codigo;
      };
      pai.addEventListener("change", async () => {
        ajustar();
        if (!editando) await sugerir();
      });
      $("#sugerir", L)?.addEventListener("click", () => void sugerir());
      ajustar();
      if (!editando) void sugerir();

      $("[data-salvar]", L)?.addEventListener("click", async () => {
        if (!fv(f, "codigo")) return void avisar("Informe o código da conta.");
        if (!fv(f, "nome")) return void avisar("Informe o nome da conta.");
        const corpo: PlanoContaEntrada = {
          plano_pai_id: pai.value || null, codigo: fv(f, "codigo"), nome: fv(f, "nome"),
          tipo_conta: tipo.value as "A" | "S", natureza: nat.value as PlanoContaEntrada["natureza"],
        };
        const salva = await gravar({
          recarregar: ["financeiro"], mensagem: "Conta salva", fechar,
          operacao: () => (editando ? apiFinanceiro.plano.atualizar(base.id, corpo) : apiFinanceiro.plano.criar(corpo)),
        });
        if (salva) {
          tela.selecionada = salva.id;
          render();
        }
      });
    },
  });
}

registrarAcao("selecionarConta", (alvo) => {
  tela.selecionada = tela.selecionada === alvo.dataset.id ? null : (alvo.dataset.id ?? null);
  render();
});

$("#view")?.addEventListener("input", (evento) => {
  const input = evento.target as HTMLInputElement;
  if (!input.matches("[data-busca-plano]")) return;
  tela.busca = input.value;
  const posicao = input.selectionStart ?? input.value.length;
  render();
  const novo = $("[data-busca-plano]") as HTMLInputElement | null;
  novo?.focus();
  novo?.setSelectionRange(posicao, posicao);
});

registrarAcao("alternarNo", (alvo) => {
  const id = alvo.dataset.id ?? "";
  if (tela.recolhidas.has(id)) tela.recolhidas.delete(id);
  else tela.recolhidas.add(id);
  render();
});
registrarAcao("novaConta", () => {
  const s = contaSelecionada();
  formConta("nova", undefined, s && s.tipo_conta === "S" && s.nivel < 3 ? s : undefined);
});
registrarAcao("editarConta", (alvo) => {
  const s = (tela.contas ?? []).find((c) => c.id === alvo.dataset.id) ?? contaSelecionada();
  if (s) formConta("editar", s);
});
registrarAcao("excluirConta", (alvo) => {
  const s = (tela.contas ?? []).find((c) => c.id === alvo.dataset.id) ?? contaSelecionada();
  if (!s) return;
  confirmarExclusao({
    titulo: "Excluir conta",
    mensagem: `Excluir a conta ${s.codigo} ${s.nome}? Contas com filhas ou com títulos lançados não podem ser excluídas.`,
    sucesso: "Conta excluída",
    operacao: () => apiFinanceiro.plano.excluir(s.id),
  });
});

