"""Adicionar membro já cadastrado direto, sem convite por e-mail.

Revision ID: 0018
Revises: 0017
"""

from migrations.sql_runner import executar_sql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0018_membro_direto_plataforma.sql")


def downgrade() -> None:
    executar_sql("0018_membro_direto_plataforma_down.sql")
