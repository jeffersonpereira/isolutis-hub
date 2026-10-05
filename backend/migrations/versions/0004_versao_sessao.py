"""Invalida tokens quando a senha muda.

Revision ID: 0004
Revises: 0003
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE usuarios ADD COLUMN versao_sessao integer NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_versao_sessao CHECK (versao_sessao >= 0)")


def downgrade() -> None:
    op.execute("ALTER TABLE usuarios DROP CONSTRAINT ck_usuarios_versao_sessao")
    op.execute("ALTER TABLE usuarios DROP COLUMN versao_sessao")
