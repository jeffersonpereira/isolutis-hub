import { api } from "@/api/endpoints";
import type { Negocio, NegocioEntrada } from "@/api/tipos";
import { $ } from "@/core/dom";
import { brl, brlCurto, dataBR, hoje } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { numero, paraCampo } from "@/core/numero";
import { ABERTAS, ETAPAS, MOTIVOS_PERDA, ORC_STATUS, ORIGENS, etapaNome } from "@/domain/constantes";
import { botaoWa } from "@/domain/whatsapp";
import { dados, eu, nomeMembro, podeEscrever, ui } from "@/state/estado";
import { recarregar, registrarVista, render } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { tentar } from "@/ui/erros";
import { registrarAbertura, registrarSoltar } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco, ligarNovoCliente, opcoesEquipe, resolverCliente, seletorCliente } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { melhorarFormulario } from "@/ui/acessibilidade";
import { toast } from "@/ui/toast";
import { botaoNovo } from "./comum";
import { abrirFormulario, registrarFormulario } from "./ponte";

registrarConsulta("negocios", (id) => dados.negocios.find((n) => n.id === id));

export function valorNegocio(n: Pick<Negocio, "valor" | "mensal">): string {
  const p: string[] = [];
  if (numero(n.valor)) p.push(brl(n.valor));
  if (numero(n.mensal)) p.push(brl(n.mensal) + "/mês");
  return p.join(" + ") || "sem valor";
}

function vista(): Safe {
  const etapas = ui.mostrarFechados ? ETAPAS : ETAPAS.filter((e) => ABERTAS.includes(e.id));
  const h = hoje();
  const escrever = podeEscrever();
  return html`<div class="head"><div><h1>Negócios e funil de vendas</h1><p>Arraste um cartão para mudar a etapa. Ao marcar como Ganho, o Hub Comercial oferece lançar o faturamento.</p></div>
    <div class="tools"><label class="check"><input type="checkbox" id="fechados" data-act="alternarFechados"${ui.mostrarFechados ? " checked" : ""}> Mostrar ganhos e perdidos</label>${botaoNovo("novoNegocio", "Novo negócio")}</div></div>
  ${!dados.negocios.length ? html`<div class="empty"><b>Nenhum negócio no funil</b>Cada conversa comercial vira um negócio: começa como Lead, passa pelo diagnóstico e pela proposta, e termina como Ganho ou Perdido.${escrever ? html`<br><button class="btn primary" data-act="novoNegocio">Abrir o primeiro negócio</button>` : ""}</div>` : ""}
  <div class="board">${etapas.map((e) => {
    const ns = dados.negocios.filter((n) => n.etapa === e.id).sort((a, b) => (a.previsao ?? "9").localeCompare(b.previsao ?? "9"));
    const total = ns.reduce((s, n) => s + numero(n.valor), 0);
    const totalM = ns.reduce((s, n) => s + numero(n.mensal), 0);
    return html`<section class="col ${e.id}" data-etapa="${e.id}"><div class="col-h"><b>${e.nome} <span class="num">${ns.length}</span></b><span class="num">${brlCurto(total)}${totalM ? " + " + brlCurto(totalM) + "/mês" : ""}</span></div>
      ${ns.map(
        (n) => html`<article class="card" draggable="${escrever}" data-id="${n.id}" data-open="negocio:${n.id}" tabindex="0"><span class="t">${n.titulo}</span><span class="sub">${n.cliente_nome}</span>
        <span class="m"><span class="num">${valorNegocio(n)}</span><span class="${ABERTAS.includes(n.etapa) && n.previsao && n.previsao < h ? "late" : ""}">${n.previsao ? dataBR(n.previsao) : ""}</span></span>${n.responsavel_id ? html`<span class="sub">${nomeMembro(n.responsavel_id)}</span>` : ""}</article>`,
      )}
    </section>`;
  })}</div>`;
}

registrarVista({
  id: "negocios",
  permissao: "comercial",
  nome: "Funil de Vendas",
  grupo: "Comercial",
  contagem: () => dados.negocios.filter((n) => ABERTAS.includes(n.etapa)).length,
  desenhar: vista,
});

type Inicial = Partial<Negocio> & { cliente_id?: string };

export function formNegocio(n: Inicial = { etapa: "lead" }, existente?: Negocio): void {
  const reg = existente ?? (n.id ? (n as Negocio) : undefined);
  const orcs = reg ? dados.orcamentos.filter((o) => o.negocio_id === reg.id) : [];
  const cliente = dados.clientes.find((c) => c.id === n.cliente_id);
  const projeto = reg ? dados.projetos.find((p) => p.negocio_id === reg.id) : undefined;
  abrirGaveta({
    titulo: reg ? reg.titulo : "Novo negócio",
    registro: reg ? { recurso: "negocios", id: reg.id, versao: reg.versao } : null,
    autoria: linhaAutoria(reg),
    corpo: html`<div class="fields">
      ${campo("Título do negócio", inp("titulo", n.titulo, 'placeholder="Ex.: Portal do cliente para a distribuidora"'), true)}
      ${seletorCliente(n.cliente_id)}${campo("Etapa", sel("etapa", ETAPAS.map((e) => [e.id, e.nome] as const), n.etapa ?? "lead"))}
      ${campo("Valor do projeto (R$)", inp("valor", paraCampo(n.valor), 'inputmode="decimal" placeholder="0,00"'))}${campo("Manutenção mensal (R$)", inp("mensal", paraCampo(n.mensal), 'inputmode="decimal" placeholder="0,00"'))}
      ${campo("Previsão de fechamento", inp("previsao", n.previsao, 'type="date"'))}${campo("Responsável", sel("responsavel_id", opcoesEquipe("Sem responsável", true), n.responsavel_id ?? (reg ? "" : eu.id)))}
      ${campo("Origem", sel("origem", [["", "—"], ...ORIGENS.map((o) => [o, o] as const)], n.origem))}
      <div class="field" id="motivoBox"${n.etapa === "perdido" ? "" : " hidden"}><label>Motivo da perda</label>${sel("motivo_perda", [["", "—"], ...MOTIVOS_PERDA.map((m) => [m, m] as const)], n.motivo_perda)}</div>
      ${campo("Anotações", area("obs", n.obs, "Dores do cliente, próximos passos, quem decide…"), true)}</div>
      ${orcs.length ? html`<div class="related"><h3>Orçamentos deste negócio</h3>${orcs.map((o) => html`<div class="li" data-open="orcamento:${o.id}"><span class="t">Nº ${o.numero}</span><span class="sub">${ORC_STATUS[o.status_exibido]?.[0]} · ${brl(o.total_projeto)}</span></div>`)}</div>` : ""}`,
    rodape: html`${botaoSalvar()}${reg && cliente ? botaoWa(cliente, "WhatsApp do cliente") : ""}${reg && podeEscrever() ? html`<button class="btn" data-orc>Gerar orçamento</button>` : ""}${reg && reg.etapa === "ganho" ? html`<button class="btn" data-proj>${projeto ? "Ver projeto" : "Abrir projeto"}</button>` : ""}${espaco}${botaoExcluir(!!reg)}`,
    montar: (f, fechar, L) => {
      // Melhorar acessibilidade
      melhorarFormulario(f);

      ligarNovoCliente(f);
      const etapaSel = f.elements.namedItem("etapa") as HTMLSelectElement;
      etapaSel.addEventListener("change", () => {
        const motivo = $("#motivoBox");
        if (motivo) motivo.hidden = etapaSel.value !== "perdido";
      });

      // Salvar com validação e loading visual
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const botao = e.target as HTMLButtonElement;

        // Validar
        const titulo = fv(f, "titulo");
        if (!titulo) {
          toast("Dê um título ao negócio.");
          return;
        }
        if (!fv(f, "cliente_id")) {
          toast("Escolha o cliente.");
          return;
        }
        const etapa = fv(f, "etapa") as NegocioEntrada["etapa"];
        if (etapa === "perdido" && !fv(f, "motivo_perda")) {
          toast("Informe o motivo da perda.");
          return;
        }

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        const textoOriginal = botao.textContent;
        botao.innerHTML = '<span class="spinner"></span> Salvando…';

        try {
          const clienteId = await resolverCliente(f);
          if (!clienteId) {
            botao.disabled = false;
            botao.classList.remove("loading");
            botao.innerHTML = textoOriginal || "Salvar";
            return;
          }

          const corpo: NegocioEntrada = {
            titulo,
            cliente_id: clienteId,
            etapa,
            valor: numero(fv(f, "valor")),
            mensal: numero(fv(f, "mensal")),
            previsao: fv(f, "previsao") || null,
            responsavel_id: fv(f, "responsavel_id") || null,
            origem: (fv(f, "origem") || null) as NegocioEntrada["origem"],
            motivo_perda: (fv(f, "motivo_perda") || null) as NegocioEntrada["motivo_perda"],
            obs: fv(f, "obs") || null,
          };

          const salvo = await gravar({
            recarregar: ["negocios", "clientes"],
            mensagem: "Negócio salvo",
            fechar,
            operacao: () =>
              reg
                ? api.negocios.atualizar(reg.id, { ...corpo, versao: reg.versao })
                : api.negocios.criar(corpo),
          });

          // Ganhou agora e ainda não tem lançamentos: oferece lançar o faturamento.
          if (salvo && salvo.etapa === "ganho" && reg?.etapa !== "ganho" && !salvo.faturado) {
            oferecerFaturamento(salvo);
          }
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Salvar";
        }
      });

      $("[data-orc]", L)?.addEventListener("click", () => reg && abrirFormulario("orcamento", { cliente_id: reg.cliente_id, negocio_id: reg.id }));
      $("[data-proj]", L)?.addEventListener("click", () => reg && (projeto ? abrirFormulario("projeto", projeto) : abrirFormulario("projetoDoNegocio", reg.id)));
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (reg) void excluir({ recarregar: ["negocios", "clientes"], mensagem: "Negócio excluído", fechar, operacao: () => api.negocios.excluir(reg.id) });
      });
    },
  });
}

export async function moverEtapa(id: string, etapa: string): Promise<void> {
  const n = dados.negocios.find((x) => x.id === id);
  if (!n || n.etapa === etapa) return;
  // Perdido exige o motivo: abre o formulário já na etapa Perdido (só grava quando a pessoa escolher o motivo).
  if (etapa === "perdido") return formNegocio({ ...n, etapa: "perdido", motivo_perda: null }, n);
  const atualizado = await tentar(() => api.negocios.mover(id, { etapa: etapa as NegocioEntrada["etapa"], versao: n.versao }));
  if (!atualizado) return render();
  await recarregar("negocios");
  toast("Movido para " + etapaNome(etapa));
  if (etapa === "ganho" && !atualizado.faturado) oferecerFaturamento(atualizado);
}

/** Venda fechada: abre a gaveta de lançamento de faturamento com os valores do orçamento aprovado (ou do negócio). */
export function oferecerFaturamento(n: Negocio): void {
  const orc = dados.orcamentos.find((o) => o.negocio_id === n.id && o.status === "aprovado");
  abrirFormulario("faturamento", {
    cliente_id: n.cliente_id, titulo: n.titulo, negocio_id: n.id, orcamento_id: orc?.id ?? null,
    unico: orc ? orc.total_projeto : numero(n.valor), mensal: orc ? orc.total_mensal : numero(n.mensal),
  });
}

registrarFormulario("negocio", (inicial) => formNegocio(inicial));
registrarAcao("novoNegocio", () => formNegocio({ etapa: "lead" }));
registrarAcao("alternarFechados", (alvo) => {
  ui.mostrarFechados = (alvo as HTMLInputElement).checked;
  render();
});
registrarAbertura("negocio", (id) => {
  const n = dados.negocios.find((x) => x.id === id);
  if (n) formNegocio(n, n);
});
registrarSoltar("etapa", (id, etapa) => void moverEtapa(id, etapa));
