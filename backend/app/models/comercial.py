import uuid
from datetime import date
from datetime import date as _date
from decimal import Decimal

from sqlalchemy import Computed, FetchedValue, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.constantes import StatusOrcamento
from app.domain.datas import hoje
from app.domain.orcamento import ItemCalculavel, TotaisOrcamento, status_efetivo, valido_ate
from app.domain.orcamento import totais as totais_orcamento
from app.models.base import Base, ComAuditoria, ComEmpresa
from app.models.parceiro import Parceiro


class Produto(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "produtos"

    nome: Mapped[str]
    tipo: Mapped[str]
    unidade: Mapped[str] = mapped_column(default="projeto")
    preco: Mapped[Decimal] = mapped_column(default=Decimal("0"))
    ativo: Mapped[bool] = mapped_column(default=True)
    descricao: Mapped[str | None]


class Negocio(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "negocios"

    titulo: Mapped[str]
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"))
    etapa: Mapped[str] = mapped_column(default="lead")
    valor: Mapped[Decimal] = mapped_column(default=Decimal("0"))
    mensal: Mapped[Decimal] = mapped_column(default=Decimal("0"))
    previsao: Mapped[date | None]
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    origem: Mapped[str | None]
    motivo_perda: Mapped[str | None]
    obs: Mapped[str | None]
    fechado_em: Mapped[date | None]

    cliente: Mapped[Parceiro] = relationship(lazy="raise", foreign_keys=[cliente_id])
    # Preenchido pela consulta (EXISTS em lancamentos_receita); não é coluna.
    faturado: bool = False

    @property
    def cliente_nome(self) -> str:
        return self.cliente.nome


class Orcamento(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "orcamentos"

    # Gerado pelo trigger do banco (AAAA-NNN, atômico) e devolvido por RETURNING.
    numero: Mapped[str] = mapped_column(server_default=FetchedValue())
    data: Mapped[date]
    validade_dias: Mapped[int] = mapped_column(default=15)
    status: Mapped[str] = mapped_column(default="rascunho")
    desconto: Mapped[Decimal] = mapped_column(default=Decimal("0"))
    obs: Mapped[str | None]
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"))
    negocio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("negocios.id"))
    aprovado_em: Mapped[date | None]

    cliente: Mapped[Parceiro] = relationship(lazy="raise", foreign_keys=[cliente_id])
    itens: Mapped[list["OrcamentoItem"]] = relationship(
        back_populates="orcamento", cascade="all, delete-orphan", order_by="OrcamentoItem.ordem", lazy="raise"
    )

    @property
    def cliente_nome(self) -> str:
        return self.cliente.nome

    @property
    def valido_ate(self) -> _date:
        return valido_ate(self.data, self.validade_dias)

    @property
    def status_exibido(self) -> str:
        return status_efetivo(StatusOrcamento(self.status), self.data, self.validade_dias, hoje()).value

    @property
    def totais(self) -> TotaisOrcamento:
        return totais_orcamento((ItemCalculavel(i.qtd, i.preco_unitario, i.mensal) for i in self.itens), self.desconto)

    @property
    def total_projeto(self) -> Decimal:
        return self.totais.projeto

    @property
    def total_mensal(self) -> Decimal:
        return self.totais.mensal


class OrcamentoItem(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "orcamento_itens"

    orcamento_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orcamentos.id"))
    ordem: Mapped[int]
    produto_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("produtos.id"))
    descricao: Mapped[str]
    qtd: Mapped[Decimal] = mapped_column(default=Decimal("1"))
    preco_unitario: Mapped[Decimal] = mapped_column(default=Decimal("0"))
    mensal: Mapped[bool] = mapped_column(default=False)
    subtotal: Mapped[Decimal] = mapped_column(Computed("round(qtd * preco_unitario, 2)", persisted=True))

    orcamento: Mapped[Orcamento] = relationship(back_populates="itens", lazy="raise")
