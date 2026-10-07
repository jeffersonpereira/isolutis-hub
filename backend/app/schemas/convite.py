from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.comum import Entrada, Leitura


class ConviteEntrada(Entrada):
    nome: str = Field(min_length=1, max_length=200)
    email: EmailStr
    papel: str = Field(pattern="^(admin|membro)$")


class ConviteLeitura(Leitura):
    id: int
    email: str
    papel: str
    criado_em: datetime
    expira_em: datetime
    usado_em: datetime | None = None


class AceitarConviteEntrada(Entrada):
    """Conta nova define a senha aqui; conta existente aceita autenticada e ignora estes campos."""

    senha: str | None = Field(default=None, min_length=8, max_length=128)
    confirmar_senha: str | None = Field(default=None, max_length=128)


class ConviteInfo(Leitura):
    """Informações públicas do convite para exibir na tela de aceitação."""

    email: str
    papel: str
    empresa_nome: str
    criado_por_nome: str
    estado: str  # "valido" | "expirado" | "usado"
    conta_existente: bool = False
