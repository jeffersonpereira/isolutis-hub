/** Helper para simplificar validação e submissão de formulários. */

import { fv, campoDe } from "./campos";
import type { ErroValidacao, Schema } from "./validators";
import { toast } from "./toast";

export interface OpcoesCampo<T> {
  schema?: Schema<T>;
  aoSubmeter: (dados: T) => Promise<void>;
  fechar?: () => void;
  formulario: HTMLFormElement;
  botaoSubmissao: HTMLElement;
}

/** Cria um handler de formulário com validação integrada. */
export function criarFormulario<T extends Record<string, unknown>>({
  schema,
  aoSubmeter,
  fechar,
  formulario,
  botaoSubmissao,
}: OpcoesCampo<T>) {
  const botao = botaoSubmissao as HTMLButtonElement;

  return async function submeter() {
    if (!schema) {
      // Sem schema: apenas chama o handler
      botao.disabled = true;
      try {
        await aoSubmeter({} as T);
      } catch (e) {
        console.error(e);
      } finally {
        botao.disabled = false;
      }
      return;
    }

    const dados = Object.fromEntries(
      Array.from(formulario.elements).reduce(
        (acc, el) => {
          if ((el as any).name) {
            acc.push([(el as any).name, fv(formulario, (el as any).name)]);
          }
          return acc;
        },
        [] as [string, string][],
      ),
    );

    const resultado = schema.parse(dados);
    if (!resultado.sucesso) {
      mostrarErros(formulario, resultado.erros);
      return;
    }

    botao.disabled = true;
    try {
      await aoSubmeter(resultado.dados as T);
      if (fechar) fechar();
    } catch (e) {
      console.error(e);
    } finally {
      botao.disabled = false;
    }
  };
}

/** Mostra erros de validação ao lado dos campos. */
function mostrarErros(formulario: HTMLFormElement, erros: ErroValidacao) {
  // Limpar erros anteriores
  formulario.querySelectorAll(".erro-campo").forEach((el) => el.remove());

  // Mostrar novos erros
  for (const [campo, mensagem] of Object.entries(erros)) {
    if (campo === "_global") {
      toast(mensagem);
      continue;
    }

    const el = formulario.elements.namedItem(campo);
    if (!el) continue;

    const erro = document.createElement("span");
    erro.className = "erro-campo sub";
    erro.style.color = "var(--bad)";
    erro.textContent = mensagem;
    el.parentElement?.appendChild(erro);
  }

  toast("Verifique os erros no formulário.");
}
