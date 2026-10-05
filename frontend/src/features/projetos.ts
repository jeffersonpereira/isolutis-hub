import { api } from "@/api/endpoints";
import type { EtapaEntrada, Projeto, ProjetoEntrada } from "@/api/tipos";
import { $ } from "@/core/dom";
import { dataBR, hoje } from "@/core/formato";
import { html, raw, type Safe } from "@/core/html";
import { ETAPA_STATUS, PROJ_STATUS } from "@/domain/constantes";
import { dados, eu, nomeCliente, podeEscrever, ui } from "@/state/estado";
import { registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco, ligarNovoCliente, opcoesEquipe, resolverCliente, seletorCliente } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { avisar, toast } from "@/ui/toast";
import { melhorarFormulario } from "@/ui/acessibilidade";
import { botaoNovo } from "./comum";
import { registrarFormulario } from "./ponte";

registrarConsulta("projetos", (id) => dados.projetos.find((p) => p.id === id));

function vista(): Safe {
  const f = ui.projStatus;
  const h = hoje();
  const lista = dados.projetos
    .filter((p) => f === "todos" || (f === "ativos" ? p.status !== "entregue" : p.status === f))
    .sort((a, b) => (a.entrega ?? "9").localeCompare(b.entrega ?? "9"));
  const segs: Array<[string, string]> = [["ativos", "Em andamento"], ["entregue", "Entregues"], ["todos", "Todos"]];
  const escrever = podeEscrever();
  const ganhosSemProjeto = dados.negocios.filter((n) => n.etapa === "ganho" && !dados.projetos.some((p) => p.negocio_id === n.id));
  return html`<div class="head"><div><h1>Projetos</h1><p>O passo a passo da construção de cada solução vendida e o relatório de entrega para o cliente.</p></div>
    <div class="tools"><div class="seg" role="group" aria-label="Filtrar projetos">${segs.map(([k, r]) => html`<button data-act="filtroProj" data-valor="${k}" aria-pressed="${f === k}">${r}</button>`)}</div>${botaoNovo("novoProjeto", "Novo projeto")}</div></div>
  ${
    ganhosSemProjeto.length && escrever
      ? html`<div class="banner" style="background:var(--info-bg);color:var(--info)">${ganhosSemProjeto.length === 1 ? "Um negócio ganho ainda não tem projeto" : ganhosSemProjeto.length + " negócios ganhos ainda não têm projeto"}: ${ganhosSemProjeto.slice(0, 4).map((n, i) => html`${i ? " · " : ""}<button class="btn ghost" style="padding:0 4px;color:inherit;text-decoration:underline" data-act="projetoDoNegocio" data-id="${n.id}">${n.titulo}</button>`)}</div>`
      : ""
  }
  ${
    !dados.projetos.length
      ? html`<div class="empty"><b>Nenhum projeto ainda</b>Quando um negócio é ganho, abra o projeto: registre o escopo, monte as etapas da construção e acompanhe o andamento. No fim, gere o relatório de entrega com a identidade da iSolutis para mostrar ao cliente.${escrever ? html`<br><button class="btn primary" data-act="novoProjeto">Abrir o primeiro projeto</button>` : ""}</div>`
      : !lista.length
        ? html`<p class="sub">Nenhum projeto com esse filtro.</p>`
        : html`<div class="pgrid">${lista.map((p) => {
            const [rot, cls] = PROJ_STATUS[p.status] ?? PROJ_STATUS.planejamento!;
            const atrasado = p.entrega && p.entrega < h && p.status !== "entregue";
            const concluidas = p.etapas.filter((e) => e.status === "concluida").length;
            const agora = p.etapas.find((e) => e.status === "andamento") ?? p.etapas.find((e) => e.status !== "concluida");
            return html`<article class="pcard" tabindex="0" data-open="projeto:${p.id}"><div class="pc-h"><span class="pill ${cls}">${rot}</span>${atrasado ? html`<span class="pill bad">Atrasado</span>` : ""}</div>
        <b class="pc-t">${p.titulo}</b><span class="sub">${p.cliente_nome}</span>
        <div class="prog" aria-label="${p.progresso}% concluído"><i style="width:${p.progresso}%"></i></div>
        <div class="pc-m"><span>${concluidas} de ${p.etapas.length} etapas · ${p.progresso}%</span><span class="num">${p.entrega ? "entrega " + dataBR(p.entrega) : "sem data de entrega"}</span></div>
        ${agora && p.status !== "entregue" ? html`<span class="sub">Agora: ${agora.titulo}</span>` : ""}</article>`;
          })}</div>`
  }`;
}

registrarVista({
  id: "projetos",
  nome: "Projetos",
  contagem: () => dados.projetos.filter((p) => p.status !== "entregue").length,
  desenhar: vista,
});

type EtapaTela = EtapaEntrada & { id?: string | null };

function progressoDe(etapas: readonly EtapaTela[]): number {
  return etapas.length ? Math.round((100 * etapas.filter((e) => e.status === "concluida").length) / etapas.length) : 0;
}

export function formProjeto(p?: Projeto, inicial: Partial<ProjetoEntrada> = {}): void {
  let atual = p;
  const etapas: EtapaTela[] = (p?.etapas ?? []).map((e) => ({ id: e.id, titulo: e.titulo, status: e.status as EtapaTela["status"], responsavel_id: e.responsavel_id, inicio: e.inicio, fim: e.fim, descricao: e.descricao, entregaveis: e.entregaveis }));
  const ganhos = dados.negocios.filter((n) => n.etapa === "ganho");
  const v = <K extends keyof ProjetoEntrada>(k: K): ProjetoEntrada[K] | undefined => (p ? (p as unknown as ProjetoEntrada)[k] : inicial[k]);
  abrirGaveta({
    titulo: p ? p.titulo : "Novo projeto",
    registro: p ? { recurso: "projetos", id: p.id, versao: p.versao } : null,
    autoria: linhaAutoria(p),
    corpo: html`<div class="fields">
      ${campo("Nome do projeto", inp("titulo", v("titulo"), 'placeholder="Ex.: Portal do cliente"'), true)}
      ${seletorCliente(v("cliente_id"))}<div class="field"><label for="f-negocio_id">Negócio vendido</label>${sel("negocio_id", [["", "Sem vínculo"], ...ganhos.map((n) => [n.id, `${n.titulo} · ${nomeCliente(n.cliente_id)}`] as const)], v("negocio_id"))}</div>
      ${campo("Situação", sel("status", Object.entries(PROJ_STATUS).map(([k, x]) => [k, x[0]] as const), v("status") ?? "planejamento"))}${campo("Responsável técnico", sel("responsavel_id", opcoesEquipe("Sem responsável", true), v("responsavel_id") ?? (p ? "" : eu.id)))}
      ${campo("Início", inp("inicio", v("inicio") ?? hoje(), 'type="date"'))}${campo("Entrega prevista", inp("entrega", v("entrega"), 'type="date"'))}
      ${campo("Objetivo do projeto", area("objetivo", v("objetivo"), "O problema que o sistema resolve para o cliente, em uma ou duas frases."), true)}
      ${campo("Escopo (o que será entregue)", area("escopo", v("escopo"), "Uma linha por item."), true)}
      ${campo("Fora do escopo", area("fora_escopo", v("fora_escopo"), "O que não faz parte desta entrega (opcional)."), true)}
      ${campo("Depois da entrega", area("pos_entrega", v("pos_entrega")), true)}
    </div>
    <div><div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap"><h2 style="margin:0">Passo a passo da construção</h2><span class="sub" id="progTxt"></span></div>
      <div id="etapasBox" class="etapas"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px"><button class="btn" type="button" id="addEtapa">Adicionar etapa</button><button class="btn ghost" type="button" id="padrao">Usar as etapas padrão da iSolutis</button></div></div>`,
    rodape: html`${botaoSalvar()}${p || podeEscrever() ? html`<button class="btn" data-relatorio>Gerar relatório de entrega</button>` : ""}${espaco}${botaoExcluir(!!p)}`,
    montar: (f, fechar, L) => {
      melhorarFormulario(f);
      ligarNovoCliente(f);
      const box = $("#etapasBox", L) as HTMLElement;
      const equipeOps = opcoesEquipe("Sem responsável");
      const desenhar = (): void => {
        ($("#padrao", L) as HTMLElement).hidden = etapas.length > 0;
        $("#progTxt", L)!.textContent = etapas.length ? `${progressoDe(etapas)}% concluído` : "";
        box.innerHTML = etapas.length
          ? String(html`${etapas.map(
              (e, i) => html`<div class="etapa" data-i="${i}">
          <div class="et-h"><span class="et-n num">${String(i + 1).padStart(2, "0")}</span><input data-k="titulo" value="${e.titulo}" placeholder="Nome da etapa" aria-label="${"Nome da etapa " + (i + 1)}">
            <select data-k="status" aria-label="Situação da etapa">${Object.entries(ETAPA_STATUS).map(([k, x]) => html`<option value="${k}"${raw(e.status === k ? " selected" : "")}>${x[0]}</option>`)}</select>
            <span class="et-a"><button type="button" class="btn ghost" data-mv="-1" aria-label="Subir etapa"${raw(i === 0 ? " disabled" : "")}>↑</button><button type="button" class="btn ghost" data-mv="1" aria-label="Descer etapa"${raw(i === etapas.length - 1 ? " disabled" : "")}>↓</button><button type="button" class="btn ghost" data-rmetapa aria-label="Remover etapa">×</button></span></div>
          <div class="fields">
            <div class="field"><label>Início</label><input type="date" data-k="inicio" value="${e.inicio ?? ""}"></div><div class="field"><label>Término previsto</label><input type="date" data-k="fim" value="${e.fim ?? ""}"></div>
            <div class="field full"><label>Responsável</label><select data-k="responsavel_id">${equipeOps.map(([val, rot]) => html`<option value="${val}"${raw(String(val) === (e.responsavel_id ?? "") ? " selected" : "")}>${rot}</option>`)}</select></div>
            <div class="field full"><label>O que acontece nesta etapa</label><textarea data-k="descricao">${e.descricao ?? ""}</textarea></div>
            <div class="field full"><label>Entregáveis (um por linha)</label><textarea data-k="entregaveis">${e.entregaveis ?? ""}</textarea></div>
          </div></div>`,
            )}`)
          : String(html`<p class="sub" style="margin:8px 0 0">Nenhuma etapa ainda. Comece pelas etapas padrão e ajuste ao projeto, ou adicione uma a uma.</p>`);
      };
      const editar = (e: Event): void => {
        const el = (e.target as Element).closest<HTMLInputElement>("[data-k]");
        const d = (e.target as Element).closest<HTMLElement>(".etapa");
        const etapa = d ? etapas[Number(d.dataset.i)] : undefined;
        if (!el || !etapa) return;
        const k = el.dataset.k as "titulo" | "status" | "inicio" | "fim" | "responsavel_id" | "descricao" | "entregaveis";
        (etapa as Record<string, unknown>)[k] = k === "inicio" || k === "fim" || k === "responsavel_id" ? el.value || null : el.value;
        if (k === "status") $("#progTxt", L)!.textContent = `${progressoDe(etapas)}% concluído`;
      };
      box.addEventListener("input", editar);
      box.addEventListener("change", editar);
      box.addEventListener("click", (e) => {
        const d = (e.target as Element).closest<HTMLElement>(".etapa");
        if (!d) return;
        const i = Number(d.dataset.i);
        const mv = (e.target as Element).closest<HTMLElement>("[data-mv]");
        if (mv) {
          const j = i + Number(mv.dataset.mv);
          const a = etapas[i], b = etapas[j];
          if (!a || !b) return;
          etapas[i] = b;
          etapas[j] = a;
          return desenhar();
        }
        if ((e.target as Element).closest("[data-rmetapa]")) {
          etapas.splice(i, 1);
          desenhar();
        }
      });
      $("#addEtapa", L)?.addEventListener("click", () => {
        etapas.push({ titulo: "", status: "a_fazer", responsavel_id: fv(f, "responsavel_id") || null, inicio: null, fim: null, descricao: null, entregaveis: null });
        desenhar();
        box.lastElementChild?.querySelector("input")?.focus();
      });
      $("#padrao", L)?.addEventListener("click", async () => {
        const sugeridas = await tentar(() => api.projetos.etapasPadrao(fv(f, "inicio") || undefined, fv(f, "entrega") || undefined));
        if (!sugeridas) return;
        sugeridas.forEach((e) => etapas.push({ titulo: e.titulo, status: "a_fazer", responsavel_id: fv(f, "responsavel_id") || null, inicio: e.inicio, fim: e.fim, descricao: e.descricao, entregaveis: e.entregaveis }));
        desenhar();
        toast("Etapas padrão adicionadas. Ajuste nomes e datas ao projeto.");
      });
      desenhar();
      (f.elements.namedItem("negocio_id") as HTMLSelectElement).addEventListener("change", () => {
        const n = dados.negocios.find((x) => x.id === fv(f, "negocio_id"));
        if (!n) return;
        const titulo = f.elements.namedItem("titulo") as HTMLInputElement;
        if (!titulo.value) titulo.value = n.titulo;
        (f.elements.namedItem("cliente_id") as HTMLSelectElement).value = n.cliente_id;
      });

      const coletar = async (): Promise<ProjetoEntrada | null> => {
        const titulo = fv(f, "titulo");
        if (!titulo) return avisar("Dê um nome ao projeto.");
        if (!fv(f, "cliente_id")) return avisar("Escolha o cliente.");
        const clienteId = await resolverCliente(f);
        if (!clienteId) return null;
        return {
          titulo, cliente_id: clienteId, negocio_id: fv(f, "negocio_id") || null, orcamento_id: atual?.orcamento_id ?? inicial.orcamento_id ?? null,
          status: fv(f, "status") as ProjetoEntrada["status"], responsavel_id: fv(f, "responsavel_id") || null, inicio: fv(f, "inicio") || null, entrega: fv(f, "entrega") || null,
          objetivo: fv(f, "objetivo") || null, escopo: fv(f, "escopo") || null, fora_escopo: fv(f, "fora_escopo") || null, pos_entrega: fv(f, "pos_entrega") || null,
          etapas: etapas.map((e) => ({ ...e, titulo: e.titulo || "Etapa" })),
        };
      };
      const persistir = (corpo: ProjetoEntrada) =>
        gravar({
          recarregar: ["projetos", "negocios"], mensagem: "Projeto salvo",
          operacao: () => (atual ? api.projetos.atualizar(atual.id, { ...corpo, versao: atual.versao }) : api.projetos.criar(corpo)),
        });

      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;
        const textoOriginal = botao.textContent;

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        botao.innerHTML = '<span class="spinner"></span> Salvando…';

        try {
          const corpo = await coletar();
          if (corpo && (await persistir(corpo))) fechar();
          else {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Salvar";
          }
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Salvar";
        }
      });
      $("[data-relatorio]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;
        const textoOriginal = botao.textContent;

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        botao.innerHTML = '<span class="spinner"></span> Gerando…';

        try {
          const corpo = await coletar();
          if (!corpo) {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Gerar relatório de entrega";
            return;
          }
          const salvo = await persistir(corpo);
          if (!salvo) {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Gerar relatório de entrega";
            return;
          }
          atual = salvo;
          if ((await tentar(() => api.projetos.relatorio(salvo.id))) !== null) {
            toast("Relatório baixado. Abra no navegador e use Imprimir → Salvar como PDF.");
          } else {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Gerar relatório de entrega";
          }
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Gerar relatório de entrega";
        }
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (p) void excluir({ recarregar: ["projetos", "tarefas"], mensagem: "Projeto excluído", fechar, operacao: () => api.projetos.excluir(p.id) });
      });

    },
  });
}

async function projetoDoNegocio(negocioId: string): Promise<void> {
  const m = await tentar(() => api.projetos.modelo(negocioId));
  if (m) formProjeto(undefined, m);
}

registrarFormulario("projeto", (existente, inicial) => formProjeto(existente, inicial));
registrarFormulario("projetoDoNegocio", (id) => void projetoDoNegocio(id));
registrarAcao("novoProjeto", () => formProjeto());
registrarAcao("projetoDoNegocio", (alvo) => void projetoDoNegocio(alvo.dataset.id ?? ""));
registrarAcao("filtroProj", (alvo) => {
  ui.projStatus = alvo.dataset.valor ?? "ativos";
  render();
});
registrarAbertura("projeto", (id) => {
  const p = dados.projetos.find((x) => x.id === id);
  if (p) formProjeto(p);
});

