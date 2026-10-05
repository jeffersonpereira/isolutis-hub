"""Memberships, tags e seleção da empresa ativa."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UsuarioEmpresa(Base):
    __tablename__ = "usuario_empresa"

    empresa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("empresa.id"), primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    papel: Mapped[str] = mapped_column(String(16))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class TagParceiro(Base):
    __tablename__ = "tag_parceiro"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    empresa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("empresa.id"), server_default=text("app_empresa_id()"))
    nome: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())


class ParceiroTag(Base):
    __tablename__ = "parceiro_tag"

    empresa_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("app_empresa_id()"))
    parceiro_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
