import uuid
from datetime import date, datetime

from sqlalchemy import Computed, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.constantes import StatusEtapa
from app.domain.projeto import progresso
from app.models.base import Base, ComAuditoria, ComEmpresa
from app.models.parceiro import Parceiro


class Projeto(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "projetos"

    titulo: Mapped[str]
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parceiro_negocio.id"))
    negocio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("negocios.id"))
    orcamento_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orcamentos.id"))
    status: Mapped[str] = mapped_column(default="planejamento")
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    inicio: Mapped[date | None]
    entrega: Mapped[date | None]
    objetivo: Mapped[str | None]
    escopo: Mapped[str | None]
    fora_escopo: Mapped[str | None]
    pos_entrega: Mapped[str | None]

    cliente: Mapped[Parceiro] = relationship(lazy="raise", foreign_keys=[cliente_id])
    etapas: Mapped[list["ProjetoEtapa"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan", order_by="ProjetoEtapa.ordem", lazy="raise"
    )

    @property
    def cliente_nome(self) -> str:
        return self.cliente.nome

    @property
    def progresso(self) -> int:
        return progresso(StatusEtapa(e.status) for e in self.etapas)


class ProjetoEtapa(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "projeto_etapas"

    projeto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projetos.id"))
    ordem: Mapped[int]
    titulo: Mapped[str]
    status: Mapped[str] = mapped_column(default="a_fazer")
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    inicio: Mapped[date | None]
    fim: Mapped[date | None]
    descricao: Mapped[str | None]
    entregaveis: Mapped[str | None]

    projeto: Mapped[Projeto] = relationship(back_populates="etapas", lazy="raise")


class Tarefa(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "tarefas"

    titulo: Mapped[str]
    coluna: Mapped[str] = mapped_column(default="a_fazer")
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    prazo: Mapped[date | None]
    prioridade: Mapped[str] = mapped_column(default="media")
    prioridade_ordem: Mapped[int] = mapped_column(
        Computed("CASE prioridade WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END", persisted=True)
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("parceiro_negocio.id"))
    projeto_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projetos.id"))
    descricao: Mapped[str | None]
    concluida_em: Mapped[datetime | None]
    busca: Mapped[str] = mapped_column(
        Computed("imm_unaccent(lower(titulo || ' ' || coalesce(descricao, '')))", persisted=True)
    )

    checklist: Mapped[list["TarefaChecklist"]] = relationship(
        back_populates="tarefa", cascade="all, delete-orphan", order_by="TarefaChecklist.ordem", lazy="raise"
    )


class TarefaChecklist(ComAuditoria, ComEmpresa, Base):
    __tablename__ = "tarefa_checklist"

    tarefa_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tarefas.id"))
    ordem: Mapped[int]
    texto: Mapped[str]
    feito: Mapped[bool] = mapped_column(default=False)

    tarefa: Mapped[Tarefa] = relationship(back_populates="checklist", lazy="raise")
