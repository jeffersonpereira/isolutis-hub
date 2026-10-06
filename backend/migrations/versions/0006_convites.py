"""Tabela de convites por e-mail para ingressar na equipe de uma empresa.

Revision ID: 0006
Revises: 0005
"""

from migrations.sql_runner import executar_sql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0006_convites.sql")


def downgrade() -> None:
    executar_sql("0006_convites_down.sql")
