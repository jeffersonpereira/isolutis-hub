"""Schema inicial (modelagem do DBA: docs/banco-de-dados.md)

Revision ID: 0001
Revises:
"""

from migrations.sql_runner import executar_sql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0001_schema_inicial.sql")


def downgrade() -> None:
    executar_sql("0001_schema_inicial_down.sql")
