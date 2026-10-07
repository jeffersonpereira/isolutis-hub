import type { Cliente, MembroEquipe, Negocio, Orcamento, Produto, Projeto, Tarefa } from "@/api/tipos";

/** Pessoa logada. */
export const eu = { id: "", nome: "", email: "", admin: false };

/** Coleções mantidas em memória (pequenas: equipe de poucas pessoas). Faturamento/despesas são por ano e ficam nas próprias telas. */
export const dados = {
  clientes: [] as Cliente[],
  negocios: [] as Negocio[],
  orcamentos: [] as Orcamento[],
  produtos: [] as Produto[],
  projetos: [] as Projeto[],
  tarefas: [] as Tarefa[],
  equipe: [] as MembroEquipe[],
};

/** Filtros e escolhas de tela (não vão para o servidor). */
export const ui = {
  busca: "",
  cliOrigem: "",
  cliComNegocios: false,
  mostrarFechados: false,
  ano: new Date().getFullYear(),
  mes: null as number | null,
  orcStatus: "todos",
  despTipo: "todos",
  projStatus: "ativos",
  tarefaPessoa: "todas",
  tarefaBusca: "",
  tarefaConcluidasTodas: false,
  buscaFin: "",
  buscaPlano: "",
  finTipo: "todos",
  finStatus: "todos",
};

/** Estado da conexão com os dados. */
export const conexao = { somenteLeitura: false, semDados: false };

export const porId = <T extends { id: string }>(lista: readonly T[], id?: string | null): T | undefined =>
  id ? lista.find((x) => x.id === id) : undefined;

export const nomeCliente = (id?: string | null): string => porId(dados.clientes, id)?.nome ?? "—";
export const nomeMembro = (id?: string | null): string => porId(dados.equipe, id)?.nome ?? "";
/** Nome para frases ("você", "outra pessoa da equipe") na linha de autoria. */
export const nomeDe = (id?: string | null): string =>
  id === eu.id ? "você" : nomeMembro(id) || "outra pessoa da equipe";
export const podeEscrever = (): boolean => !conexao.somenteLeitura && !conexao.semDados;
