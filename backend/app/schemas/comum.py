"""Tipos e bases compartilhados pelos schemas da API (contrato JSON em snake_case)."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer


def _texto_ou_none(v: object) -> object:
    """Campos de texto opcionais: vazio vira None (o banco tem CHECKs que rejeitam '')."""
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


TextoOpcional = Annotated[str | None, BeforeValidator(_texto_ou_none)]
Texto = Annotated[str, Field(min_length=1, max_length=500)]
TextoLongo = Annotated[Annotated[str, Field(max_length=20000)] | None, BeforeValidator(_texto_ou_none)]

# Dinheiro: entra como número/texto, sai como número JSON (o front trabalha com number).
Dinheiro = Annotated[
    Decimal,
    Field(max_digits=14, decimal_places=2),
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]
DinheiroPositivo = Annotated[Dinheiro, Field(ge=0)]
Quantidade = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=3),
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]


class Entrada(BaseModel):
    """Base de payloads de escrita: rejeita campos desconhecidos e apara espaços."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Leitura(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Auditoria(Leitura):
    id: UUID
    empresa_id: UUID
    criado_em: datetime
    atualizado_em: datetime
    criado_por: UUID | None
    atualizado_por: UUID | None
    versao: int


class ComVersao(Entrada):
    """Payload de edição: `versao` é a que o cliente leu; se mudou no servidor, a resposta é 409."""

    versao: int = Field(ge=1)


def so_digitos(v: object) -> object:
    return re.sub(r"\D", "", v) if isinstance(v, str) else v
