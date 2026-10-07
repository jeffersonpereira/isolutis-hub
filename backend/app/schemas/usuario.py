from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field

from app.domain.papeis import Papel

from app.schemas.comum import ComVersao, Entrada, Leitura

SENHA = Field(min_length=8, max_length=128)


class UsuarioLeitura(Leitura):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    email: str
    nome: str
    papel: Papel | None = None  # papel na empresa ativa; nulo onde não há empresa (ex.: /auth/eu)
    ativo: bool
    senha_definida: bool
    ultimo_acesso: datetime | None
    versao: int = Field(validation_alias="versao_sessao")  # lê a coluna versao_sessao, mas a API devolve "versao"
    totp_ativo: bool = False


class MembroEquipe(Leitura):
    """Visão mínima da equipe, disponível a qualquer pessoa logada (responsáveis, autoria)."""

    id: UUID
    nome: str
    email: str
    ativo: bool


class LoginEntrada(Entrada):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenSaida(Leitura):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioLeitura


class TrocarSenhaEntrada(Entrada):
    senha_atual: str = Field(min_length=1, max_length=128)
    nova_senha: str = SENHA


class UsuarioCriar(Entrada):
    nome: str = Field(min_length=1, max_length=200)
    email: EmailStr
    senha: str = SENHA
    papel: Papel = "membro"


class UsuarioAtualizar(ComVersao):
    nome: str = Field(min_length=1, max_length=200)
    papel: Papel
    ativo: bool = True
    senha: str | None = Field(default=None, min_length=8, max_length=128)
