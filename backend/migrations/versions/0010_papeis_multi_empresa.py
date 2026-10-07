"""Quatro papéis por empresa, remoção de usuarios.admin e criação de empresa só pelo operador.

Revision ID: 0010
Revises: 0009
"""

from migrations.sql_runner import executar_sql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0010_papeis_multi_empresa.sql")


def downgrade() -> None:
    executar_sql("0010_papeis_multi_empresa_down.sql")
