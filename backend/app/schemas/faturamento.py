from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.comum import Auditoria, Dinheiro, DinheiroPositivo, Entrada, Leitura, Texto, TextoOpcional

TipoReceita = Literal["projeto", "mensal", "consultoria", "outro"]
StatusReceita = Literal["previsto", "recebido"]


class LancamentoEntrada(Entrada):
    cliente_id: UUID
    tipo: TipoReceita
    descricao: Texto
    valor: DinheiroPositivo
    vencimento: date
    status: StatusReceita = "previsto"
    nf: TextoOpcional = None
    negocio_id: UUID | None = None
    orcamento_id: UUID | None = None
    # Só na criação: repete o lançamento todo mês (série "1/N").
    repetir: int = Field(default=1, ge=1, le=36)


class LancamentoAtualizar(Entrada):
    cliente_id: UUID
    tipo: TipoReceita
    descricao: Texto
    valor: DinheiroPositivo
    vencimento: date
    status: StatusReceita
    nf: TextoOpcional = None
    versao: int = Field(ge=1)


class LancamentoLeitura(Auditoria):
    cliente_id: UUID
    cliente_nome: str
    tipo: str
    descricao: str
    valor: Dinheiro
    vencimento: date
    status: str
    recebido_em: date | None
    nf: str | None
    negocio_id: UUID | None
    orcamento_id: UUID | None
    grupo_id: UUID | None
    parcela: int | None
    total_parcelas: int | None


class PlanoProjeto(Entrada):
    valor: DinheiroPositivo
    parcelas: int = Field(default=1, ge=1, le=24)
    primeiro_vencimento: date


class PlanoMensal(Entrada):
    valor: DinheiroPositivo
    meses: int = Field(default=12, ge=1, le=36)
    primeira_mensalidade: date


class FaturamentoEmLote(Entrada):
    """Geração atômica dos lançamentos de uma venda fechada (projeto parcelado e/ou mensalidades)."""

    cliente_id: UUID
    titulo: TextoOpcional = None
    negocio_id: UUID | None = None
    orcamento_id: UUID | None = None
    projeto: PlanoProjeto | None = None
    mensal: PlanoMensal | None = None

    @model_validator(mode="after")
    def _algo_para_lancar(self) -> "FaturamentoEmLote":
        if not ((self.projeto and self.projeto.valor) or (self.mensal and self.mensal.valor)):
            raise ValueError("Nada marcado para lançar.")
        return self


class MesFaturamento(Leitura):
    mes: int
    recebido: Dinheiro
    previsto: Dinheiro
    recorrente: Dinheiro
    quantidade: int


class ResumoFaturamento(Leitura):
    ano: int
    anos_disponiveis: list[int]
    meses: list[MesFaturamento]
    total_recebido: Dinheiro
    total_previsto: Dinheiro
    total_recorrente: Dinheiro
