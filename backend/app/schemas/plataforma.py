from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.domain.papeis import Papel
from app.schemas.comum import Entrada, Leitura, TextoOpcional


class AcessoPlataforma(Leitura):
    operador: bool


class EmpresaPlataforma(Leitura):
    id: UUID
    nome: str
    inscricao: str | None
    status: Literal["ativa", "suspensa"]
    membros_ativos: int
    criado_em: datetime


class EmpresaNova(Entrada):
    nome: str = Field(min_length=1, max_length=150)
    inscricao: TextoOpcional = Field(default=None, max_length=18)  # CNPJ, com ou sem máscara
    admin_nome: str = Field(min_length=1, max_length=200)
    admin_email: EmailStr


class StatusEntrada(Entrada):
    status: Literal["ativa", "suspensa"]


class MembroPlataforma(Leitura):
    usuario_id: UUID
    nome: str
    email: str
    papel: Papel
    ativo: bool  # vínculo com a empresa
    usuario_ativo: bool  # conta
    ultimo_acesso: datetime | None


class ConvitePlataforma(Leitura):
    id: int
    email: str
    papel: Papel
    criado_em: datetime
    expira_em: datetime


class MembroAtualizar(Entrada):
    papel: Papel
    ativo: bool


class EmpresaDetalhe(Leitura):
    empresa: EmpresaPlataforma
    membros: list[MembroPlataforma]
    convites: list[ConvitePlataforma]
