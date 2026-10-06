"""Onda 2: onboarding, TOTP/2FA e rastreamento de notificações.

Revision ID: 0007
Revises: 0006
"""

from migrations.sql_runner import executar_sql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    executar_sql("0007_onda2.sql")


def downgrade() -> None:
    executar_sql("0007_onda2_down.sql")
