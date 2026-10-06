import { http } from "./http";
import type * as T from "./tipos";
import type { components } from "./schema";

type S = components["schemas"];
const ano = (a: number) => ({ ano: a });

export const api = {
  empresas: { listar: () => http.get<Array<{ id: string; nome: string; papel: "admin" | "membro" }>>("/empresas") },
  auth: {
    login: (email: string, senha: string) => http.post<T.LoginResposta>("/auth/login", { email, senha }),
    eu: () => http.get<T.Usuario>("/auth/eu"),
    trocarSenha: (senha_atual: string, nova_senha: string) => http.post<void>("/auth/trocar-senha", { senha_atual, nova_senha }),
    totp: {
      setup: () => http.post<T.SetupTotpResposta>("/auth/2fa/setup"),
      confirmar: (d: T.ConfirmarTotpEntrada) => http.post<void>("/auth/2fa/confirmar", d),
      verificar: (d: T.VerificarTotpEntrada) => http.post<T.TokenSaida>("/auth/2fa/verificar", d),
      desativar: (codigo: string) => http.delete(`/auth/2fa?codigo=${encodeURIComponent(codigo)}`),
    },
  },
  onboarding: {
    status: () => http.get<T.OnboardingStatus>("/onboarding/status"),
    salvarEmpresa: (nome: string, segmento: string) => http.patch<void>("/onboarding/empresa", { nome, segmento }),
    salvarProdutos: (produtos: T.ProdutoOnboarding[]) => http.post<void>("/onboarding/produtos", { produtos }),
    concluir: () => http.post<void>("/onboarding/concluir"),
  },
  relatorios: {
    dre: (a: number) => http.get<T.DreItem[]>("/relatorios/dre", ano(a)),
    fluxoCaixa: (a: number) => http.get<T.FluxoItem[]>("/relatorios/fluxo-caixa", ano(a)),
    exportarPdf: (tipo: "dre" | "fluxo-caixa", a: number) => http.baixar(`/relatorios/${tipo}`, { ano: a, formato: "pdf" }),
    exportarXlsx: (tipo: "dre" | "fluxo-caixa", a: number) => http.baixar(`/relatorios/${tipo}`, { ano: a, formato: "xlsx" }),
  },
  equipe: { listar: () => http.get<T.MembroEquipe[]>("/equipe") },
  usuarios: {
    listar: () => http.get<T.Usuario[]>("/usuarios"),
    criar: (d: S["UsuarioCriar"]) => http.post<T.Usuario>("/usuarios", d),
    atualizar: (id: string, d: S["UsuarioAtualizar"]) => http.put<T.Usuario>(`/usuarios/${id}`, d),
    remover: (id: string) => http.delete(`/usuarios/${id}`),
  },
  convites: {
    listar: () => http.get<T.Convite[]>("/convites"),
    criar: (d: T.ConviteEntrada) => http.post<T.Convite>("/convite", d),
    cancelar: (id: number) => http.delete(`/convite/${id}`),
    verificar: (token: string) => http.get<T.ConviteInfo>(`/auth/convite/${token}`),
    aceitar: (token: string, d: T.AceitarConviteEntrada) => http.post<T.TokenSaida>(`/auth/convite/${token}/aceitar`, d),
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
  despesas: {
    listar: (a: number) => http.get<T.Despesa[]>("/despesas", ano(a)),
    opcoes: () => http.get<T.OpcoesDespesa>("/despesas/opcoes"),
    resumo: (a: number) => http.get<T.ResumoDespesas>("/despesas/resumo", ano(a)),
    criar: (d: T.DespesaEntrada) => http.post<T.Despesa[]>("/despesas", d),
    atualizar: (id: string, d: S["DespesaAtualizar"]) => http.put<T.Despesa>(`/despesas/${id}`, d),
    pagar: (id: string) => http.post<T.Despesa>(`/despesas/${id}/pagar`),
    excluir: (id: string) => http.delete(`/despesas/${id}`),
  },
  investimentos: {
    listar: (a: number) => http.get<T.Investimento[]>("/investimentos", ano(a)),
    criar: (d: T.InvestimentoEntrada) => http.post<T.Investimento>("/investimentos", d),
    atualizar: (id: string, d: T.InvestimentoEntrada & { versao: number }) => http.put<T.Investimento>(`/investimentos/${id}`, d),
    excluir: (id: string) => http.delete(`/investimentos/${id}`),
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
