"""Substitui o plano de contas de UMA empresa pelo plano padrão (app/financeiro/dados/plano_contas_padrao.csv).

Apaga TODAS as contas de plano_contas da empresa e insere as do CSV, numa única transação.
Sem --confirmar só simula (mostra o que seria apagado e inserido) e não altera nada.

Exemplos:
  python -m app.scripts.carregar_plano_contas --empresa-nome "iSolutis"                 # simulação
  python -m app.scripts.carregar_plano_contas --empresa-nome "iSolutis" --confirmar     # aplica

Usa HUB_MIGRATION_DATABASE_URL (credencial de provisionamento), como criar_admin.

Segurança:
- os ids do CSV são fixos, então o plano só pode existir numa empresa por banco (a chave primária é global);
- se a empresa já tem títulos financeiros lançados em alguma conta, nada é apagado (o banco também recusa:
  contas com títulos são protegidas). Resolva os títulos antes (ou peça outra estratégia).
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import get_settings
from app.db import criar_engine

CSV_PADRAO = Path(__file__).resolve().parents[1] / "financeiro" / "dados" / "plano_contas_padrao.csv"


def ler_plano(caminho: Path = CSV_PADRAO) -> list[dict[str, str]]:
    """Contas do CSV ordenadas por nível (pai antes do filho), validando o arquivo antes de tocar no banco."""
    with caminho.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    ids = {linha["id"] for linha in linhas}
    if len(ids) != len(linhas):
        raise SystemExit("O CSV tem ids repetidos.")
    if len({linha["codigo"] for linha in linhas}) != len(linhas):
        raise SystemExit("O CSV tem códigos repetidos.")
    for linha in linhas:
        pai = linha["plano_pai_id"]
        if pai and pai not in ids:
            raise SystemExit(f"Conta {linha['codigo']}: o pai {pai} não está no CSV.")
        UUID(linha["id"])
    return sorted(linhas, key=lambda linha: linha["codigo"].count("."))


async def carregar(empresa_id: UUID | None, empresa_nome: str | None, confirmar: bool) -> None:
    plano = ler_plano()
    url = get_settings().migration_database_url
    if not url:
        raise SystemExit("Defina HUB_MIGRATION_DATABASE_URL; este script não usa a credencial runtime.")
    engine = criar_engine(url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as sessao:
            if empresa_id:
                linha = (
                    await sessao.execute(text("select id, nome from empresa where id = :i"), {"i": empresa_id})
                ).first()
            else:
                linhas = (
                    await sessao.execute(text("select id, nome from empresa where nome = :n"), {"n": empresa_nome})
                ).all()
                if len(linhas) > 1:
                    raise SystemExit("Há mais de uma empresa com esse nome; use --empresa-id.")
                linha = linhas[0] if linhas else None
            if linha is None:
                raise SystemExit("Empresa não encontrada.")
            empresa, nome = linha

            atuais = await sessao.scalar(
                text("select count(*) from plano_contas where empresa_id = :e"), {"e": empresa}
            )
            titulos = await sessao.scalar(
                text("select count(*) from titulo_financeiro where empresa_id = :e"), {"e": empresa}
            )
            em_outra = await sessao.scalar(
                text("select count(*) from plano_contas where id = any(:ids) and empresa_id <> :e"),
                {"ids": [UUID(c["id"]) for c in plano], "e": empresa},
            )
            print(f"Empresa: {nome} ({empresa})")
            print(
                f"Contas atuais a apagar: {atuais} · títulos financeiros lançados: {titulos} · contas a inserir: {len(plano)}"
            )
            if em_outra:
                raise SystemExit(
                    f"{em_outra} id(s) do CSV já pertencem a outra empresa: o plano padrão só cabe numa empresa por banco."
                )
            if titulos:
                raise SystemExit("Há títulos lançados: nada foi alterado. Resolva os títulos antes de trocar o plano.")
            if not confirmar:
                print("Simulação: nada foi alterado. Rode de novo com --confirmar para aplicar.")
                return

            # filhas antes das mães (a chave estrangeira do pai é RESTRICT)
            for nivel in (3, 2, 1):
                await sessao.execute(
                    text("delete from plano_contas where empresa_id = :e and nivel = :n"), {"e": empresa, "n": nivel}
                )
            for conta in plano:  # pais antes dos filhos; nível, natureza e regras vêm do trigger do banco
                await sessao.execute(
                    text(
                        "insert into plano_contas (id, empresa_id, plano_pai_id, codigo, nome, tipo_conta, natureza) "
                        "values (:id, :e, :pai, :codigo, :nome, :tipo, :natureza)"
                    ),
                    {
                        "id": UUID(conta["id"]), "e": empresa, "pai": UUID(conta["plano_pai_id"]) if conta["plano_pai_id"] else None,
                        "codigo": conta["codigo"], "nome": conta["nome"], "tipo": conta["tipo_conta"], "natureza": conta["natureza"],
                    },
                )  # fmt: skip
            await sessao.commit()
            print(f"Plano de contas substituído: {atuais} apagadas, {len(plano)} inseridas.")
    finally:
        await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    destino = ap.add_mutually_exclusive_group(required=True)
    destino.add_argument("--empresa-id", type=UUID)
    destino.add_argument("--empresa-nome")
    ap.add_argument("--confirmar", action="store_true", help="aplica de fato (sem isto, só simula)")
    args = ap.parse_args()
    if sys.platform == "win32":  # o psycopg assíncrono não roda no loop Proactor padrão do Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(carregar(args.empresa_id, args.empresa_nome, args.confirmar))


if __name__ == "__main__":
    main()
