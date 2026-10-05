/** Tipos do contrato da API, derivados do OpenAPI do backend (npm run gen:api). */
import type { components } from "./schema";

type S = components["schemas"];

export type Usuario = S["UsuarioLeitura"];
export type MembroEquipe = S["MembroEquipe"];
export type Cliente = S["ClienteResumo"];
export type ClienteEntrada = S["ClienteEntrada"];
export type ClienteRelacionados = S["ClienteRelacionados"];
export type Produto = S["ProdutoLeitura"];
export type ProdutoEntrada = S["ProdutoEntrada"];
export type Negocio = S["NegocioLeitura"];
export type NegocioEntrada = S["NegocioEntrada"];
export type Orcamento = S["OrcamentoLeitura"];
export type OrcamentoEntrada = S["OrcamentoEntrada"];
export type ItemEntrada = S["ItemEntrada"];
export type Lancamento = S["LancamentoLeitura"];
export type LancamentoEntrada = S["LancamentoEntrada"];
export type FaturamentoEmLote = S["FaturamentoEmLote"];
export type ResumoFaturamento = S["ResumoFaturamento"];
export type Despesa = S["DespesaLeitura"];
export type DespesaEntrada = S["DespesaEntrada"];
export type Investimento = S["InvestimentoLeitura"];
export type InvestimentoEntrada = S["InvestimentoEntrada"];
export type OpcoesDespesa = S["OpcoesDespesa"];
export type ResumoDespesas = S["ResumoDespesas"];
export type Projeto = S["ProjetoLeitura"];
export type ProjetoEntrada = S["ProjetoEntrada"];
export type EtapaEntrada = S["EtapaEntrada"];
export type EtapaSugerida = S["EtapaSugerida"];
export type ModeloProjeto = S["ModeloProjeto"];
export type Tarefa = S["TarefaLeitura"];
export type TarefaEntrada = S["TarefaEntrada"];
export type Painel = S["Painel"];

/** Recursos que a interface mantém em memória e recarrega quando o servidor avisa de mudanças. */
export type Recurso = "clientes" | "produtos" | "negocios" | "orcamentos" | "projetos" | "tarefas" | "equipe" | "faturamento" | "despesas";
