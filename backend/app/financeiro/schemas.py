"""Contrato da API do módulo financeiro (snake_case; dinheiro como número JSON)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from app.financeiro.regras import MAXIMO_DE_OCORRENCIAS
from app.schemas.comum import Entrada, Leitura, TextoLongo

# Valores monetários do plano: numeric(13,2)
Valor = Annotated[
    Decimal,
    Field(max_digits=13, decimal_places=2),
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]
Nome = Annotated[str, Field(min_length=1, max_length=150)]


# ----------------------------------------------------------------------------- referências
class MunicipioLeitura(Leitura):
    id: UUID
    nome: str
    uf: str


class InstituicaoLeitura(Leitura):
    id: UUID
    codigo: str
    nome: str


# ----------------------------------------------------------------------------- plano de contas
class PlanoContaEntrada(Entrada):
    plano_pai_id: UUID | None = None
    codigo: Annotated[str, Field(min_length=1, max_length=20)]
    nome: Nome
    tipo_conta: Literal["A", "S"]
    # Obrigatória nas contas de nível 1; nas demais é herdada da conta pai (o valor enviado é ignorado).
    natureza: Literal["R", "D"] | None = None
    # Conta em que entram os aportes de sócios (só analítica e de receita).
    aporte_socio: bool = False

    @model_validator(mode="after")
    def _natureza_da_raiz(self) -> "PlanoContaEntrada":
        if self.plano_pai_id is None and self.natureza is None:
            raise ValueError("Informe a natureza (receita ou despesa) da conta de primeiro nível.")
        return self


class PlanoContaLeitura(Leitura):
    id: UUID
    plano_pai_id: UUID | None
    codigo: str
    nome: str
    tipo_conta: str
    natureza: str
    nivel: int
    aporte_socio: bool = False
    possui_filhas: bool = False
    possui_titulos: bool = False


class ProximoCodigo(Leitura):
    codigo: str


# ----------------------------------------------------------------------------- contas bancárias
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


# ----------------------------------------------------------------------------- títulos
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
    # Em título quitado, se vier vazio assume o valor devido.
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
    valor_quitacao: Valor
    anotacao: str | None
    recorrencia_id: UUID | None = None


class TotaisTitulos(Leitura):
    """Valores devidos em aberto do filtro completo (não só da página)."""

    a_receber: Valor
    a_pagar: Valor


class PaginaTitulos(Leitura):
    itens: list[TituloLeitura]
    total: int
    totais: TotaisTitulos


# ----------------------------------------------------------------------------- recorrência de títulos
Frequencia = Literal["semanal", "quinzenal", "mensal", "bimestral", "trimestral", "semestral", "anual"]
Termino = Literal["data", "quantidade", "sem_fim"]


class _TerminoDaRecorrencia(Entrada):
    """Exatamente uma forma de término: data final, quantidade de ocorrências ou sem fim."""

    termino: Termino
    data_fim: date | None = None
    quantidade: Annotated[int, Field(ge=1, le=MAXIMO_DE_OCORRENCIAS)] | None = None

    @model_validator(mode="after")
    def _termino_coerente(self) -> "_TerminoDaRecorrencia":
        if self.termino == "data" and (self.data_fim is None or self.quantidade is not None):
            raise ValueError("Informe só a data final do término.")
        if self.termino == "quantidade" and (self.quantidade is None or self.data_fim is not None):
            raise ValueError("Informe só a quantidade de ocorrências do término.")
        if self.termino == "sem_fim" and (self.data_fim is not None or self.quantidade is not None):
            raise ValueError("Recorrência sem fim não tem data final nem quantidade.")
        return self


class RecorrenciaAtualizar(_TerminoDaRecorrencia):
    """O que se pode mudar numa recorrência; frequência e início são fixos (encerre e crie outra para mudá-los)."""

    conta_bancaria_id: UUID
    plano_conta_id: UUID
    parceiro_id: UUID
    valor_titulo: Valor = Field(gt=0)
    anotacao: TextoLongo = None


class RecorrenciaEntrada(RecorrenciaAtualizar):
    tipo_conta: Literal["P", "R"]
    frequencia: Frequencia
    data_inicio: date

    @model_validator(mode="after")
    def _fim_depois_do_inicio(self) -> "RecorrenciaEntrada":
        if self.termino == "data" and self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError("A data final não pode ser antes do início.")
        return self


class RecorrenciaLeitura(BaseModel):
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
    valor_titulo: Valor
    anotacao: str | None
    frequencia: str
    data_inicio: date
    termino: str
    data_fim: date | None
    quantidade: int | None
    ativa: bool
    encerrada_em: datetime | None
    titulos_gerados: int
    titulos_abertos: int
    proximo_vencimento: date | None


# ----------------------------------------------------------------------------- fluxo de caixa
class MesFluxo(Leitura):
    mes: int
    entradas_realizadas: Valor
    entradas_previstas: Valor
    aportes_realizados: Valor = Decimal("0.00")
    aportes_previstos: Valor = Decimal("0.00")
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
    total_aportes: Valor = Decimal("0.00")
    total_saidas: Valor
