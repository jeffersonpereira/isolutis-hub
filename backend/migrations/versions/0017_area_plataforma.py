"""Área da plataforma: operador, status da empresa, auditoria e funções de provisionamento.

Revision ID: 0017
Revises: 0016
"""

from migrations.sql_runner import executar_sql

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0017_area_plataforma.sql")


def downgrade() -> None:
    executar_sql("0017_area_plataforma_down.sql")
