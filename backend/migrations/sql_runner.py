"""Executa scripts .sql inteiros (várias instruções) pela conexão do Alembic."""

from pathlib import Path

from alembic import op

PASTA_SQL = Path(__file__).parent / "sql"


def executar_sql(nome_arquivo: str) -> None:
    sql = (PASTA_SQL / nome_arquivo).read_text(encoding="utf-8")
    # Protocolo simples do psycopg (sem parâmetros) aceita várias instruções em uma chamada.
    conexao = op.get_bind().connection.driver_connection
    conexao.execute(sql)  # type: ignore[union-attr]
