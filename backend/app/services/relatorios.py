"""Serviços para relatórios financeiros: DRE e Fluxo de Caixa."""

from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financeiro import Despesa, LancamentoReceita

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

ZERO = Decimal("0")


async def calcular_dre(
    db: AsyncSession,
    empresa_id: object,  # uuid.UUID — aceito como opaque para não duplicar tipagem
    ano: int,
) -> list[dict]:
    """DRE (Demonstrativo de Resultado) mensal para o ano informado.

    Retorna lista com 12 entradas, uma por mês:
      {mes, nome_mes, receitas, custos, resultado}
    Meses sem movimentação aparecem com valores zero.
    """
    # Receitas recebidas no ano (filtra pela empresa via RLS + campo vencimento)
    linhas_receitas = await db.execute(
        select(
            extract("month", LancamentoReceita.vencimento).label("mes"),
            func.coalesce(func.sum(LancamentoReceita.valor), ZERO).label("total"),
        )
        .where(
            LancamentoReceita.status == "recebido",
            extract("year", LancamentoReceita.vencimento) == ano,
        )
        .group_by(extract("month", LancamentoReceita.vencimento))
    )
    receitas_por_mes: dict[int, Decimal] = {
        int(mes): total for mes, total in linhas_receitas.all()
    }

    # Custos pagos no ano (Despesa.data é a data de referência da despesa)
    linhas_despesas = await db.execute(
        select(
            extract("month", Despesa.data).label("mes"),
            func.coalesce(func.sum(Despesa.valor), ZERO).label("total"),
        )
        .where(
            Despesa.status == "pago",
            extract("year", Despesa.data) == ano,
        )
        .group_by(extract("month", Despesa.data))
    )
    custos_por_mes: dict[int, Decimal] = {
        int(mes): total for mes, total in linhas_despesas.all()
    }

    resultado = []
    for i, nome in enumerate(MESES, start=1):
        receitas = receitas_por_mes.get(i, ZERO)
        custos = custos_por_mes.get(i, ZERO)
        resultado.append(
            {
                "mes": i,
                "nome_mes": nome,
                "receitas": float(receitas),
                "custos": float(custos),
                "resultado": float(receitas - custos),
            }
        )

    return resultado


async def calcular_fluxo_caixa(
    db: AsyncSession,
    empresa_id: object,  # uuid.UUID
    ano: int,
) -> list[dict]:
    """Fluxo de Caixa mensal para o ano informado.

    Retorna lista com 12 entradas:
      {mes, nome_mes, entradas, saidas, saldo_mes, saldo_acumulado}
    O saldo acumulado é calculado em Python acumulando mês a mês.
    """
    linhas_entradas = await db.execute(
        select(
            extract("month", LancamentoReceita.vencimento).label("mes"),
            func.coalesce(func.sum(LancamentoReceita.valor), ZERO).label("total"),
        )
        .where(
            LancamentoReceita.status == "recebido",
            extract("year", LancamentoReceita.vencimento) == ano,
        )
        .group_by(extract("month", LancamentoReceita.vencimento))
    )
    entradas_por_mes: dict[int, Decimal] = {
        int(mes): total for mes, total in linhas_entradas.all()
    }

    linhas_saidas = await db.execute(
        select(
            extract("month", Despesa.data).label("mes"),
            func.coalesce(func.sum(Despesa.valor), ZERO).label("total"),
        )
        .where(
            Despesa.status == "pago",
            extract("year", Despesa.data) == ano,
        )
        .group_by(extract("month", Despesa.data))
    )
    saidas_por_mes: dict[int, Decimal] = {
        int(mes): total for mes, total in linhas_saidas.all()
    }

    resultado = []
    saldo_acumulado = Decimal("0")
    for i, nome in enumerate(MESES, start=1):
        entradas = entradas_por_mes.get(i, ZERO)
        saidas = saidas_por_mes.get(i, ZERO)
        saldo_mes = entradas - saidas
        saldo_acumulado += saldo_mes
        resultado.append(
            {
                "mes": i,
                "nome_mes": nome,
                "entradas": float(entradas),
                "saidas": float(saidas),
                "saldo_mes": float(saldo_mes),
                "saldo_acumulado": float(saldo_acumulado),
            }
        )

    return resultado
