import uuid
from datetime import datetime

from sqlalchemy import Computed, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ComAuditoria, ComEmpresa


class Usuario(ComAuditoria, Base):
    """Equipe/login. Membro do Hub = usuário ativo."""

    __tablename__ = "usuarios"

    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    nome: Mapped[str]
    senha_hash: Mapped[str | None]
    versao_sessao: Mapped[int] = mapped_column(default=0, server_default="0")
    senha_definida: Mapped[bool] = mapped_column(Computed("senha_hash IS NOT NULL", persisted=True))
    admin: Mapped[bool] = mapped_column(default=False)
    ativo: Mapped[bool] = mapped_column(default=True)
    ultimo_acesso: Mapped[datetime | None]
    totp_secret: Mapped[str | None] = mapped_column(nullable=True)
    totp_ativo: Mapped[bool] = mapped_column(default=False, server_default="false")


class CategoriaDespesa(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "categorias_despesa"
    __table_args__ = (UniqueConstraint("empresa_id", "nome", name="uq_categorias_despesa_empresa_nome"),)

    nome: Mapped[str] = mapped_column(CITEXT)
    ordem: Mapped[int] = mapped_column(default=0)
    ativo: Mapped[bool] = mapped_column(default=True)


class Investidor(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "investidores"
    __table_args__ = (UniqueConstraint("empresa_id", "nome", name="uq_investidores_empresa_nome"),)

    nome: Mapped[str] = mapped_column(CITEXT)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ativo: Mapped[bool] = mapped_column(default=True)
