"""Parceiro de negócio como cadastro único com papéis; funde e remove `clientes`

Revision ID: 0003
Revises: 0002
"""

from migrations.sql_runner import executar_sql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0003_parceiro_hub.sql")


def downgrade() -> None:
    executar_sql("0003_parceiro_hub_down.sql")
