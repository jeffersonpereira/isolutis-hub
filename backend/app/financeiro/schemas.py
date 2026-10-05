"""Contratos Pydantic do módulo financeiro."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    model_validator,
)


NaturezaFinanceira = Literal[
    "RECEITAS",
    "CUSTOS",
    "DESPESAS",
    "INVESTIMENTOS",
    "MOVIMENTAÇÕES FINANCEIRAS",
    "EMPRÉSTIMOS E FINANCIAMENTOS",
]


def _texto_ou_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


Valor = Annotated[
    Decimal,
    Field(max_digits=13, decimal_places=2),
    PlainSerializer(float, return_type=float, when_used="json"),
]
Nome = Annotated[str, Field(min_length=1, max_length=150)]
TextoLongo = Annotated[
    Annotated[str, Field(max_length=20_000)] | None,
    BeforeValidator(_texto_ou_none),
]


class Entrada(BaseModel):
    """Payload de escrita: rejeita campos desconhecidos e apara espaços."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Leitura(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MunicipioLeitura(Leitura):
    id: UUID
    nome: str
    uf: str


class InstituicaoLeitura(Leitura):
    id: UUID
    codigo: str
    nome: str


class PlanoContaEntrada(Entrada):
    plano_pai_id: UUID | None = None
    codigo: Annotated[str, Field(min_length=1, max_length=20)]
    nome: Nome
    tipo_conta: Literal["A", "S"]
    natureza: NaturezaFinanceira | None = None

    @model_validator(mode="after")
    def _natureza_da_raiz(self) -> PlanoContaEntrada:
        if self.plano_pai_id is None and self.natureza is None:
            raise ValueError("Informe a natureza da conta de primeiro nível.")
        return self


class PlanoContaLeitura(Leitura):
    id: UUID
    plano_pai_id: UUID | None
    codigo: str
    nome: str
    tipo_conta: str
    natureza: str
    nivel: int
    possui_filhas: bool = False
    possui_titulos: bool = False


class ProximoCodigo(Leitura):
    codigo: str


class ContaBancariaEntrada(Entrada):
    instituicao_financeira_id: UUID
    nome: Nome
    saldo_inicial: Valor = Decimal("0.00")


class ContaBancariaLeitura(Leitura):
    id: UUID
    instituicao_financeira_id: UUID
    instituicao_codigo: str
    instituicao_nome: str
    nome: str
    saldo_inicial: Valor


class TituloEntrada(Entrada):
    tipo_conta: Literal["P", "R"]
    conta_bancaria_id: UUID
    plano_conta_id: UUID
    parceiro_id: UUID
    data_emissao: date | None = None
    data_vencimento: date
    valor_titulo: Valor = Field(gt=0)
    valor_desconto: Valor = Field(default=Decimal("0.00"), ge=0)
    valor_multa: Valor = Field(default=Decimal("0.00"), ge=0)
    valor_juros: Valor = Field(default=Decimal("0.00"), ge=0)
    status: Literal["A", "Q", "C"] = "A"
    data_pagamento: date | None = None
    valor_quitacao: Valor | None = Field(default=None, ge=0)
    anotacao: TextoLongo = None


class TituloLeitura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo_conta: str
    conta_bancaria_id: UUID
    conta_bancaria_nome: str
    plano_conta_id: UUID
    plano_conta_codigo: str
    plano_conta_nome: str
    parceiro_id: UUID
    parceiro_nome: str
    data_emissao: date | None
    data_vencimento: date
    valor_titulo: Valor
    valor_desconto: Valor
    valor_multa: Valor
    valor_juros: Valor
    valor_devido: Valor
    status: str
    data_pagamento: date | None
    valor_quitacao: Valor | None
    anotacao: str | None


class MesFluxo(Leitura):
    mes: int
    entradas_realizadas: Valor
    entradas_previstas: Valor
    saidas_realizadas: Valor
    saidas_previstas: Valor
    saldo_do_mes: Valor
    saldo_acumulado: Valor


class FluxoDeCaixa(Leitura):
    ano: int
    anos_disponiveis: list[int]
    saldo_inicial: Valor
    meses: list[MesFluxo]
    total_entradas: Valor
    total_saidas: Valor
