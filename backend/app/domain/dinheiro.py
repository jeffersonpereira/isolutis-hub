"""Dinheiro sempre em Decimal; arredondamento comercial (meio para cima) em centavos."""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")


def centavos(valor: Decimal | int | float | str) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def dividir_em_parcelas(total: Decimal, n: int) -> list[Decimal]:
    """Divide `total` em `n` parcelas de centavos; a última absorve a diferença de arredondamento."""
    if n < 1:
        raise ValueError("O número de parcelas deve ser pelo menos 1.")
    total = centavos(total)
    base = centavos(total / n)
    parcelas = [base] * (n - 1)
    parcelas.append(total - base * (n - 1))
    return parcelas
