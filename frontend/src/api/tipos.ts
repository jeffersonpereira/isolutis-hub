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

/** Convites por e-mail para ingressar na equipe. */
export interface Convite {
  id: number;
  email: string;
  papel: string;
  criado_em: string;
  expira_em: string;
  usado_em: string | null;
}

export interface ConviteEntrada {
  nome: string;
  email: string;
  papel: "admin" | "membro";
}

export interface AceitarConviteEntrada {
  senha: string;
  confirmar_senha: string;
}

export interface ConviteInfo {
  email: string;
  papel: string;
  empresa_nome: string;
  criado_por_nome: string;
  estado: "valido" | "expirado" | "usado";
}

export interface TokenSaida {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

/** Recursos que a interface mantém em memória e recarrega quando o servidor avisa de mudanças. */
export type Recurso = "clientes" | "produtos" | "negocios" | "orcamentos" | "projetos" | "tarefas" | "equipe" | "faturamento" | "despesas";

// ─── Onboarding ─────────────────────────────────────────────────────────────

export interface OnboardingStatus {
  concluido: boolean;
}

export interface ProdutoOnboarding {
  nome: string;
  preco: number | null;
}

// ─── Relatórios ─────────────────────────────────────────────────────────────

export interface DreItem {
  mes: number;
  nome_mes: string;
  receitas: number;
  custos: number;
  resultado: number;
}

export interface FluxoItem {
  mes: number;
  nome_mes: string;
  entradas: number;
  saidas: number;
  saldo: number;
  saldo_acumulado: number;
}

// ─── 2FA / TOTP ──────────────────────────────────────────────────────────────

export interface LoginResposta {
  access_token: string;
  token_type: string;
  usuario: Usuario;
  /** Presente quando o usuário tem 2FA ativo; ausente quando não tem. */
  requer_2fa?: true;
  /** Token temporário de curta duração para concluir o 2FA. */
  token_temporario?: string;
}

export interface SetupTotpResposta {
  qr_code: string;
  provisioning_uri: string;
  backup_codes: string[];
}

export interface ConfirmarTotpEntrada {
  codigo: string;
  backup_codes: string[];
}

export interface VerificarTotpEntrada {
  token_temporario: string;
  codigo: string;
}
