"""Aceite de convite sob RLS: função SECURITY DEFINER que vincula o membro a partir de um convite válido.

Revision ID: 0009
Revises: 0008
"""

from migrations.sql_runner import executar_sql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0009_aceite_convite_rls.sql")


def downgrade() -> None:
    executar_sql("0009_aceite_convite_rls_down.sql")
