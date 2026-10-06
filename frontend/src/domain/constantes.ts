/** Vocabulário e rótulos da interface (os valores são os mesmos aceitos pela API). */
export const ETAPAS = [
  { id: "lead", nome: "Lead" },
  { id: "diag_agendado", nome: "Diagnóstico agendado" },
  { id: "diag_feito", nome: "Diagnóstico feito" },
  { id: "proposta", nome: "Proposta enviada" },
  { id: "negociacao", nome: "Negociação" },
  { id: "ganho", nome: "Ganho" },
  { id: "perdido", nome: "Perdido" },
] as const;
export type EtapaId = (typeof ETAPAS)[number]["id"];
export const ABERTAS: readonly string[] = ETAPAS.slice(0, 5).map((e) => e.id);
export const etapaNome = (id: string): string => ETAPAS.find((e) => e.id === id)?.nome ?? id;

export const TIPOS: Record<string, string> = {
  projeto: "Projeto sob medida",
  mensal: "Manutenção mensal",
  consultoria: "Consultoria",
  outro: "Outro",
};
export const UNIDADES: Record<string, string> = { projeto: "projeto", mensal: "mês", consultoria: "hora", outro: "unidade" };

export const ORC_STATUS: Record<string, readonly [string, string]> = {
  rascunho: ["Rascunho", ""],
  enviado: ["Enviado", "info"],
  aprovado: ["Aprovado", "ok"],
  recusado: ["Recusado", "bad"],
  vencido: ["Vencido", "warn"],
};
export const ORIGENS = ["Site", "Indicação", "LinkedIn", "Instagram", "WhatsApp", "Evento", "Prospecção ativa", "Outro"] as const;
export const MOTIVOS_PERDA = ["Preço", "Prazo", "Escolheu concorrente", "Adiou o projeto", "Sem resposta", "Fora do perfil"] as const;

export const PROJ_STATUS: Record<string, readonly [string, string]> = {
  planejamento: ["Planejamento", "info"],
  construcao: ["Em construção", "warn"],
  validacao: ["Em validação", "teal-mid"],
  entregue: ["Entregue", "ok"],
  pausado: ["Pausado", ""],
};
export const ETAPA_STATUS: Record<string, readonly [string, string]> = {
  a_fazer: ["A fazer", ""],
  andamento: ["Em andamento", "warn"],
  concluida: ["Concluída", "ok"],
};

export const FORMAS_INVEST = ["Dinheiro (aporte)", "Equipamento", "Pagamento de despesa da empresa", "Outro"] as const;

export const COLUNAS_TAREFA = [
  { id: "a_fazer", nome: "A fazer" },
  { id: "fazendo", nome: "Fazendo" },
  { id: "revisao", nome: "Em revisão" },
  { id: "concluido", nome: "Concluído" },
] as const;
export const PRIORIDADES: Record<string, readonly [string, string]> = {
  alta: ["Alta", "bad"],
  media: ["Média", "warn"],
  baixa: ["Baixa", ""],
};
export const OPCOES_REPETICAO = [1, 2, 3, 6, 12, 18, 24, 36] as const;

export const AREA_NOME: Record<string, string> = {
  painel: "Painel", clientes: "Clientes", negocios: "Negócios", orcamentos: "Orçamentos", faturamento: "Faturamento",
  despesas: "Despesas", produtos: "Produtos", projetos: "Projetos", tarefas: "Tarefas", equipe: "Equipe",
};
