import type { Cliente, ClienteReferencia, MembroEquipe, Negocio, Orcamento, Papel, Permissao, Produto, Projeto, Tarefa } from "@/api/tipos";

/** Pessoa logada. */
export const eu = { id: "", nome: "", email: "" };

/** Empresa ativa desta aba e o que o papel do usuário permite nela (vem do servidor; o front decide só por `permissoes`). */
export const acesso: { empresaId: string; empresaNome: string; papel: Papel | ""; permissoes: readonly Permissao[] } = {
  empresaId: "",
  empresaNome: "",
  papel: "",
  permissoes: [],
};
export const temPermissao = (p: Permissao): boolean => acesso.permissoes.includes(p);

/** Coleções mantidas em memória (pequenas: equipe de poucas pessoas). Faturamento/despesas são por ano e ficam nas próprias telas. */
export const dados = {
  clientes: [] as Cliente[],
  /** Só id e nome: carregada para todos os papéis, serve para exibir o nome do cliente. */
  referenciasClientes: [] as ClienteReferencia[],
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

export const nomeCliente = (id?: string | null): string => (porId(dados.referenciasClientes, id) ?? porId(dados.clientes, id))?.nome ?? "—";
export const nomeMembro = (id?: string | null): string => porId(dados.equipe, id)?.nome ?? "";
/** Nome para frases ("você", "outra pessoa da equipe") na linha de autoria. */
export const nomeDe = (id?: string | null): string =>
  id === eu.id ? "você" : nomeMembro(id) || "outra pessoa da equipe";
export const podeEscrever = (): boolean => !conexao.somenteLeitura && !conexao.semDados;
