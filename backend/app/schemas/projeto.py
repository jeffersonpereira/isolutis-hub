from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.comum import Auditoria, Entrada, Leitura, Texto, TextoLongo, TextoOpcional

StatusProjeto = Literal["planejamento", "construcao", "validacao", "entregue", "pausado"]
StatusEtapa = Literal["a_fazer", "andamento", "concluida"]


class EtapaEntrada(Entrada):
    id: UUID | None = None
    titulo: Texto
    status: StatusEtapa = "a_fazer"
    responsavel_id: UUID | None = None
    inicio: date | None = None
    fim: date | None = None
    descricao: TextoLongo = None
    entregaveis: TextoLongo = None

    @model_validator(mode="after")
    def _datas(self) -> "EtapaEntrada":
        if self.inicio and self.fim and self.fim < self.inicio:
            raise ValueError(f"Na etapa “{self.titulo}”, o término não pode ser antes do início.")
        return self


class ProjetoEntrada(Entrada):
    titulo: Texto
    cliente_id: UUID
    negocio_id: UUID | None = None
    orcamento_id: UUID | None = None
    status: StatusProjeto = "planejamento"
    responsavel_id: UUID | None = None
    inicio: date | None = None
    entrega: date | None = None
    objetivo: TextoLongo = None
    escopo: TextoLongo = None
    fora_escopo: TextoLongo = None
    pos_entrega: TextoLongo = None
    etapas: list[EtapaEntrada] = []

    @model_validator(mode="after")
    def _datas(self) -> "ProjetoEntrada":
        if self.inicio and self.entrega and self.entrega < self.inicio:
            raise ValueError("A entrega prevista não pode ser antes do início.")
        return self


class ProjetoAtualizar(ProjetoEntrada):
    versao: int = Field(ge=1)


class EtapaLeitura(Leitura):
    id: UUID
    ordem: int
    titulo: str
    status: str
    responsavel_id: UUID | None
    inicio: date | None
    fim: date | None
    descricao: str | None
    entregaveis: str | None


class ProjetoLeitura(Auditoria):
    titulo: str
    cliente_id: UUID
    cliente_nome: str
    negocio_id: UUID | None
    orcamento_id: UUID | None
    status: str
    responsavel_id: UUID | None
    inicio: date | None
    entrega: date | None
    objetivo: str | None
    escopo: str | None
    fora_escopo: str | None
    pos_entrega: str | None
    progresso: int
    etapas: list[EtapaLeitura]


class EtapaSugerida(Leitura):
    titulo: str
    descricao: str
    entregaveis: str
    status: str
    inicio: date
    fim: date


class ModeloProjeto(Leitura):
    """Valores iniciais para um projeto novo aberto a partir de um negócio ganho."""

    titulo: str
    cliente_id: UUID
    negocio_id: UUID
    orcamento_id: UUID | None
    responsavel_id: UUID | None
    inicio: date
    escopo: TextoOpcional
    pos_entrega: str
