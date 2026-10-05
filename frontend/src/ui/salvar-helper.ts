/**
 * Helper genérico para salvar com validação, loading visual e recarregar.
 * Elimina duplicação do padrão: validar → mostrar loading → chamar API → recarregar → fechar
 */

import { recarregar } from "@/state/nucleo";
import { toast } from "./toast";

export interface OpcoesSalvar {
  /** Form HTMLFormElement */
  form: HTMLFormElement;
  /** Container para mostrar loading (botão ou outro elemento) */
  botaoSalvar: HTMLButtonElement;
  /** Validar antes de salvar. Retorna objeto com erros ou null se válido. */
  validar: () => Record<string, string> | null;
  /** Operação que efetivamente salva (API call). */
  operacao: () => Promise<any>;
  /** Qual recurso recarregar após salvar (ex: "equipe"). */
  recarregarRecurso: string;
  /** Fechar gaveta após sucesso. */
  fechar: () => void;
  /** Callback opcional após sucesso. */
  onSucesso?: (resultado: any) => void;
  /** Mensagem de sucesso personalizada. */
  mensagemSucesso?: string;
}

/**
 * Executa ciclo completo de validação → loading visual → API → recarregar → fechar.
 * Mostra erros em toast e desabilita botão durante operação.
 */
export async function salvarComValidacao(opcoes: OpcoesSalvar): Promise<void> {
  const {
    botaoSalvar,
    validar,
    operacao,
    recarregarRecurso,
    fechar,
    onSucesso,
    mensagemSucesso,
  } = opcoes;

  // 1. Validar
  const erros = validar();
  if (erros) {
    Object.values(erros).forEach((msg) => toast(msg));
    return;
  }

  // 2. Mostrar loading
  botaoSalvar.disabled = true;
  botaoSalvar.classList.add("loading");
  const textoOriginal = botaoSalvar.textContent;
  botaoSalvar.innerHTML = '<span class="spinner"></span> Salvando…';

  try {
    // 3. Chamar API
    const resultado = await operacao();

    // 4. Recarregar dados
    await recarregar(recarregarRecurso);

    // 5. Callback opcional
    if (onSucesso) onSucesso(resultado);

    // 6. Feedback
    toast(mensagemSucesso || "Salvo");
    fechar();
  } catch (erro) {
    // Erro já foi tratado em tentar(), apenas resetar UI
    botaoSalvar.disabled = false;
    botaoSalvar.classList.remove("loading");
    botaoSalvar.innerHTML = textoOriginal || "Salvar";
  }
}

/**
 * Cria função validadora para um formulário com base em regras.
 * Retorna: objeto com erros por campo, ou null se tudo está válido.
 */
export function criarValidador(
  form: HTMLFormElement,
  regras: Record<string, { validar: () => string | null }[]>,
): () => Record<string, string> | null {
  return () => {
    const erros: Record<string, string> = {};

    for (const [campo, validadores] of Object.entries(regras)) {
      const input = form.elements.namedItem(campo) as HTMLInputElement | null;
      if (!input) continue;

      for (const { validar } of validadores) {
        const erro = validar();
        if (erro) {
          erros[campo] = erro;
          break; // Mostrar apenas o primeiro erro do campo
        }
      }
    }

    return Object.keys(erros).length > 0 ? erros : null;
  };
}
