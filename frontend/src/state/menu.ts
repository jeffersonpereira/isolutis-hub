/**
 * Catálogo de navegação: como as telas se organizam no menu lateral, o ícone de cada uma e as ações rápidas
 * que ela oferece ao "+ Novo" e à paleta de comandos. As telas continuam se registrando sozinhas
 * (`registrarVista`); aqui só se descreve onde cada uma aparece. Tela visível que não conste daqui entra
 * no fim do menu, em "Outros", para nunca ficar inalcançável.
 */
export interface AcaoRapida {
  /** Nome da ação registrada com `registrarAcao`. */
  id: string;
  rotulo: string;
  icone?: string;
}

export type ItemMenu = { id: string } | { grupo: string; icone: string; filhos: string[] };

export interface SecaoMenu {
  /** Sem rótulo, os itens aparecem no topo, antes das seções. */
  rotulo?: string;
  itens: ItemMenu[];
}

export const ESTRUTURA_MENU: SecaoMenu[] = [
  { itens: [{ id: "painel" }, { id: "clientes" }] },
  { rotulo: "Comercial", itens: [{ id: "negocios" }, { id: "orcamentos" }, { id: "produtos" }] },
  { rotulo: "Operação", itens: [{ id: "projetos" }, { id: "tarefas" }] },
  {
    rotulo: "Financeiro",
    itens: [
      { grupo: "Financeiro", icone: "financeiro", filhos: ["fin-titulos", "fin-fluxo", "fin-plano", "fin-contas", "fin-parceiros"] },
      { id: "faturamento" },
      { id: "despesas" },
      { id: "relatorios" },
    ],
  },
  { rotulo: "Administração", itens: [{ id: "equipe" }, { id: "empresa" }] },
];

export const ICONES_DAS_TELAS: Record<string, string> = {
  painel: "painel",
  clientes: "clientes",
  negocios: "negocios",
  orcamentos: "orcamentos",
  produtos: "produtos",
  projetos: "projetos",
  tarefas: "tarefas",
  "fin-titulos": "titulos",
  "fin-fluxo": "fluxo",
  "fin-plano": "plano",
  "fin-contas": "contas",
  "fin-parceiros": "fornecedores",
  faturamento: "faturamento",
  despesas: "despesas",
  relatorios: "relatorios",
  equipe: "equipe",
  empresa: "empresa",
  conta: "conta",
};

export const ACOES_DAS_TELAS: Record<string, AcaoRapida[]> = {
  clientes: [{ id: "novoCliente", rotulo: "Novo cliente", icone: "clientes" }],
  negocios: [{ id: "novoNegocio", rotulo: "Novo negócio", icone: "negocios" }],
  orcamentos: [{ id: "novoOrcamento", rotulo: "Novo orçamento", icone: "orcamentos" }],
  produtos: [{ id: "novoProduto", rotulo: "Novo produto", icone: "produtos" }],
  projetos: [{ id: "novoProjeto", rotulo: "Novo projeto", icone: "projetos" }],
  tarefas: [{ id: "novaTarefa", rotulo: "Nova tarefa", icone: "tarefas" }],
  faturamento: [{ id: "novoLanc", rotulo: "Novo lançamento", icone: "faturamento" }],
  despesas: [
    { id: "novaDespesa", rotulo: "Nova despesa", icone: "despesas" },
    { id: "novoInvest", rotulo: "Novo investimento", icone: "despesas" },
  ],
  "fin-titulos": [{ id: "novoTitulo", rotulo: "Novo título", icone: "titulos" }],
  "fin-contas": [{ id: "novaContaBancaria", rotulo: "Nova conta bancária", icone: "contas" }],
  "fin-parceiros": [{ id: "novoParceiro", rotulo: "Novo fornecedor", icone: "fornecedores" }],
  equipe: [{ id: "novoUsuario", rotulo: "Novo usuário", icone: "equipe" }],
};
