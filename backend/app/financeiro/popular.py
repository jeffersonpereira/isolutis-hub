"""Carga das tabelas de referência: municípios (IBGE) e instituições financeiras (COMPE/FEBRABAN).

  python -m app.financeiro.popular                      # fontes oficiais (IBGE e BrasilAPI) — precisa de internet
  python -m app.financeiro.popular --fonte snapshot     # arquivos versionados em app/financeiro/dados (offline)
  python -m app.financeiro.popular --so bancos          # só uma das cargas

É idempotente (pode rodar de novo): municípios existentes (nome + UF) são mantidos; instituições são atualizadas pelo código.

ATENÇÃO sobre o snapshot de municípios: veio de um pacote npm e tem 5.560 dos 5.570 municípios do IBGE. Serve para
desenvolvimento e como plano B; em produção prefira a fonte oficial (`--fonte oficial`), que completa a lista.
"""

import argparse
import asyncio
import json
import urllib.request
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.financeiro.models import InstituicaoFinanceira
from app.models import Municipio

DADOS = Path(__file__).parent / "dados"
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
URL_BANCOS = "https://brasilapi.com.br/api/banks/v1"
UFS = set(
    [
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    ]
)


def _baixar(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=60) as resposta:  # noqa: S310 - URL fixa e https
        return json.load(resposta)


def municipios_oficiais() -> list[dict]:
    linhas = _baixar(URL_IBGE)
    return [{"nome": x["municipio-nome"].strip(), "uf": x["UF-sigla"]} for x in linhas if x["UF-sigla"] in UFS]


def instituicoes_oficiais() -> list[dict]:
    saida: dict[str, dict] = {}
    for b in _baixar(URL_BANCOS):
        if b.get("code") is None:
            continue
        codigo = str(b["code"]).zfill(3)
        saida[codigo] = {"codigo": codigo, "nome": (b.get("fullName") or b["name"]).strip()[:150]}
    return list(saida.values())


def municipios_snapshot() -> list[dict]:
    return json.loads((DADOS / "municipios_snapshot.json").read_text(encoding="utf-8"))["municipios"]


def instituicoes_snapshot() -> list[dict]:
    return json.loads((DADOS / "bancos_snapshot.json").read_text(encoding="utf-8"))["instituicoes"]


def _em_lotes(itens: list[dict], tamanho: int = 1000) -> Iterable[list[dict]]:
    for i in range(0, len(itens), tamanho):
        yield itens[i : i + tamanho]


async def gravar_municipios(sessao: AsyncSession, municipios: list[dict]) -> int:
    antes = await sessao.scalar(func.count(Municipio.id)) or 0
    for lote in _em_lotes(municipios):
        await sessao.execute(insert(Municipio).values(lote).on_conflict_do_nothing(constraint="uq_municipio_nome_uf"))
    return (await sessao.scalar(func.count(Municipio.id)) or 0) - antes


async def gravar_instituicoes(sessao: AsyncSession, instituicoes: list[dict]) -> int:
    antes = await sessao.scalar(func.count(InstituicaoFinanceira.id)) or 0
    for lote in _em_lotes(instituicoes):
        stmt = insert(InstituicaoFinanceira).values(lote)
        await sessao.execute(
            stmt.on_conflict_do_update(constraint="uq_instituicao_financeira_codigo", set_={"nome": stmt.excluded.nome})
        )
    return (await sessao.scalar(func.count(InstituicaoFinanceira.id)) or 0) - antes


async def executar(fonte: str, so: str | None) -> dict[str, int]:
    novos: dict[str, int] = {}
    async with SessionLocal() as sessao:
        if so in (None, "municipios"):
            lista = municipios_oficiais() if fonte == "oficial" else municipios_snapshot()
            novos["municipios"] = await gravar_municipios(sessao, lista)
        if so in (None, "bancos"):
            lista = instituicoes_oficiais() if fonte == "oficial" else instituicoes_snapshot()
            novos["instituicoes"] = await gravar_instituicoes(sessao, lista)
        await sessao.commit()
    return novos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fonte", choices=["oficial", "snapshot"], default="oficial")
    ap.add_argument("--so", choices=["municipios", "bancos"])
    args = ap.parse_args()
    try:
        novos = asyncio.run(executar(args.fonte, args.so))
    except OSError as e:
        raise SystemExit(
            f"Não foi possível baixar da fonte oficial ({e}). Libere o acesso à internet ou use --fonte snapshot."
        ) from e
    for nome, n in novos.items():
        print(f"{nome}: {n} novo(s) registro(s)")
    if args.fonte == "snapshot" and args.so != "bancos":
        print(
            "Aviso: o snapshot de municípios tem 5.560 dos 5.570 do IBGE; rode com --fonte oficial quando houver internet."
        )


if __name__ == "__main__":
    main()
