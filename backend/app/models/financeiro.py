import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ComAuditoria, ComEmpresa
from app.models.parceiro import Parceiro
from app.models.usuario import CategoriaDespesa, Investidor


class LancamentoReceita(ComAuditoria, ComEmpresa, Base):
    """Conta a receber/recebida (no sistema anterior: "faturamento")."""

    __tablename__ = "lancamentos_receita"

    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"))
    tipo: Mapped[str]
    descricao: Mapped[str]
    valor: Mapped[Decimal]
    vencimento: Mapped[date]
    status: Mapped[str] = mapped_column(default="previsto")
    recebido_em: Mapped[date | None]
    nf: Mapped[str | None]
    negocio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("negocios.id"))
    orcamento_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orcamentos.id"))
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    parcela: Mapped[int | None]
    total_parcelas: Mapped[int | None]

    cliente: Mapped[Parceiro] = relationship(lazy="raise", foreign_keys=[cliente_id])

    @property
    def cliente_nome(self) -> str:
        return self.cliente.nome


class Despesa(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "despesas"

    data: Mapped[date]
    descricao: Mapped[str]
    valor: Mapped[Decimal]
    categoria_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categorias_despesa.id"))
    status: Mapped[str] = mapped_column(default="a_pagar")
    pago_em: Mapped[date | None]
    fornecedor: Mapped[str | None]
    obs: Mapped[str | None]
    grupo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    parcela: Mapped[int | None]
    total_parcelas: Mapped[int | None]

    categoria: Mapped[CategoriaDespesa] = relationship(lazy="raise")

    @property
    def categoria_nome(self) -> str:
        return self.categoria.nome


class Investimento(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "investimentos"

    data: Mapped[date]
    descricao: Mapped[str]
    valor: Mapped[Decimal]
    investidor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investidores.id"))
    forma: Mapped[str]
    obs: Mapped[str | None]

    investidor: Mapped[Investidor] = relationship(lazy="raise")

    @property
    def investidor_nome(self) -> str:
        return self.investidor.nome
