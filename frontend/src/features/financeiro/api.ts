import { http } from "@/api/http";
import type { components } from "@/api/schema";

type S = components["schemas"];

export type PlanoConta = S["PlanoContaLeitura"];
export type PlanoContaEntrada = S["PlanoContaEntrada"];
export type ContaBancaria = S["ContaBancariaLeitura"];
export type ContaBancariaEntrada = S["ContaBancariaEntrada"];
export type Parceiro = S["ParceiroLeitura"];
export type ParceiroEntrada = S["ParceiroEntrada"];
export type Papel = S["PapelLeitura"];
export type Titulo = S["TituloLeitura"];
export type PaginaTitulos = S["PaginaTitulos"];
export type TituloEntrada = S["TituloEntrada"];
export type Municipio = S["MunicipioLeitura"];
export type Instituicao = S["InstituicaoLeitura"];
export type FluxoDeCaixa = S["FluxoDeCaixa"];
export type Recorrencia = S["RecorrenciaLeitura"];
export type RecorrenciaEntrada = S["RecorrenciaEntrada"];
export type RecorrenciaAtualizar = S["RecorrenciaAtualizar"];

const B = "/financeiro";

export const apiFinanceiro = {
  municipios: (uf: string) => http.get<Municipio[]>(`${B}/municipios`, { uf, limite: 1000 }),
  instituicoes: () => http.get<Instituicao[]>(`${B}/instituicoes`),
  plano: {
    listar: () => http.get<PlanoConta[]>(`${B}/plano-contas`),
    proximoCodigo: (pai_id?: string | null) => http.get<{ codigo: string }>(`${B}/plano-contas/proximo-codigo`, { pai_id }),
    criar: (d: PlanoContaEntrada) => http.post<PlanoConta>(`${B}/plano-contas`, d),
    atualizar: (id: string, d: PlanoContaEntrada) => http.put<PlanoConta>(`${B}/plano-contas/${id}`, d),
    excluir: (id: string) => http.delete(`${B}/plano-contas/${id}`),
    /** Só com o plano vazio (409 se a empresa já tem contas). */
    importarPadrao: () => http.post<PlanoConta[]>(`${B}/plano-contas/importar-padrao`),
  },
  contas: {
    listar: () => http.get<ContaBancaria[]>(`${B}/contas-bancarias`),
    criar: (d: ContaBancariaEntrada) => http.post<ContaBancaria>(`${B}/contas-bancarias`, d),
    atualizar: (id: string, d: ContaBancariaEntrada) => http.put<ContaBancaria>(`${B}/contas-bancarias/${id}`, d),
    excluir: (id: string) => http.delete(`${B}/contas-bancarias/${id}`),
  },
  parceiros: {
    listar: (filtros: { papel?: string; busca?: string } = {}) => http.get<Parceiro[]>("/parceiros", filtros),
    papeis: () => http.get<Papel[]>("/parceiros/papeis"),
    criar: (d: ParceiroEntrada) => http.post<Parceiro>("/parceiros", d),
    atualizar: (id: string, d: S["ParceiroAtualizar"]) => http.put<Parceiro>(`/parceiros/${id}`, d),
    excluir: (id: string) => http.delete(`/parceiros/${id}`),
  },
  titulos: {
    listar: (consulta: Record<string, string | number | undefined> = {}) => http.get<PaginaTitulos>(`${B}/titulos`, consulta),
    exportar: (consulta: Record<string, string | undefined> = {}) => http.baixar(`${B}/titulos/exportar`, consulta),
    criar: (d: TituloEntrada) => http.post<Titulo>(`${B}/titulos`, d),
    atualizar: (id: string, d: TituloEntrada) => http.put<Titulo>(`${B}/titulos/${id}`, d),
    excluir: (id: string) => http.delete(`${B}/titulos/${id}`),
  },
  recorrencias: {
    listar: () => http.get<Recorrencia[]>(`${B}/recorrencias`),
    criar: (d: RecorrenciaEntrada) => http.post<Recorrencia>(`${B}/recorrencias`, d),
    atualizar: (id: string, d: RecorrenciaAtualizar) => http.put<Recorrencia>(`${B}/recorrencias/${id}`, d),
    pausar: (id: string) => http.post<Recorrencia>(`${B}/recorrencias/${id}/pausar`),
    retomar: (id: string) => http.post<Recorrencia>(`${B}/recorrencias/${id}/retomar`),
    encerrar: (id: string) => http.post<Recorrencia>(`${B}/recorrencias/${id}/encerrar`),
  },
  fluxoDeCaixa: (ano: number) => http.get<FluxoDeCaixa>(`${B}/fluxo-de-caixa`, { ano }),
};
