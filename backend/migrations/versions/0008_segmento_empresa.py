"""Onda 3: campo segmento na empresa para categorização do negócio.

Revision ID: 0008
Revises: 0007
"""

from migrations.sql_runner import executar_sql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0008_segmento_empresa.sql")


def downgrade() -> None:
    executar_sql("0008_segmento_empresa_down.sql")
