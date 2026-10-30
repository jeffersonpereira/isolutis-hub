"""Plano de contas padrão (dados/plano_contas_padrao.csv), lido como estrutura: código, nome, tipo, natureza e pai.

Os `id` do CSV servem só para ligar filha ao pai; quem importa gera ids novos por empresa (a chave primária de
`plano_contas` é global, então ids fixos só caberiam em uma empresa por banco).
"""

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CSV_PADRAO = Path(__file__).parent / "dados" / "plano_contas_padrao.csv"
# Conta analítica de receita em que entram os aportes de sócios ("Aportes de Capital").
CODIGO_APORTE_SOCIO = "7.02.001"


@dataclass(frozen=True)
class ContaPadrao:
    chave: str  # id do CSV
    pai: str | None  # id do pai no CSV
    codigo: str
    nome: str
    tipo_conta: str
    natureza: str

    @property
    def nivel(self) -> int:
        return self.codigo.count(".") + 1


@lru_cache
def ler_plano_padrao(caminho: Path = CSV_PADRAO) -> tuple[ContaPadrao, ...]:
    """Contas ordenadas por nível (pai antes da filha), validadas: sem ids ou códigos repetidos e com pais existentes."""
    with caminho.open(encoding="utf-8", newline="") as f:
        contas = [
            ContaPadrao(
                linha["id"], linha["plano_pai_id"] or None, linha["codigo"], linha["nome"], linha["tipo_conta"], linha["natureza"]
            )
            for linha in csv.DictReader(f)
        ]
    chaves = {c.chave for c in contas}
    if len(chaves) != len(contas):
        raise ValueError("O plano de contas padrão tem ids repetidos.")
    if len({c.codigo for c in contas}) != len(contas):
        raise ValueError("O plano de contas padrão tem códigos repetidos.")
    for c in contas:
        if c.pai is not None and c.pai not in chaves:
            raise ValueError(f"Conta {c.codigo}: o pai {c.pai} não está no plano padrão.")
    return tuple(sorted(contas, key=lambda c: c.nivel))
