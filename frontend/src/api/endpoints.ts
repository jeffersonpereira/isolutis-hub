import { http } from "./http";
import type * as T from "./tipos";
import type { components } from "./schema";

type S = components["schemas"];
const ano = (a: number) => ({ ano: a });

export const api = {
  empresas: {
    listar: () => http.get<Array<{ id: string; nome: string; papel: "admin" | "membro" }>>("/empresas"),
    atualizar: (id: string, d: { nome: string }) => http.put<{ id: string; nome: string }>(`/empresas/${id}`, d),
  },
  auth: {
    login: (email: string, senha: string) => http.post<S["TokenSaida"]>("/auth/login", { email, senha }),
    eu: () => http.get<T.Usuario>("/auth/eu"),
    trocarSenha: (senha_atual: string, nova_senha: string) => http.post<void>("/auth/trocar-senha", { senha_atual, nova_senha }),
  },
  equipe: { listar: () => http.get<T.MembroEquipe[]>("/equipe") },
  usuarios: {
    listar: () => http.get<T.Usuario[]>("/usuarios"),
    criar: (d: S["UsuarioCriar"]) => http.post<T.Usuario>("/usuarios", d),
    atualizar: (id: string, d: S["UsuarioAtualizar"]) => http.put<T.Usuario>(`/usuarios/${id}`, d),
    remover: (id: string) => http.delete(`/usuarios/${id}`),
  },
  clientes: {
    listar: () => http.get<T.Cliente[]>("/clientes"),
    criar: (d: T.ClienteEntrada) => http.post<S["ClienteLeitura"]>("/clientes", d),
    atualizar: (id: string, d: T.ClienteEntrada & { versao: number }) => http.put<S["ClienteLeitura"]>(`/clientes/${id}`, d),
    excluir: (id: string) => http.delete(`/clientes/${id}`),
    relacionados: (id: string) => http.get<T.ClienteRelacionados>(`/clientes/${id}/relacionados`),
  },
  produtos: {
    listar: () => http.get<T.Produto[]>("/produtos"),
    criar: (d: T.ProdutoEntrada) => http.post<T.Produto>("/produtos", d),
    catalogo: () => http.post<T.Produto[]>("/produtos/catalogo"),
    atualizar: (id: string, d: T.ProdutoEntrada & { versao: number }) => http.put<T.Produto>(`/produtos/${id}`, d),
    excluir: (id: string) => http.delete(`/produtos/${id}`),
  },
  negocios: {
    listar: () => http.get<T.Negocio[]>("/negocios"),
    criar: (d: T.NegocioEntrada) => http.post<T.Negocio>("/negocios", d),
    atualizar: (id: string, d: T.NegocioEntrada & { versao: number }) => http.put<T.Negocio>(`/negocios/${id}`, d),
    mover: (id: string, d: S["MoverEtapa"]) => http.patch<T.Negocio>(`/negocios/${id}/etapa`, d),
    excluir: (id: string) => http.delete(`/negocios/${id}`),
  },
  orcamentos: {
    listar: () => http.get<T.Orcamento[]>("/orcamentos"),
    criar: (d: T.OrcamentoEntrada) => http.post<T.Orcamento>("/orcamentos", d),
    atualizar: (id: string, d: T.OrcamentoEntrada & { versao: number }) => http.put<T.Orcamento>(`/orcamentos/${id}`, d),
    aprovar: (id: string) => http.post<S["AprovacaoSaida"]>(`/orcamentos/${id}/aprovar`),
    excluir: (id: string) => http.delete(`/orcamentos/${id}`),
    baixar: (id: string) => http.baixar(`/orcamentos/${id}/documento`),
  },
  faturamento: {
    listar: (a: number, mes?: number) => http.get<T.Lancamento[]>("/faturamento", { ano: a, mes }),
    resumo: (a: number) => http.get<T.ResumoFaturamento>("/faturamento/resumo", ano(a)),
    criar: (d: T.LancamentoEntrada) => http.post<T.Lancamento[]>("/faturamento", d),
    lote: (d: T.FaturamentoEmLote) => http.post<T.Lancamento[]>("/faturamento/lote", d),
    atualizar: (id: string, d: S["LancamentoAtualizar"]) => http.put<T.Lancamento>(`/faturamento/${id}`, d),
    receber: (id: string) => http.post<T.Lancamento>(`/faturamento/${id}/receber`),
    excluir: (id: string) => http.delete(`/faturamento/${id}`),
    exportar: (a: number) => http.baixar("/faturamento/exportar", ano(a)),
  },
  projetos: {
    listar: () => http.get<T.Projeto[]>("/projetos"),
    modelo: (negocio_id: string) => http.get<T.ModeloProjeto>("/projetos/modelo", { negocio_id }),
    etapasPadrao: (inicio?: string, entrega?: string) => http.get<T.EtapaSugerida[]>("/projetos/etapas-padrao", { inicio, entrega }),
    criar: (d: T.ProjetoEntrada) => http.post<T.Projeto>("/projetos", d),
    atualizar: (id: string, d: T.ProjetoEntrada & { versao: number }) => http.put<T.Projeto>(`/projetos/${id}`, d),
    excluir: (id: string) => http.delete(`/projetos/${id}`),
    relatorio: (id: string) => http.baixar(`/projetos/${id}/relatorio`),
  },
  tarefas: {
    listar: () => http.get<T.Tarefa[]>("/tarefas"),
    criar: (d: T.TarefaEntrada) => http.post<T.Tarefa>("/tarefas", d),
    atualizar: (id: string, d: T.TarefaEntrada & { versao: number }) => http.put<T.Tarefa>(`/tarefas/${id}`, d),
    mover: (id: string, d: S["MoverTarefa"]) => http.patch<T.Tarefa>(`/tarefas/${id}/coluna`, d),
    excluir: (id: string) => http.delete(`/tarefas/${id}`),
  },
  painel: { obter: () => http.get<T.Painel>("/painel") },
};
