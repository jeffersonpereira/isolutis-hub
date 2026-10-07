"""plano_contas.natureza somente R/D e regra RN04 do título.

Revision ID: 0011
Revises: 0010
"""

from migrations.sql_runner import executar_sql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0011_natureza_receita_despesa.sql")


def downgrade() -> None:
    executar_sql("0011_natureza_receita_despesa_down.sql")
