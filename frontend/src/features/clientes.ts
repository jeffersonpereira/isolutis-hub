import { api } from "@/api/endpoints";
import type { Cliente } from "@/api/tipos";
import { $ } from "@/core/dom";
import { brl, compararTexto, iniciais, normalizarTexto, pluralizar } from "@/core/formato";
import { esc, html, raw, type Safe } from "@/core/html";
import { ORC_STATUS, ORIGENS, etapaNome } from "@/domain/constantes";
import { botaoWa, numeroWa } from "@/domain/whatsapp";
import { dados, podeEscrever, ui } from "@/state/estado";
import { caminhoDoRegistro, caminhoNovo } from "@/state/caminhos";
import { registrarVista, render } from "@/state/nucleo";
import { registrarRotaDeRegistro } from "@/state/roteador";
import { registrarAcao } from "@/ui/acoes";
import { barraDeFerramentas, cabecalhoDePagina, chip, estadoVazio } from "@/ui/componentes";
import { registrarConsulta } from "@/ui/conflito";
import { registrarAbertura } from "@/ui/eventos";
import { abrirFormularioPagina, mostrarRegistroNaoEncontrado } from "@/ui/formulario-pagina";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { melhorarFormulario } from "@/ui/acessibilidade";
import { toast } from "@/ui/toast";
import { ligarCamposDoParceiro, lerCamposDoParceiro, secoesDoParceiro } from "./parceiros/campos";
import { botaoNovo } from "./comum";
import { formNegocio, valorNegocio } from "./negocios";

registrarConsulta("clientes", (id) => dados.clientes.find((c) => c.id === id));

function vista(): Safe {
  const q = normalizarTexto(ui.busca);
  const todos = dados.clientes;
  const n = todos.length;
  const lista = todos
    .filter((c) => !q || normalizarTexto([c.nome, c.contato, c.municipio_nome, c.segmento, c.email].join(" ")).includes(q))
    .filter((c) => !ui.cliOrigem || c.origem === ui.cliOrigem)
    .filter((c) => !ui.cliComNegocios || c.negocios_abertos > 0)
    .sort((a, b) => compararTexto(a.nome, b.nome));
  const cabecalho = cabecalhoDePagina({
    titulo: "Clientes",
    descricao: `${n} ${pluralizar(n, "empresa cadastrada", "empresas cadastradas")}`,
    acoes: botaoNovo("novoCliente", "Novo cliente"),
  });
  if (!n) {
    return html`${cabecalho}${estadoVazio({
      icone: "clientes",
      titulo: "Nenhum cliente ainda",
      texto: "Cadastre as empresas com quem a iSolutis conversa: quem pediu diagnóstico, quem já é cliente de manutenção, quem veio por indicação.",
      acao: podeEscrever() ? html`<button class="btn primary" data-act="novoCliente">Cadastrar o primeiro cliente</button>` : undefined,
    })}`;
  }
  const comNegocios = todos.filter((c) => c.negocios_abertos > 0).length;
  const abertos = todos.reduce((soma, c) => soma + c.negocios_abertos, 0);
  const faturado = todos.reduce((soma, c) => soma + c.faturado, 0);
  const filtros = html`<select class="chip" data-act="filtrarOrigem" aria-label="Filtrar por origem"><option value="">Origem: todas</option>${ORIGENS.map((o) => html`<option value="${o}"${o === ui.cliOrigem ? raw(" selected") : ""}>${o}</option>`)}</select>${chip({ rotulo: "Com negócios abertos", acao: "alternarComNegocios", pressionado: ui.cliComNegocios })}`;
  const contagem = `${lista.length} ${pluralizar(lista.length, "cliente", "clientes")}`;
  return html`${cabecalho}
    <div class="kpis">
      <div class="kpi"><span class="l">Clientes</span><span class="v">${n}</span><span class="s">${comNegocios} ${pluralizar(comNegocios, "com negócio aberto", "com negócios abertos")}</span></div>
      <div class="kpi"><span class="l">Negócios abertos</span><span class="v">${abertos}</span><span class="s">em ${comNegocios} ${pluralizar(comNegocios, "cliente", "clientes")}</span></div>
      <div class="kpi"><span class="l">Faturado</span><span class="v num">${brl(faturado)}</span><span class="s">recebido de todos os clientes</span></div>
    </div>
    <div class="painel-lista">
      ${barraDeFerramentas({ busca: { chave: "busca", valor: ui.busca, placeholder: "Buscar por nome, contato ou cidade", rotulo: "Buscar clientes" }, filtros, contagem })}
      <div class="tbl-wrap"><table><thead><tr><th>Empresa</th><th>Contato</th><th>Cidade</th><th>Origem</th><th class="r">Negócios abertos</th><th class="r">Faturado</th></tr></thead><tbody>
      ${lista.map(
        (c) => html`<tr tabindex="0" data-open="cliente:${c.id}"><td><div class="who"><i class="av" aria-hidden="true">${iniciais(c.nome)}</i><div><b>${c.nome}</b>${c.segmento ? html`<div class="sub">${c.segmento}</div>` : ""}</div></div></td>
          <td>${c.contato || "—"}${c.telefone ? html`<div class="sub num">${c.telefone}</div>` : ""}${numeroWa(c.telefone) ? html`<div>${botaoWa(c, "Conversar", undefined, "mini")}</div>` : ""}</td>
          <td>${c.municipio_nome ? `${c.municipio_nome}/${c.uf}` : "—"}</td><td>${c.origem ? html`<span class="pill">${c.origem}</span>` : "—"}</td><td class="r num">${c.negocios_abertos}</td><td class="r num">${brl(c.faturado)}</td></tr>`,
      )}
      ${!lista.length ? html`<tr><td colspan="6"><div class="empty sem-borda">Nenhum cliente encontrado${ui.busca ? html` para “${ui.busca}”` : ""}. Tente outro termo ou limpe os filtros.</div></td></tr>` : ""}
      </tbody></table></div>
      <div class="rodtab"><span>Mostrando ${lista.length} de ${n}</span><span>Dica: pressione <kbd>Enter</kbd> numa linha para abrir</span></div>
    </div>`;
}

registrarVista({
  id: "clientes",
  nome: "Clientes",
  contagem: () => dados.clientes.length,
  desenhar: vista,
});

/** Abre o cliente num formulário em página (rota `/clientes/<id>` ou `/clientes/novo`). */
export function formCliente(c?: Cliente): void {
  const novo = !c;
  const secoes = secoesDoParceiro(c ?? {});
  if (c) secoes.push({ id: "relacionados", titulo: "Relacionados", descricao: "Registros ligados a este cliente", corpo: html`<div class="related" id="relacionados">${relacionados(c)}</div>` });
  void abrirFormularioPagina({
    vista: "clientes",
    rotuloLista: "Clientes",
    caminho: c ? caminhoDoRegistro("clientes", c.id) : caminhoNovo("clientes"),
    titulo: c ? c.nome : "Novo cliente",
    avatar: c ? iniciais(c.nome) : undefined,
    meta: linhaAutoria(c),
    secoes,
    acoes: html`${c ? botaoWa(c, "Conversar no WhatsApp") : ""}${c && podeEscrever() ? html`<button type="button" class="btn" data-novo-negocio>Novo negócio</button>` : ""}`,
    salvar: botaoSalvar(),
    excluir: botaoExcluir(!!c),
    registro: c ? { recurso: "clientes", id: c.id, versao: c.versao } : null,
    montar: (f, fechar, L) => {
      // Melhorar acessibilidade
      melhorarFormulario(f);

      ligarCamposDoParceiro(f, c ?? {});
      if (c) void preencherFaturamento(c.id);

      // Salvar com validação e loading visual
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;

        // Validar
        const lido = lerCamposDoParceiro(f, "cliente");
        if (!lido) {
          toast("Corrija os dados do cliente antes de salvar.");
          return;
        }

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        const textoOriginal = botao.textContent;
        botao.innerHTML = '<span class="spinner"></span> Salvando…';

        try {
          const corpo = Object.fromEntries(
            Object.entries(lido).filter(([k]) => k !== "tipo_pessoa" && k !== "papeis")
          ) as Parameters<typeof api.clientes.criar>[0];

          await gravar({
            recarregar: ["clientes"],
            mensagem: "Cliente salvo",
            fechar,
            operacao: () =>
              novo ? api.clientes.criar(corpo) : api.clientes.atualizar(c.id, { ...corpo, versao: c.versao }),
          });
        } catch {
          // Erro já foi tratado em gravar/tentar
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Salvar";
        }
      });

      // Excluir
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (c) void excluir({ recarregar: ["clientes"], mensagem: "Cliente excluído", fechar, operacao: () => api.clientes.excluir(c.id) });
      });

      // Novo negócio
      $("[data-novo-negocio]", L)?.addEventListener("click", () => {
        if (c) formNegocio({ cliente_id: c.id, etapa: "lead" });
      });
    },
  });
}

/** Negócios e orçamentos do cliente (já em memória); o faturamento chega do servidor logo em seguida. */
function relacionados(c: Cliente): Safe {
  const ns = dados.negocios.filter((n) => n.cliente_id === c.id);
  const os = dados.orcamentos.filter((o) => o.cliente_id === c.id);
  return html`<h3>Negócios (${ns.length})</h3>${ns.length ? ns.map((n) => html`<div class="li" data-open="negocio:${n.id}"><span class="t">${n.titulo}</span><span class="sub">${etapaNome(n.etapa)} · ${valorNegocio(n)}</span></div>`) : html`<p class="sub">Nenhum.</p>`}
    <h3>Orçamentos (${os.length})</h3>${os.length ? os.map((o) => html`<div class="li" data-open="orcamento:${o.id}"><span class="t">Nº ${o.numero}</span><span class="sub">${ORC_STATUS[o.status_exibido]?.[0]} · ${brl(o.total_projeto)}</span></div>`) : html`<p class="sub">Nenhum.</p>`}
    <h3>Faturamento</h3><p class="sub" style="margin:0" id="relFat">Carregando…</p>`;
}

async function preencherFaturamento(id: string): Promise<void> {
  try {
    const r = await api.clientes.relacionados(id);
    const el = $("#relFat");
    if (el) el.innerHTML = `${r.lancamentos} ${esc(pluralizar(r.lancamentos, "lançamento", "lançamentos"))} · <b class="num">${esc(brl(r.recebido))}</b> recebido`;
  } catch {
    const el = $("#relFat");
    if (el) el.textContent = "Não foi possível carregar o faturamento.";
  }
}

registrarAcao("novoCliente", () => formCliente());
registrarAbertura("cliente", (id) => {
  const c = dados.clientes.find((x) => x.id === id);
  if (c) formCliente(c);
});

registrarAcao("alternarComNegocios", () => {
  ui.cliComNegocios = !ui.cliComNegocios;
  render();
  $<HTMLElement>('[data-act="alternarComNegocios"]')?.focus();
});
registrarAcao("filtrarOrigem", (alvo) => {
  ui.cliOrigem = (alvo as HTMLSelectElement).value;
  render();
  $<HTMLElement>('[data-act="filtrarOrigem"]')?.focus();
});

registrarRotaDeRegistro("clientes", {
  novo: () => formCliente(),
  abrir: (id) => {
    const c = dados.clientes.find((x) => x.id === id);
    if (c) formCliente(c);
    else mostrarRegistroNaoEncontrado({ vista: "clientes", rotuloLista: "Clientes" });
  },
});
