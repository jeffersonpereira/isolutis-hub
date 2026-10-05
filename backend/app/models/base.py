"""Base declarativa e colunas de auditoria compartilhadas.

As colunas de auditoria (criado_em, atualizado_em, criado_por, atualizado_por, versao) são mantidas
pelo trigger `set_audit` do banco (ver docs/banco-de-dados.md). O ORM só as lê:
`eager_defaults` busca os valores gerados pelo banco com RETURNING após INSERT/UPDATE.
"""

import uuid
from datetime import datetime

from sqlalchemy import FetchedValue, MetaData, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Mesmos nomes de constraints do schema SQL (útil para o Alembic e mensagens de erro).
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


PK = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


class ComAuditoria:
    """Mixin: id uuid + carimbos de auditoria + `versao` para concorrência otimista."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now(), server_onupdate=FetchedValue())
    atualizado_em: Mapped[datetime] = mapped_column(server_default=func.now(), server_onupdate=FetchedValue())
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_default=FetchedValue())
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_onupdate=FetchedValue())
    versao: Mapped[int] = mapped_column(server_default=text("1"), server_onupdate=FetchedValue())


class ComEmpresa:
    """Coluna de tenant nas entidades cujo ciclo de vida pertence a uma empresa."""

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), server_default=text("app_empresa_id()"), nullable=False
    )

    @declared_attr.directive
    def __mapper_args__(cls) -> dict[str, object]:  # noqa: N805
        # `versao` é incrementada pelo trigger do banco; o ORM só a usa como guarda (UPDATE ... WHERE versao = :lida).
        return {"eager_defaults": True, "version_id_col": cls.versao, "version_id_generator": False}
