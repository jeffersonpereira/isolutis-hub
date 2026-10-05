"""Regras de orçamento: totais, validade e status efetivo."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.constantes import StatusOrcamento
from app.domain.datas import adicionar_dias
from app.domain.dinheiro import ZERO, centavos


@dataclass(frozen=True)
class ItemCalculavel:
    qtd: Decimal
    preco_unitario: Decimal
    mensal: bool


@dataclass(frozen=True)
class TotaisOrcamento:
    projeto: Decimal  # soma dos itens únicos menos o desconto (nunca negativo)
    mensal: Decimal  # soma dos itens de cobrança mensal


def totais(itens: Iterable[ItemCalculavel], desconto: Decimal = ZERO) -> TotaisOrcamento:
    unico = ZERO
    mensal = ZERO
    for item in itens:
        valor = item.qtd * item.preco_unitario
        if item.mensal:
            mensal += valor
        else:
            unico += valor
    return TotaisOrcamento(projeto=max(ZERO, centavos(unico - desconto)), mensal=centavos(mensal))


def valido_ate(data: date, validade_dias: int) -> date:
    return adicionar_dias(data, validade_dias or 15)


def status_efetivo(status: StatusOrcamento, data: date, validade_dias: int, hoje: date) -> StatusOrcamento:
    """'vencido' não é gravado: é um orçamento enviado cuja validade já passou."""
    if status is StatusOrcamento.ENVIADO and valido_ate(data, validade_dias) < hoje:
        return StatusOrcamento.VENCIDO
    return status
