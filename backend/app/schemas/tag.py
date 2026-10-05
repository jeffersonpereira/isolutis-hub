from uuid import UUID

from pydantic import Field

from app.schemas.comum import Entrada, Leitura


class TagEntrada(Entrada):
    nome: str = Field(min_length=1, max_length=80)


class TagLeitura(Leitura):
    id: UUID
    nome: str
    ativo: bool


class TagsParceiroEntrada(Entrada):
    tag_ids: list[UUID] = Field(max_length=50)
