"""Schemas de validação para usuários e equipe."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=150)


class UsuarioCriar(UsuarioBase):
    """Payload para criar novo usuário."""

    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    admin: bool = False

    @field_validator("email")
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("senha")
    @classmethod
    def senha_validar(cls, v: str) -> str:
        """Validar força mínima de senha."""
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula.")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um dígito.")
        return v


class UsuarioAtualizar(UsuarioBase):
    """Payload para atualizar usuário. Admin não pode ser alterado (apenas em desativação)."""

    senha: str | None = Field(default=None, min_length=8, max_length=128)
    ativo: bool = True
    versao: int

    @field_validator("senha", mode="before")
    @classmethod
    def senha_validar(cls, v: str | None) -> str | None:
        """Validar força de senha se fornecida."""
        if v is None:
            return None
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula.")
        if not any(c.islower() for c in v):
            raise ValueError("Senha deve conter pelo menos uma letra minúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos um dígito.")
        return v


class MembroEquipe(BaseModel):
    """Resposta para listar membros da equipe."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    email: str
    admin: bool
    ativo: bool


class UsuarioLeitura(MembroEquipe):
    """Resposta completa de usuário (com último acesso)."""

    senha_definida: bool
    ultimo_acesso: str | None
    versao: int
