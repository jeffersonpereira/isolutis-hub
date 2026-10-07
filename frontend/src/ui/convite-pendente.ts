/**
 * Convite à espera do login. Quem já tem conta não define senha ao aceitar: a tela do convite guarda o
 * token aqui, o login normal (com 2FA, se ativo) acontece, e `principal()` conclui o aceite em seguida.
 * Fica em `sessionStorage` (some ao fechar a aba) e é apagado em qualquer desfecho.
 */
import { api } from "@/api/endpoints";
import { ErroApi } from "@/api/http";
import { toast } from "@/ui/toast";

const CHAVE = "hub.convite.pendente";

export const convitePendente = {
  definir(token: string): void {
    try {
      sessionStorage.setItem(CHAVE, token);
    } catch {
      /* armazenamento indisponível (modo privado): quem chama confere com `obter` */
    }
  },
  obter(): string | null {
    try {
      return sessionStorage.getItem(CHAVE);
    } catch {
      return null;
    }
  },
  limpar(): void {
    try {
      sessionStorage.removeItem(CHAVE);
    } catch {
      /* ver acima */
    }
  },
};

interface Dependencias {
  aceitar: (token: string) => Promise<unknown>;
  avisar: (mensagem: string) => void;
}

/** Conclui o convite pendente, se houver, com a sessão já autenticada. Nunca lança: o resultado vira aviso. */
export async function concluirConvitePendente(
  deps: Dependencias = { aceitar: (token) => api.convites.aceitar(token), avisar: toast },
): Promise<void> {
  const token = convitePendente.obter();
  if (!token) return;
  convitePendente.limpar(); // antes de chamar: qualquer desfecho consome a pendência e evita repetição
  try {
    await deps.aceitar(token);
    deps.avisar("Convite aceito. Você agora tem acesso a mais uma empresa.");
  } catch (erro) {
    deps.avisar(erro instanceof ErroApi ? erro.message : "Não foi possível aceitar o convite agora. Abra o link de novo.");
  }
}
