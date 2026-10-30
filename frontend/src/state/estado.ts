import type { Cliente, ClienteReferencia, MembroEquipe, MeuEscopo, Negocio, Orcamento, Papel, Permissao, PessoaReferencia, Produto, Projeto, ProjetoReferencia, Tarefa } from "@/api/tipos";

/** Pessoa logada. */
/** `operador`: pessoa da AIME Tech com acesso à área da plataforma (fora de qualquer empresa). */
export const eu = { id: "", nome: "", email: "", operador: false };

/** Empresa ativa desta aba e o que o papel do usuário permite nela (vem do servidor; o front decide só por `permissoes`). */
export const acesso: { empresaId: string; empresaNome: string; papel: Papel | ""; permissoes: readonly Permissao[] } = {
  empresaId: "",
  empresaNome: "",
  papel: "",
  permissoes: [],
};
export const temPermissao = (p: Permissao): boolean => acesso.permissoes.includes(p);

/** Coleções mantidas em memória (pequenas: equipe de poucas pessoas). O faturamento é por ano e ficam nas próprias telas. */
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
  /** Quem a pessoa pode pôr como dono (ela; ela e liderados; ou todos, se admin). */
  atribuiveis: [] as PessoaReferencia[],
  /** Id e título dos projetos visíveis ou das tarefas que a pessoa executa. */
  referenciasProjetos: [] as ProjetoReferencia[],
  /** Escopo de acesso da pessoa na empresa ativa (admin, líder). */
  escopo: { ve_tudo: false, lider: false, liderados: 0, equipes: 0 } as MeuEscopo,
};

/** Admin ou líder: pode criar sem dono e atribuir a outra pessoa (o servidor confere a mesma regra). */
export const defineDono = (): boolean => dados.escopo.ve_tudo || dados.escopo.lider;

/** Filtros e escolhas de tela (não vão para o servidor). */
export const ui = {
  busca: "",
  cliOrigem: "",
  cliComNegocios: false,
  mostrarFechados: false,
  ano: new Date().getFullYear(),
  mes: null as number | null,
  orcStatus: "todos",
  projStatus: "ativos",
  tarefaPessoa: "todas",
  tarefaBusca: "",
  tarefaConcluidasTodas: false,
  buscaFin: "",
  buscaPlano: "",
};

/** Estado da conexão com os dados. */
export const conexao = { somenteLeitura: false, semDados: false };

export const porId = <T extends { id: string }>(lista: readonly T[], id?: string | null): T | undefined =>
  id ? lista.find((x) => x.id === id) : undefined;

export const nomeCliente = (id?: string | null): string => (porId(dados.referenciasClientes, id) ?? porId(dados.clientes, id))?.nome ?? "—";
export const nomeMembro = (id?: string | null): string => porId(dados.equipe, id)?.nome ?? "";
export const tituloProjeto = (id?: string | null): string =>
  (porId(dados.projetos, id) ?? porId(dados.referenciasProjetos, id))?.titulo ?? "";
/** Nome para frases ("você", "outra pessoa da equipe") na linha de autoria. */
export const nomeDe = (id?: string | null): string =>
  id === eu.id ? "você" : nomeMembro(id) || "outra pessoa da equipe";
export const podeEscrever = (): boolean => !conexao.somenteLeitura && !conexao.semDados;
