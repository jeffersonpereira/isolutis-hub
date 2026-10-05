"""Parceiro de negócio: cadastro único de pessoas e empresas (hub de papéis).

Um parceiro é criado uma vez e assume papéis (cliente, fornecedor, funcionário…) em `parceiro_papel`.
Negócios, orçamentos, projetos, tarefas e lançamentos de receita apontam para o parceiro **no papel de cliente**
(`cliente_id`); o banco recusa quem não tem o papel.
"""

import uuid
from datetime import datetime
from decimal import Decimal  # noqa: F401  (reexport de tipo usado por outros módulos)

from sqlalchemy import FetchedValue, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nome: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None]


class Municipio(Base):
    __tablename__ = "municipio"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nome: Mapped[str]
    uf: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None]


class PapelParceiro(Base):
    """Domínio editável dos papéis que um parceiro pode assumir."""

    __tablename__ = "papel_parceiro"

    codigo: Mapped[str] = mapped_column(primary_key=True)
    nome: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)


class ParceiroPapel(Base):
    __tablename__ = "parceiro_papel"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("app_empresa_id()")
    )
    parceiro_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"), primary_key=True)
    papel: Mapped[str] = mapped_column(ForeignKey("papel_parceiro.codigo"), primary_key=True)


class Parceiro(Base):
    __tablename__ = "parceiro_negocio"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("empresa.id"))
    tipo_pessoa: Mapped[str] = mapped_column(default="PJ")
    cpf_cnpj: Mapped[str | None]
    nome: Mapped[str]
    segmento: Mapped[str | None]
    contato: Mapped[str | None]
    cargo: Mapped[str | None]
    telefone: Mapped[str | None]
    email: Mapped[str | None]
    origem: Mapped[str | None]
    obs: Mapped[str | None]
    endereco: Mapped[str | None]
    cep: Mapped[str | None]
    municipio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("municipio.id"))
    # Carimbos mantidos pelo trigger (mesmos nomes de atributo das demais entidades: criado_em/atualizado_em)
    criado_em: Mapped[datetime] = mapped_column("created_at", server_default=func.now(), server_onupdate=FetchedValue())
    atualizado_em: Mapped[datetime | None] = mapped_column("updated_at", server_onupdate=FetchedValue())
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_default=FetchedValue())
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_onupdate=FetchedValue())
    versao: Mapped[int] = mapped_column(server_default=text("1"), server_onupdate=FetchedValue())

    municipio: Mapped[Municipio | None] = relationship(lazy="raise")
    papeis: Mapped[list[ParceiroPapel]] = relationship(cascade="all, delete-orphan", lazy="raise")

    __mapper_args__ = {"eager_defaults": True, "version_id_col": versao, "version_id_generator": False}

    @property
    def codigos_de_papel(self) -> list[str]:
        return sorted(p.papel for p in self.papeis)

    @property
    def municipio_nome(self) -> str | None:
        return self.municipio.nome if self.municipio else None

    @property
    def uf(self) -> str | None:
        return self.municipio.uf if self.municipio else None
