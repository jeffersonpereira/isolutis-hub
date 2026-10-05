"""Regras puras do módulo financeiro (sem banco, sem HTTP)."""

import re
from decimal import Decimal

from app.domain.dinheiro import centavos

NIVEL_MAXIMO = 3
# Largura do último segmento do código em cada nível: 1 · 1.01 · 1.01.001
LARGURA_SEGMENTO = {2: 2, 3: 3}


# ----------------------------------------------------------------------------- documentos
def so_digitos(valor: str | None) -> str:
    return re.sub(r"\D", "", valor or "")


def _digito(base: str, pesos: list[int]) -> int:
    resto = sum(int(d) * p for d, p in zip(base, pesos, strict=True)) % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    d1 = _digito(cpf[:9], list(range(10, 1, -1)))
    d2 = _digito(cpf[:9] + str(d1), list(range(11, 1, -1)))
    return cpf[9:] == f"{d1}{d2}"


def cnpj_valido(cnpj: str) -> bool:
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    d1 = _digito(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _digito(cnpj[:12] + str(d1), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[12:] == f"{d1}{d2}"


def documento_valido(tipo_pessoa: str, documento: str) -> bool:
    return cpf_valido(documento) if tipo_pessoa == "PF" else cnpj_valido(documento)


# ----------------------------------------------------------------------------- plano de contas
def nivel_do_codigo(codigo: str) -> int:
    return codigo.count(".") + 1


def mensagem_codigo_invalido(nivel: int, pai_codigo: str | None) -> str:
    if nivel == 1:
        return "O código de uma conta de primeiro nível deve ser um número (ex.: 1)."
    largura = LARGURA_SEGMENTO[nivel]
    exemplo = f"{pai_codigo}.{'1'.zfill(largura)}"
    return f"O código deve ser o do pai seguido de ponto e {largura} dígitos (ex.: {exemplo})."


def codigo_valido(codigo: str, pai_codigo: str | None) -> bool:
    """RN01: 1 · 1.01 · 1.01.001 — o filho carrega o código do pai e um segmento de largura fixa."""
    if pai_codigo is None:
        return re.fullmatch(r"\d+", codigo) is not None
    nivel = nivel_do_codigo(pai_codigo) + 1
    if nivel > NIVEL_MAXIMO:
        return False
    segmento = LARGURA_SEGMENTO[nivel]
    return re.fullmatch(rf"{re.escape(pai_codigo)}\.\d{{{segmento}}}", codigo) is not None


def chave_de_ordenacao(codigo: str) -> tuple[int, ...]:
    """Ordena 1, 1.01, 1.01.001, 1.02, 2 ... numericamente (e não como texto)."""
    return tuple(int(p) for p in codigo.split("."))


def proximo_codigo(codigos_irmaos: list[str], pai_codigo: str | None) -> str:
    """Sugere o próximo código livre entre os filhos de `pai_codigo` (ou entre as raízes)."""
    ultimos = [int(c.split(".")[-1]) for c in codigos_irmaos]
    n = max(ultimos, default=0) + 1
    if pai_codigo is None:
        return str(n)
    largura = LARGURA_SEGMENTO[nivel_do_codigo(pai_codigo) + 1]
    return f"{pai_codigo}.{str(n).zfill(largura)}"


# ----------------------------------------------------------------------------- títulos
def natureza_do_titulo(tipo_titulo: str) -> str:
    """RN04: conta a pagar usa conta de despesa; a receber usa conta de receita."""
    return "D" if tipo_titulo == "P" else "R"


def valor_devido(valor: Decimal, desconto: Decimal, multa: Decimal, juros: Decimal) -> Decimal:
    return centavos(valor - desconto + multa + juros)
