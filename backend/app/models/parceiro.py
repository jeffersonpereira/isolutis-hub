"""Parceiro de negócio: cadastro único de pessoas e empresas (hub de papéis).

Um parceiro é criado uma vez e assume papéis (cliente, fornecedor, funcionário…) em `parceiro_papel`.
Negócios, orçamentos, projetos, tarefas e lançamentos de receita apontam para o parceiro **no papel de cliente**
(`cliente_id`); o banco recusa quem não tem o papel.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import FetchedValue, ForeignKey, LargeBinary, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    onboarding_concluido: Mapped[bool] = mapped_column(default=False, server_default="false")
    segmento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # ativa | suspensa; só a área da plataforma altera (gatilho no banco). Suspensa recusa o acesso, sem apagar dados.
    status: Mapped[str] = mapped_column(String(10), default="ativa", server_default="ativa")
    # Cadastro completo (todos opcionais; `nome` segue como nome de exibição no Hub)
    tipo_inscricao: Mapped[str | None]
    inscricao: Mapped[str | None]
    razao_social: Mapped[str | None]
    nome_fantasia: Mapped[str | None]
    inscricao_estadual: Mapped[str | None]
    inscricao_municipal: Mapped[str | None]
    cnae_codigo: Mapped[str | None]
    cnae_descricao: Mapped[str | None]
    regime_tributario: Mapped[str | None]
    data_abertura: Mapped[date | None]
    email: Mapped[str | None]
    telefone: Mapped[str | None]
    site: Mapped[str | None]
    cep: Mapped[str | None]
    logradouro: Mapped[str | None]
    numero: Mapped[str | None]
    complemento: Mapped[str | None]
    bairro: Mapped[str | None]
    municipio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("municipio.id"))
    # Identidade visual: logomarca (bytes + tipo MIME) e paleta {"primaria": "#rrggbb", "destaque": "#rrggbb"}
    logo: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    logo_tipo: Mapped[str | None]
    logo_atualizada_em: Mapped[datetime | None]
    paleta: Mapped[dict[str, str] | None] = mapped_column(JSONB(none_as_null=True))


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


class ParceiroSocio(Base):
    """Participação (%) de um parceiro com o papel `socio`; a soma por empresa não passa de 100."""

    __tablename__ = "parceiro_socio"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("app_empresa_id()")
    )
    parceiro_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"), primary_key=True)
    participacao_percentual: Mapped[Decimal]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None]


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
    # Dono do cliente (carteira): define quem o enxerga e edita (RLS por escopo, migração 0015).
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    municipio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("municipio.id"))
    # Carimbos mantidos pelo trigger (mesmos nomes de atributo das demais entidades: criado_em/atualizado_em)
    criado_em: Mapped[datetime] = mapped_column("created_at", server_default=func.now(), server_onupdate=FetchedValue())
    atualizado_em: Mapped[datetime | None] = mapped_column("updated_at", server_onupdate=FetchedValue())
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_default=FetchedValue())
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), server_onupdate=FetchedValue())
    versao: Mapped[int] = mapped_column(server_default=text("1"), server_onupdate=FetchedValue())

    municipio: Mapped[Municipio | None] = relationship(lazy="raise")
    papeis: Mapped[list[ParceiroPapel]] = relationship(cascade="all, delete-orphan", lazy="raise")
    socio: Mapped[ParceiroSocio | None] = relationship(cascade="all, delete-orphan", lazy="raise", uselist=False)

    __mapper_args__ = {"eager_defaults": True, "version_id_col": versao, "version_id_generator": False}

    @property
    def codigos_de_papel(self) -> list[str]:
        return sorted(p.papel for p in self.papeis)

    @property
    def participacao_percentual(self) -> Decimal | None:
        return self.socio.participacao_percentual if self.socio else None

    @property
    def municipio_nome(self) -> str | None:
        return self.municipio.nome if self.municipio else None

    @property
    def uf(self) -> str | None:
        return self.municipio.uf if self.municipio else None
