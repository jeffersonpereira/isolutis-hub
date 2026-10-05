/** Helper genérico para CRUD: reduz duplicação entre features. */

import type { Safe } from "@/core/html";
import { recarregar } from "@/state/nucleo";
import { registrarAcao } from "./acoes";
import { registrarAbertura } from "./eventos";
import { abrirGaveta } from "./gaveta";
import { tentar } from "./erros";
import { toast } from "./toast";

export interface OpcoesCrudHelper<T> {
  /** ID do recurso (ex: "clientes", "negocios") */
  recurso: string;

  /** Renderizar lista de items */
  renderizarLista(items: T[]): Safe;

  /** Renderizar formulário de criação/edição */
  renderizarFormulario(item?: T): {
    titulo: string;
    corpo: Safe;
    rodape: Safe;
    aoMontar?: (form: HTMLFormElement, fechar: () => void, container: HTMLElement) => void;
  };

  /** Salvar item (criar ou atualizar) */
  aoSalvar: (item: T, isNovo: boolean) => Promise<T>;

  /** Excluir item */
  aoExcluir?: (item: T) => Promise<void>;

  /** Ação desencadeada após sucesso */
  aoSucesso?: (item: T, isNovo: boolean) => void;
}

/** Cria um feature CRUD com handlers padrão. */
export function setupCrud<T extends { id: string }>(opcoes: OpcoesCrudHelper<T>) {
  const { recurso, renderizarFormulario, aoSalvar, aoSucesso } = opcoes;

  // Registrar ação "novo"
  registrarAcao(`novo${primeiraLetraMaiuscula(recurso)}`, async () => {
    abrirGaveta({
      titulo: renderizarFormulario().titulo,
      corpo: renderizarFormulario().corpo,
      rodape: renderizarFormulario().rodape,
      montar: async (f, fechar, L) => {
        renderizarFormulario().aoMontar?.(f, fechar, L);

        // Handler de salvar
        const botaoSalvar = L.querySelector("[data-salvar]") as HTMLButtonElement | null;
        botaoSalvar?.addEventListener("click", async () => {
          botaoSalvar.disabled = true;
          try {
            const resultado = await tentar(() => aoSalvar({} as T, true));
            if (resultado) {
              await recarregar(recurso);
              toast("Criado com sucesso");
              aoSucesso?.(resultado, true);
              fechar();
            }
          } finally {
            botaoSalvar.disabled = false;
          }
        });
      },
    });
  });

  // Registrar ação "abrir" (editar)
  registrarAbertura(recurso, (id) => {
    // Buscar item da lista global (depende de como estado é gerenciado)
    // Para versão genérica, pode precisar de callback
    console.warn(`abrir ${recurso}:${id} - precisa implementar busca do item no estado`);
  });
}

function primeiraLetraMaiuscula(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Helper simplificado para padrão de salvar + recarregar + fechar.
 * Use quando o formulário não precisa de lógica customizada complexa.
 */
export async function salvarComRecarregar<T>({
  operacao,
  recursoParaRecarregar,
  mensagem = "Salvo com sucesso",
  fechar,
}: {
  operacao: () => Promise<T>;
  recursoParaRecarregar: string | string[];
  mensagem?: string;
  fechar: () => void;
}): Promise<T | null> {
  try {
    const resultado = await tentar(operacao);
    if (resultado) {
      const recursos = typeof recursoParaRecarregar === "string" ? [recursoParaRecarregar] : recursoParaRecarregar;
      await recarregar(...recursos);
      toast(mensagem);
      fechar();
    }
    return resultado;
  } catch (e) {
    console.error(e);
    return null;
  }
}
