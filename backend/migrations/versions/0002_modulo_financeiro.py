"""Módulo financeiro: plano de contas, contas bancárias, parceiros e títulos

Revision ID: 0002
Revises: 0001
"""

from migrations.sql_runner import executar_sql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0002_modulo_financeiro.sql")


def downgrade() -> None:
    executar_sql("0002_modulo_financeiro_down.sql")
