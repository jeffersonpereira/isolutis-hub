import { html, type Safe } from "@/core/html";
import { abrirGaveta } from "@/ui/gaveta";
import { tentar } from "@/ui/erros";
import { recarregar } from "@/state/nucleo";
import { toast } from "@/ui/toast";

export const GRUPO = "Financeiro";

/** 11.222.333/0001-81 · 529.982.247-25 (documentos guardados só com dígitos). */
export function formatarDocumento(doc: string | null | undefined): string {
  if (!doc) return "—";
  if (doc.length === 14) return doc.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
  if (doc.length === 11) return doc.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  return doc;
}

/** RN04: título a pagar (`P`) usa conta analítica de despesa (`D`); a receber (`R`), de receita (`R`). */
export function contasDoPlanoParaTitulo<T extends { tipo_conta: string; natureza: string }>(plano: readonly T[], tipoTitulo: string): T[] {
  const natureza = tipoTitulo === "P" ? "D" : "R";
  return plano.filter((c) => c.tipo_conta === "A" && c.natureza === natureza);
}

export const formatarCep = (cep?: string | null): string => (cep && cep.length === 8 ? cep.replace(/(\d{5})(\d{3})/, "$1-$2") : (cep ?? ""));

/** Botões de editar/excluir na linha de uma tabela (`acao` é o prefixo das ações registradas). */
export const acoesDaLinha = (acao: string, id: string): Safe =>
  html`<div class="fin-acoes"><button class="btn" data-act="${acao}Editar" data-id="${id}">Editar</button><button class="btn danger" data-act="${acao}Excluir" data-id="${id}">Excluir</button></div>`;

/**
 * Confirmação de exclusão na própria gaveta (o mesmo padrão visual dos formulários).
 * Executa `operacao` ao confirmar, recarrega o módulo e avisa; erros da API aparecem como aviso.
 */
export function confirmarExclusao(o: { titulo: string; mensagem: string; sucesso: string; operacao: () => Promise<void> }): void {
  abrirGaveta({
    titulo: o.titulo,
    corpo: html`<p style="margin:0">${o.mensagem}</p>`,
    rodape: html`<button class="btn danger" data-confirmar>Excluir</button><button class="btn" data-fechar>Cancelar</button>`,
    montar: (_f, fechar, L) => {
      const botao = L.querySelector<HTMLButtonElement>("[data-confirmar]");
      // o primeiro clique "arma" os botões danger (padrão da gaveta); aqui o gesto já é a confirmação
      botao?.classList.add("armed");
      if (botao) botao.textContent = "Confirmar exclusão";
      botao?.addEventListener("click", async () => {
        botao.disabled = true;
        const ok = await tentar(async () => (await o.operacao(), true));
        if (ok === null) {
          botao.disabled = false;
          return;
        }
        await recarregar("financeiro");
        toast(o.sucesso);
        fechar();
      });
    },
  });
}
