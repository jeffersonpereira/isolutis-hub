import { api } from "@/api/endpoints";
import type { Tarefa, TarefaEntrada } from "@/api/tipos";
import { $ } from "@/core/dom";
import { dataBR, hoje, iniciais, pluralizar } from "@/core/formato";
import { html, raw, type Safe } from "@/core/html";
import { COLUNAS_TAREFA, PRIORIDADES } from "@/domain/constantes";
import { dados, eu, nomeCliente, nomeMembro, podeEscrever, ui } from "@/state/estado";
import { recarregar, registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura, registrarSoltar } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco, opcoesClientes, opcoesEquipe } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { avisar, toast } from "@/ui/toast";
import { botaoNovo } from "./comum";

registrarConsulta("tarefas", (id) => dados.tarefas.find((t) => t.id === id));

const PESO_PRIORIDADE: Record<string, number> = { alta: 0, media: 1, baixa: 2 };
const LIMITE_CONCLUIDAS = 12;

function ordenar(a: Tarefa, b: Tarefa): number {
  return (
    (PESO_PRIORIDADE[a.prioridade] ?? 1) - (PESO_PRIORIDADE[b.prioridade] ?? 1) ||
    (a.prazo ?? "9999").localeCompare(b.prazo ?? "9999") ||
    a.criado_em.localeCompare(b.criado_em)
  );
}

const vinculo = (t: Tarefa): string => (t.projeto_id ? (dados.projetos.find((p) => p.id === t.projeto_id)?.titulo ?? "") : t.cliente_id ? nomeCliente(t.cliente_id) : "");

function vista(): Safe {
  const h = hoje();
  const q = ui.tarefaBusca.toLowerCase();
  const p = ui.tarefaPessoa;
  const escrever = podeEscrever();
  const filtradas = dados.tarefas.filter(
    (t) =>
      (p === "todas" || (p === "minhas" ? t.responsavel_id === eu.id : p === "sem" ? !t.responsavel_id : t.responsavel_id === p)) &&
      (!q || [t.titulo, t.descricao, t.cliente_id ? nomeCliente(t.cliente_id) : "", dados.projetos.find((x) => x.id === t.projeto_id)?.titulo].join(" ").toLowerCase().includes(q)),
  );
  const atrasadas = dados.tarefas.filter((t) => t.coluna !== "concluido" && t.prazo && t.prazo < h).length;
  const minhas = dados.tarefas.filter((t) => t.coluna !== "concluido" && t.responsavel_id === eu.id).length;
  const filtros: Array<[string, string]> = [["todas", "Todas"], ["minhas", "Minhas"], ...dados.equipe.filter((m) => m.ativo && m.id !== eu.id).map((m): [string, string] => [m.id, m.nome.split(" ")[0] ?? m.nome]), ["sem", "Sem responsável"]];
  return html`<div class="head"><div><h1>Tarefas da equipe</h1><p>${minhas} ${pluralizar(minhas, "tarefa", "tarefas")} com você${atrasadas ? html` · <b style="color:var(--bad)">${atrasadas} ${pluralizar(atrasadas, "atrasada", "atrasadas")}</b>` : ""}. Arraste um cartão para mudar de coluna.</p></div>
    <div class="tools"><input class="search" id="tbusca" data-busca="tarefaBusca" type="search" placeholder="Buscar tarefa, cliente ou projeto" value="${ui.tarefaBusca}">${botaoNovo("novaTarefa", "Nova tarefa")}</div></div>
  <div class="seg" role="group" aria-label="Filtrar por pessoa" style="margin-bottom:14px;flex-wrap:wrap">${filtros.map(([k, r]) => html`<button data-act="filtroPessoa" data-valor="${k}" aria-pressed="${p === k}">${r}</button>`)}</div>
  ${!dados.tarefas.length ? html`<div class="empty" style="margin-bottom:14px"><b>Nenhuma tarefa ainda</b>Crie as tarefas da semana, escolha quem é o responsável e o prazo. Cada pessoa filtra pelas suas em "Minhas".${escrever ? html`<br><button class="btn primary" data-act="novaTarefa">Criar a primeira tarefa</button>` : ""}</div>` : ""}
  <div class="board tboard">${COLUNAS_TAREFA.map((c) => {
    const daColuna = filtradas.filter((t) => t.coluna === c.id);
    let ts = [...daColuna];
    let escondidas = 0;
    if (c.id === "concluido") {
      ts.sort((a, b) => (b.concluida_em ?? "").localeCompare(a.concluida_em ?? ""));
      if (!ui.tarefaConcluidasTodas && ts.length > LIMITE_CONCLUIDAS) {
        escondidas = ts.length - LIMITE_CONCLUIDAS;
        ts = ts.slice(0, LIMITE_CONCLUIDAS);
      }
    } else ts.sort(ordenar);
    return html`<section class="col tcol ${c.id}" data-coluna="${c.id}"><div class="col-h"><b>${c.nome} <span class="num">${daColuna.length}</span></b>${c.id !== "concluido" && escrever ? html`<button class="btn ghost" data-act="novaTarefa" data-coluna="${c.id}" aria-label="${"Nova tarefa em " + c.nome}" style="padding:0 6px">+</button>` : ""}</div>
      ${ts.map((t) => cartao(t, h, escrever))}
      ${escondidas ? html`<button class="btn ghost" data-act="verConcluidas">Mostrar mais ${escondidas}</button>` : ""}
      ${c.id === "concluido" && ui.tarefaConcluidasTodas && daColuna.length > LIMITE_CONCLUIDAS ? html`<button class="btn ghost" data-act="verConcluidas">Mostrar só as recentes</button>` : ""}
    </section>`;
  })}</div>`;
}

function cartao(t: Tarefa, h: string, escrever: boolean): Safe {
  const atrasada = t.coluna !== "concluido" && !!t.prazo && t.prazo < h;
  const hojeV = t.prazo === h;
  const [pr, pcls] = PRIORIDADES[t.prioridade] ?? PRIORIDADES.media!;
  const resp = nomeMembro(t.responsavel_id);
  const feitos = t.checklist.filter((i) => i.feito).length;
  const vinc = vinculo(t);
  return html`<article class="card tcard p-${t.prioridade}" draggable="${escrever}" data-id="${t.id}" data-open="tarefa:${t.id}" tabindex="0">
    <span class="t">${t.titulo}</span>
    ${vinc ? html`<span class="sub">${vinc}</span>` : ""}
    <span class="m"><span>${t.prioridade !== "media" ? html`<span class="pill ${pcls}">${pr}</span> ` : ""}${t.checklist.length ? html`<span class="sub">☑ ${feitos}/${t.checklist.length}</span>` : ""}</span><span class="${atrasada ? "late" : ""}" style="${hojeV ? "color:var(--warn);font-weight:600" : ""}">${t.prazo ? (atrasada ? "atrasada · " : hojeV ? "hoje · " : "") + dataBR(t.prazo).slice(0, 5) : ""}</span></span>
    ${resp ? html`<span class="tresp"><i class="av mini">${iniciais(resp)}</i>${resp.split(" ")[0]}</span>` : html`<span class="sub">sem responsável</span>`}
  </article>`;
}

registrarVista({
  id: "tarefas",
  nome: "Tarefas",
  grupo: "Operação",
  contagem: () => dados.tarefas.filter((t) => t.coluna !== "concluido" && t.responsavel_id === eu.id).length,
  desenhar: vista,
});

type ItemCk = { id?: string | null; texto: string; feito: boolean };

export function formTarefa(t?: Tarefa, colunaInicial = "a_fazer"): void {
  const checklist: ItemCk[] = (t?.checklist ?? []).map((i) => ({ id: i.id, texto: i.texto, feito: i.feito }));
  const projs = dados.projetos.filter((p) => p.status !== "entregue" || p.id === t?.projeto_id);
  abrirGaveta({
    titulo: t ? t.titulo : "Nova tarefa",
    registro: t ? { recurso: "tarefas", id: t.id, versao: t.versao } : null,
    autoria: linhaAutoria(t),
    corpo: html`<div class="fields">
      ${campo("O que precisa ser feito", inp("titulo", t?.titulo, 'placeholder="Ex.: Enviar proposta revisada para a distribuidora"'), true)}
      ${campo("Coluna", sel("coluna", COLUNAS_TAREFA.map((c) => [c.id, c.nome] as const), t?.coluna ?? colunaInicial))}
      ${campo("Responsável", sel("responsavel_id", opcoesEquipe("Sem responsável", true), t ? (t.responsavel_id ?? "") : eu.id))}
      ${campo("Prazo", inp("prazo", t?.prazo, 'type="date"'))}
      ${campo("Prioridade", sel("prioridade", Object.entries(PRIORIDADES).map(([k, v]) => [k, v[0]] as const), t?.prioridade ?? "media"))}
      ${campo("Cliente", sel("cliente_id", opcoesClientes("Nenhum"), t?.cliente_id))}
      ${campo("Projeto", sel("projeto_id", [["", "Nenhum"], ...projs.map((p) => [p.id, `${p.titulo} · ${p.cliente_nome}`] as const)], t?.projeto_id))}
      ${campo("Detalhes", area("descricao", t?.descricao, "Contexto, links, o que é preciso para considerar pronta…"), true)}
    </div>
    <div><h2 style="margin-bottom:6px">Checklist</h2><div id="ckBox" class="ck"></div>
      <div style="display:flex;gap:8px;margin-top:8px"><input id="ckNovo" class="search" style="flex:1;width:auto" placeholder="Adicionar item e apertar Enter"><button class="btn" type="button" id="ckAdd">Adicionar</button></div></div>`,
    rodape: html`${botaoSalvar()}${t && t.coluna !== "concluido" && podeEscrever() ? html`<button class="btn" data-concluir>Concluir</button>` : ""}${espaco}${botaoExcluir(!!t)}`,
    montar: (f, fechar, L) => {
      const box = $("#ckBox", L) as HTMLElement;
      const novo = $<HTMLInputElement>("#ckNovo", L)!;
      const desenhar = (): void => {
        box.innerHTML = checklist.length
          ? String(html`${checklist.map((i, k) => html`<label class="ck-i"><input type="checkbox" data-ck="${k}"${raw(i.feito ? " checked" : "")}><span style="${i.feito ? "text-decoration:line-through;color:var(--muted)" : ""}">${i.texto}</span><button type="button" class="btn ghost" data-ckrm="${k}" aria-label="Remover item" style="padding:0 6px;margin-left:auto">×</button></label>`)}`)
          : '<p class="sub" style="margin:0">Sem itens. Use para quebrar a tarefa em passos.</p>';
      };
      const adicionar = (): void => {
        const v = novo.value.trim();
        if (!v) return;
        checklist.push({ texto: v, feito: false });
        novo.value = "";
        desenhar();
        novo.focus();
      };
      $("#ckAdd", L)?.addEventListener("click", adicionar);
      novo.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          adicionar();
        }
      });
      box.addEventListener("change", (e) => {
        const k = (e.target as HTMLElement).dataset.ck;
        const item = k === undefined ? undefined : checklist[Number(k)];
        if (item) {
          item.feito = (e.target as HTMLInputElement).checked;
          desenhar();
        }
      });
      box.addEventListener("click", (e) => {
        const b = (e.target as Element).closest<HTMLElement>("[data-ckrm]");
        if (b) {
          e.preventDefault();
          checklist.splice(Number(b.dataset.ckrm), 1);
          desenhar();
        }
      });
      desenhar();
      (f.elements.namedItem("projeto_id") as HTMLSelectElement).addEventListener("change", () => {
        const p = dados.projetos.find((x) => x.id === fv(f, "projeto_id"));
        const cli = f.elements.namedItem("cliente_id") as HTMLSelectElement;
        if (p && !cli.value) cli.value = p.cliente_id;
      });
      const coletar = (colunaForcada?: string): TarefaEntrada | null => {
        const titulo = fv(f, "titulo");
        if (!titulo) return avisar("Descreva o que precisa ser feito.");
        return {
          titulo, coluna: (colunaForcada ?? fv(f, "coluna")) as TarefaEntrada["coluna"], responsavel_id: fv(f, "responsavel_id") || null, prazo: fv(f, "prazo") || null,
          prioridade: fv(f, "prioridade") as TarefaEntrada["prioridade"], cliente_id: fv(f, "cliente_id") || null, projeto_id: fv(f, "projeto_id") || null,
          descricao: fv(f, "descricao") || null, checklist,
        };
      };
      const salvar = async (corpo: TarefaEntrada, mensagem: string): Promise<void> => {
        await gravar({
          recarregar: ["tarefas"], mensagem, fechar,
          operacao: () => (t ? api.tarefas.atualizar(t.id, { ...corpo, versao: t.versao }) : api.tarefas.criar(corpo)),
        });
      };
      $("[data-salvar]", L)?.addEventListener("click", async () => {
        const corpo = coletar();
        if (corpo) await salvar(corpo, t ? "Tarefa salva" : "Tarefa criada");
      });
      $("[data-concluir]", L)?.addEventListener("click", async () => {
        const corpo = coletar("concluido");
        if (corpo) await salvar(corpo, "Tarefa concluída");
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (t) void excluir({ recarregar: ["tarefas"], mensagem: "Tarefa excluída", fechar, operacao: () => api.tarefas.excluir(t.id) });
      });
    },
  });
}

async function moverTarefa(id: string, coluna: string): Promise<void> {
  const t = dados.tarefas.find((x) => x.id === id);
  if (!t || t.coluna === coluna) return;
  const movida = await tentar(() => api.tarefas.mover(id, { coluna: coluna as Tarefa["coluna"] & ("a_fazer" | "fazendo" | "revisao" | "concluido"), versao: t.versao }));
  if (!movida) return render();
  await recarregar("tarefas");
  toast(coluna === "concluido" ? "Tarefa concluída" : "Movida para " + (COLUNAS_TAREFA.find((c) => c.id === coluna)?.nome ?? coluna));
}

registrarAcao("novaTarefa", (alvo) => formTarefa(undefined, alvo.dataset.coluna ?? "a_fazer"));
registrarAcao("filtroPessoa", (alvo) => {
  ui.tarefaPessoa = alvo.dataset.valor ?? "todas";
  render();
});
registrarAcao("verConcluidas", () => {
  ui.tarefaConcluidasTodas = !ui.tarefaConcluidasTodas;
  render();
});
registrarAbertura("tarefa", (id) => {
  const t = dados.tarefas.find((x) => x.id === id);
  if (t) formTarefa(t);
});
registrarSoltar("coluna", (id, coluna) => void moverTarefa(id, coluna));

