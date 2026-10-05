import { ErroApi } from "@/api/http";
import { toast } from "./toast";

/** Mostra o erro de uma operação de forma amigável (a API já devolve a mensagem em português). */
export function tratarErro(e: unknown): void {
  console.error(e);
  if (e instanceof ErroApi) {
    if (e.codigo === "validacao" && Array.isArray(e.detalhes)) {
      const d = e.detalhes[0] as { mensagem?: string } | undefined;
      toast(d?.mensagem ? limparMensagem(d.mensagem) : e.message);
    } else {
      toast(e.message);
    }
    return;
  }
  toast("Não foi possível concluir agora. Verifique a conexão e tente de novo.");
}

/** Mensagens de validação do Pydantic vêm como "Value error, ..."; tira o prefixo técnico. */
const limparMensagem = (m: string): string => m.replace(/^Value error, /, "");

/**
 * Executa uma operação de gravação: devolve o resultado, ou `null` depois de mostrar o erro.
 * Os fluxos "salvar e fechar" seguem o padrão: `if ((await tentar(() => api...)) !== null) fechar()`.
 */
export async function tentar<T>(operacao: () => Promise<T>): Promise<T | null> {
  try {
    return await operacao();
  } catch (e) {
    tratarErro(e);
    return null;
  }
}
