"""Aritmética de datas do domínio (sem acesso a banco)."""

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def adicionar_meses(d: date, n: int) -> date:
    """Soma `n` meses mantendo o dia, limitado ao último dia do mês de destino (31/01 + 1 = 28/02)."""
    indice = d.year * 12 + (d.month - 1) + n
    ano, mes = divmod(indice, 12)
    mes += 1
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def adicionar_dias(d: date, n: int) -> date:
    return d + timedelta(days=n)


def hoje() -> date:
    """Data de hoje no fuso do negócio (America/Sao_Paulo)."""
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
