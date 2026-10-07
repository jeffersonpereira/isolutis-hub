/** Papéis por empresa: rótulos e descrições para telas (a regra de acesso vive no servidor). */
import type { Papel } from "@/api/tipos";

export const ROTULO_PAPEL: Record<Papel, string> = {
  admin: "Administrador",
  financeiro: "Financeiro",
  comercial: "Comercial",
  membro: "Membro",
};

export const DESCRICAO_PAPEL: Record<Papel, string> = {
  admin: "Acesso total, inclusive equipe e dados da empresa",
  financeiro: "Financeiro, faturamento, despesas e relatórios",
  comercial: "Clientes, negócios, orçamentos e produtos",
  membro: "Painel, projetos e tarefas",
};

/** Opções para selects de papel, na ordem em que fazem sentido para quem concede o acesso. */
export const OPCOES_PAPEL: ReadonlyArray<readonly [Papel, string]> = (["membro", "comercial", "financeiro", "admin"] as const).map(
  (p) => [p, `${ROTULO_PAPEL[p]} — ${DESCRICAO_PAPEL[p]}`] as const,
);

export const rotuloDoPapel = (papel?: string | null): string => (papel && papel in ROTULO_PAPEL ? ROTULO_PAPEL[papel as Papel] : "—");
