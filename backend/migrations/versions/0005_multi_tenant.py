"""Empresa como tenant e propriedade de todos os dados operacionais.

Revision ID: 0005
Revises: 0004
"""

from migrations.sql_runner import executar_sql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0005_multi_tenant.sql")


def downgrade() -> None:
    raise RuntimeError("Migração multi-tenant requer restore/roll-forward; downgrade pode misturar ou perder dados de tenants.")
