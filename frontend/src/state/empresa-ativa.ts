/**
 * Decide, depois do login, qual empresa a aba usa. Função pura (sem DOM nem armazenamento) para poder ser testada.
 *
 *   sem empresas                                  → "nenhuma": a conta não tem acesso (oferece sair)
 *   a empresa guardada na aba ainda é acessível   → "seguir": um F5 não pergunta de novo
 *   senão                                         → "escolher": tela de escolha, com a última usada pré-selecionada
 */
import type { EmpresaAcesso } from "@/api/tipos";

export type DecisaoDeEmpresa =
  | { tipo: "nenhuma" }
  | { tipo: "seguir"; empresa: EmpresaAcesso }
  | { tipo: "escolher"; sugerida: string | null };

export function decidirEmpresa(empresas: readonly EmpresaAcesso[], daAba: string | null, ultima: string | null): DecisaoDeEmpresa {
  if (empresas.length === 0) return { tipo: "nenhuma" };
  const guardada = empresas.find((e) => e.id === daAba);
  if (guardada) return { tipo: "seguir", empresa: guardada };
  return { tipo: "escolher", sugerida: empresas.some((e) => e.id === ultima) ? ultima : null };
}
