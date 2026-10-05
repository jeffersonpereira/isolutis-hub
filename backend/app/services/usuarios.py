"""Serviços de gerenciamento de usuários."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.usuario import UsuarioAtualizar, UsuarioCriar


async def equipe(sessao: AsyncSession, empresa_id: UUID) -> list:
    """Listar membros da equipe. Placeholder para integração com banco."""
    # TODO: Implementar query que retorna usuários da empresa
    return []


async def criar(sessao: AsyncSession, empresa_id: UUID, dados: UsuarioCriar):
    """Criar novo usuário com validação."""
    # TODO: Hash de senha, criar registro no banco
    # Validações já feitas em UsuarioCriar schema
    pass


async def atualizar(
    sessao: AsyncSession,
    quem: object,  # UsuarioLogado
    empresa_id: UUID,
    usuario_id: UUID,
    dados: UsuarioAtualizar,
) -> object:
    """Atualizar usuário com verificação de permissões.

    Regras:
    - Usuário pode atualizar apenas a si mesmo, exceto nome/admin
    - Admin pode atualizar qualquer usuário
    - Um usuário não pode remover suas próprias permissões de admin
    """
    # TODO: Implementar lógica de atualização com RLS
    pass


async def desativar(
    sessao: AsyncSession,
    quem: object,  # UsuarioLogado
    empresa_id: UUID,
    usuario_id: UUID,
) -> None:
    """Desativar usuário da equipe."""
    # TODO: Implementar desativação
    pass
