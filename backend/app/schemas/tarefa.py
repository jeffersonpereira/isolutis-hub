from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.comum import Auditoria, Entrada, Leitura, Texto, TextoLongo

Coluna = Literal["a_fazer", "fazendo", "revisao", "concluido"]
Prioridade = Literal["alta", "media", "baixa"]


class ChecklistEntrada(Entrada):
    id: UUID | None = None
    texto: Texto
    feito: bool = False


class TarefaEntrada(Entrada):
    titulo: Texto
    coluna: Coluna = "a_fazer"
    responsavel_id: UUID | None = None
    prazo: date | None = None
    prioridade: Prioridade = "media"
    cliente_id: UUID | None = None
    projeto_id: UUID | None = None
    descricao: TextoLongo = None
    checklist: list[ChecklistEntrada] = []


class TarefaAtualizar(TarefaEntrada):
    versao: int = Field(ge=1)


class MoverTarefa(Entrada):
    coluna: Coluna
    versao: int = Field(ge=1)


class ChecklistLeitura(Leitura):
    id: UUID
    ordem: int
    texto: str
    feito: bool


class TarefaLeitura(Auditoria):
    titulo: str
    coluna: str
    responsavel_id: UUID | None
    prazo: date | None
    prioridade: str
    cliente_id: UUID | None
    projeto_id: UUID | None
    descricao: str | None
    concluida_em: datetime | None
    checklist: list[ChecklistLeitura]
