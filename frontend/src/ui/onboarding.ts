/**
 * Wizard de onboarding para administradores de empresa nova.
 * Exibido em vez do painel quando `empresa.onboarding_concluido === false`.
 */
import { api } from "@/api/endpoints";
import { ErroApi } from "@/api/http";
import type { Usuario } from "@/api/tipos";

export interface EstadoApp {
  usuario: (Usuario & { admin?: boolean }) | null;
  empresa: { id: string; nome: string; onboarding_concluido?: boolean } | null;
}

/** Verifica se o wizard de onboarding deve ser exibido. */
export function detectarOnboarding(estado: EstadoApp): boolean {
  return (estado.usuario?.admin === true) && (estado.empresa?.onboarding_concluido === false);
}

// ─── Estado interno do wizard ─────────────────────────────────────────────────

type Etapa = 1 | 2 | 3;

const estado = {
  etapa: 1 as Etapa,
  nomeEmpresa: "",
  segmento: "",
  produtos: [{ nome: "", preco: "" }] as Array<{ nome: string; preco: string }>,
};

let raiz: HTMLElement | null = null;
let appEl: HTMLElement | null = null;
let resolverConcluido: (() => void) | null = null;

// ─── Renderização ─────────────────────────────────────────────────────────────

function barra(): string {
  return `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:28px">
      ${([1, 2, 3] as Etapa[]).map((n) => `
        <div style="display:flex;align-items:center;gap:8px">
          <div style="
            width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
            justify-content:center;font-size:13px;font-weight:600;flex:none;
            background:${n < estado.etapa ? "var(--ok)" : n === estado.etapa ? "var(--accent)" : "var(--sunk)"};
            color:${n <= estado.etapa ? "var(--accent-ink)" : "var(--muted)"};
            border:${n === estado.etapa ? "2px solid var(--accent)" : "2px solid transparent"}
          ">${n < estado.etapa ? "✓" : n}</div>
          ${n < 3 ? `<div style="height:2px;width:40px;background:${n < estado.etapa ? "var(--ok)" : "var(--line)"}"></div>` : ""}
        </div>`).join("")}
      <span style="margin-left:auto;font-size:var(--text-xs);color:var(--muted)">Etapa ${estado.etapa} de 3</span>
    </div>`;
}

function renderEtapa1(): string {
  return `
    <form id="obForm1" novalidate>
      <h2 style="margin:0 0 4px;font-size:1.1rem;font-weight:700">Perfil da empresa</h2>
      <p style="margin:0 0 20px;font-size:var(--text-xs);color:var(--muted)">
        Diga como sua empresa se chama. Essa informação aparece nos relatórios e orçamentos.
      </p>
      <div class="fields">
        <div class="field full">
          <label for="obNome">Nome comercial <span style="color:var(--bad-texto)">*</span></label>
          <input id="obNome" name="nome" maxlength="150" required
            placeholder="Ex.: Acme Soluções Digitais"
            value="${esc(estado.nomeEmpresa)}"
            autocomplete="organization">
        </div>
        <div class="field full">
          <label for="obSegmento">Segmento <span style="font-weight:400;color:var(--muted)">(opcional)</span></label>
          <input id="obSegmento" name="segmento" maxlength="100"
            placeholder="Ex.: Desenvolvimento web, Consultoria de TI…"
            value="${esc(estado.segmento)}">
        </div>
      </div>
      <p id="obMsg1" style="min-height:1.2em;font-size:var(--text-xs);color:var(--bad-texto);margin:8px 0 0"></p>
      <div style="margin-top:20px;display:flex;justify-content:flex-end">
        <button class="btn primary" id="obProx1" type="submit">Próximo →</button>
      </div>
    </form>`;
}

function renderProdutoLinha(i: number, p: { nome: string; preco: string }): string {
  return `
    <div id="obProd${i}" style="display:flex;gap:8px;align-items:flex-start">
      <div class="field" style="flex:1">
        <label for="obPNome${i}" style="font-size:var(--text-xs)">Nome</label>
        <input id="obPNome${i}" maxlength="120" placeholder="Ex.: Site institucional"
          value="${esc(p.nome)}">
      </div>
      <div class="field" style="width:140px">
        <label for="obPPreco${i}" style="font-size:var(--text-xs)">Preço (R$)</label>
        <input id="obPPreco${i}" inputmode="decimal" placeholder="0,00"
          value="${esc(p.preco)}">
      </div>
      ${i > 0 ? `<button type="button" class="btn ghost" id="obRemProd${i}" style="padding:4px 8px;margin-top:22px" title="Remover">✕</button>` : '<div style="width:36px;margin-top:22px"></div>'}
    </div>`;
}

function renderEtapa2(): string {
  const podeMais = estado.produtos.length < 5;
  return `
    <form id="obForm2" novalidate>
      <h2 style="margin:0 0 4px;font-size:1.1rem;font-weight:700">Produtos e serviços iniciais</h2>
      <p style="margin:0 0 20px;font-size:var(--text-xs);color:var(--muted)">
        Cadastre até 5 itens que você vende. Você pode adicionar, editar ou remover depois em
        <b>Produtos</b>.
      </p>
      <div id="obProdLista">
        ${estado.produtos.map((p, i) => renderProdutoLinha(i, p)).join("")}
      </div>
      ${podeMais ? `<button type="button" class="btn" id="obAddProd" style="margin-top:8px;width:100%">+ Adicionar produto/serviço</button>` : ""}
      <p id="obMsg2" style="min-height:1.2em;font-size:var(--text-xs);color:var(--bad-texto);margin:8px 0 0"></p>
      <div style="margin-top:20px;display:flex;gap:8px;justify-content:space-between">
        <button type="button" class="btn ghost" id="obPularEtapa2">Pular esta etapa</button>
        <div style="display:flex;gap:8px">
          <button type="button" class="btn" id="obVolt2">← Voltar</button>
          <button type="submit" class="btn primary" id="obProx2">Próximo →</button>
        </div>
      </div>
    </form>`;
}

const TOUR_ITENS = [
  { icone: "👥", nome: "Clientes", desc: "Cadastre os clientes da empresa e acesse o histórico completo de cada um." },
  { icone: "🎯", nome: "Funil de vendas", desc: "Acompanhe cada negócio em andamento pelas etapas do funil comercial." },
  { icone: "💰", nome: "Faturamento", desc: "Registre recebimentos, controle o que está previsto e monitore o fluxo mensal." },
  { icone: "📋", nome: "Projetos", desc: "Organize os projetos em execução com etapas, responsáveis e datas de entrega." },
];

function renderEtapa3(): string {
  return `
    <div>
      <h2 style="margin:0 0 4px;font-size:1.1rem;font-weight:700">Conheça o Hub Comercial</h2>
      <p style="margin:0 0 20px;font-size:var(--text-xs);color:var(--muted)">
        Tudo pronto! Aqui está um resumo das principais seções que você encontrará no menu lateral.
      </p>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:24px">
        ${TOUR_ITENS.map((item) => `
          <div class="panel" style="display:flex;flex-direction:column;gap:8px">
            <div style="font-size:2rem;line-height:1">${item.icone}</div>
            <div style="font-weight:600;font-size:0.9rem">${item.nome}</div>
            <div style="font-size:var(--text-xs);color:var(--muted)">${item.desc}</div>
          </div>`).join("")}
      </div>
      <p id="obMsg3" style="min-height:1.2em;font-size:var(--text-xs);color:var(--bad-texto);margin:0 0 8px"></p>
      <div style="display:flex;gap:8px;justify-content:space-between">
        <button type="button" class="btn" id="obVolt3">← Voltar</button>
        <button type="button" class="btn primary" id="obComecar">Começar a usar</button>
      </div>
    </div>`;
}

/** Lê os valores dos inputs de produtos do DOM e sincroniza com o estado. */
function lerProdutosDom(): void {
  estado.produtos = estado.produtos.map((_, i) => ({
    nome: (document.getElementById(`obPNome${i}`) as HTMLInputElement | null)?.value.trim() ?? "",
    preco: (document.getElementById(`obPPreco${i}`) as HTMLInputElement | null)?.value.trim() ?? "",
  }));
}

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function render(): void {
  if (!raiz) return;
  raiz.querySelector(".ob-corpo")!.innerHTML = barra() + (() => {
    if (estado.etapa === 1) return renderEtapa1();
    if (estado.etapa === 2) return renderEtapa2();
    return renderEtapa3();
  })();
  ligarEventos();
}

// ─── Eventos ─────────────────────────────────────────────────────────────────

function setMsg(n: 1 | 2 | 3, texto: string): void {
  const el = document.getElementById(`obMsg${n}`);
  if (el) el.textContent = texto;
}

function ligarEventos(): void {
  if (estado.etapa === 1) {
    const form = document.getElementById("obForm1") as HTMLFormElement | null;
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const nome = (document.getElementById("obNome") as HTMLInputElement).value.trim();
      const segmento = (document.getElementById("obSegmento") as HTMLInputElement).value.trim();
      if (!nome) return setMsg(1, "Informe o nome comercial.");
      const botao = document.getElementById("obProx1") as HTMLButtonElement;
      botao.disabled = true;
      setMsg(1, "Salvando…");
      try {
        await api.onboarding.salvarEmpresa(nome, segmento);
        estado.nomeEmpresa = nome;
        estado.segmento = segmento;
        estado.etapa = 2;
        render();
      } catch (err) {
        setMsg(1, err instanceof ErroApi ? err.message : "Não foi possível salvar agora.");
        botao.disabled = false;
      }
    });
  }

  if (estado.etapa === 2) {
    document.getElementById("obVolt2")?.addEventListener("click", () => {
      lerProdutosDom();
      estado.etapa = 1;
      render();
    });

    document.getElementById("obAddProd")?.addEventListener("click", () => {
      lerProdutosDom();
      if (estado.produtos.length < 5) {
        estado.produtos.push({ nome: "", preco: "" });
        render();
      }
    });

    // Botões de remover produto
    estado.produtos.forEach((_, i) => {
      document.getElementById(`obRemProd${i}`)?.addEventListener("click", () => {
        lerProdutosDom();
        estado.produtos.splice(i, 1);
        render();
      });
    });

    const pularOuAvancar = async (pular: boolean): Promise<void> => {
      if (!pular) {
        lerProdutosDom();
        const validos = estado.produtos.filter((p) => p.nome);
        if (validos.length > 0) {
          const botao = document.getElementById("obProx2") as HTMLButtonElement;
          botao.disabled = true;
          setMsg(2, "Salvando…");
          try {
            await api.onboarding.salvarProdutos(
              validos.map((p) => ({ nome: p.nome, preco: p.preco ? Number(p.preco.replace(",", ".")) : null })),
            );
          } catch (err) {
            setMsg(2, err instanceof ErroApi ? err.message : "Não foi possível salvar os produtos.");
            botao.disabled = false;
            return;
          }
        }
      }
      estado.etapa = 3;
      render();
    };

    document.getElementById("obPularEtapa2")?.addEventListener("click", () => void pularOuAvancar(true));

    const form2 = document.getElementById("obForm2") as HTMLFormElement | null;
    form2?.addEventListener("submit", (e) => {
      e.preventDefault();
      void pularOuAvancar(false);
    });
  }

  if (estado.etapa === 3) {
    document.getElementById("obVolt3")?.addEventListener("click", () => {
      estado.etapa = 2;
      render();
    });

    document.getElementById("obComecar")?.addEventListener("click", async () => {
      const botao = document.getElementById("obComecar") as HTMLButtonElement;
      botao.disabled = true;
      setMsg(3, "Finalizando…");
      try {
        await api.onboarding.concluir();
        // Remove o wizard e restaura o app
        if (raiz) {
          raiz.remove();
          raiz = null;
        }
        if (appEl) {
          appEl.hidden = false;
          appEl = null;
        }
        resolverConcluido?.();
        resolverConcluido = null;
      } catch (err) {
        setMsg(3, err instanceof ErroApi ? err.message : "Não foi possível concluir o onboarding.");
        botao.disabled = false;
      }
    });
  }
}

// ─── Montagem ─────────────────────────────────────────────────────────────────

function montarWizard(): HTMLElement {
  const el = document.createElement("div");
  el.className = "login"; // reutiliza o overlay de login para centralizar
  el.innerHTML = `
    <div class="lg-box" style="max-width:600px;width:100%">
      <div class="lg-topo">
        <img src="/logo-horizontal.png" alt="iSolutis" width="200" height="77">
        <span>Hub Comercial</span>
      </div>
      <div class="ob-corpo"></div>
    </div>`;
  document.body.appendChild(el);
  return el;
}

/**
 * Inicia o wizard de onboarding.
 * Esconde o app principal e resolve quando o onboarding for concluído.
 */
export function iniciarWizardOnboarding(): Promise<void> {
  // Resetar estado para o caso de o wizard ter sido iniciado antes
  estado.etapa = 1;
  estado.nomeEmpresa = "";
  estado.segmento = "";
  estado.produtos = [{ nome: "", preco: "" }];

  appEl = document.querySelector<HTMLElement>(".app");
  if (appEl) appEl.hidden = true;

  raiz = montarWizard();
  render();

  return new Promise((resolve) => {
    resolverConcluido = resolve;
  });
}
