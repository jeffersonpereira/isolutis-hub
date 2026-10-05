"""Dependências do FastAPI: sessão, usuário autenticado e permissão de administrador."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import definir_empresa_da_transacao, definir_usuario_da_transacao, get_session
from app.errors import NaoAutenticado, SemPermissao
from app.models import Empresa, Usuario, UsuarioEmpresa
from sqlalchemy import select
from app.security import ler_token

Sessao = Annotated[AsyncSession, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


async def usuario_atual(
    sessao: Sessao, credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario:
    if credenciais is None:
        raise NaoAutenticado("Entre com seu e-mail e senha.")
    identidade = ler_token(credenciais.credentials)
    usuario = await sessao.get(Usuario, identidade[0]) if identidade else None
    if usuario is None or not usuario.ativo or usuario.versao_sessao != identidade[1]:
        raise NaoAutenticado("Sua sessão expirou. Entre de novo no Hub.")
    # Contrato de auditoria com o banco: o trigger set_audit usa este usuário.
    await definir_usuario_da_transacao(sessao, usuario.id)
    return usuario


async def empresa_atual(
    sessao: Sessao,
    usuario: Annotated[Usuario, Depends(usuario_atual)],
    empresa_id: Annotated[UUID | None, Header(alias="X-Empresa-ID")] = None,
) -> Empresa:
    if empresa_id is None:
        raise SemPermissao("Selecione a empresa ativa enviando o cabeçalho X-Empresa-ID.")
    consulta = select(UsuarioEmpresa).where(UsuarioEmpresa.usuario_id == usuario.id, UsuarioEmpresa.ativo)
    consulta = consulta.where(UsuarioEmpresa.empresa_id == empresa_id)
    memberships = list((await sessao.scalars(consulta)).all())
    if not memberships:
        raise SemPermissao("Você não tem acesso ativo à empresa selecionada.")
    membership = memberships[0]
    await definir_empresa_da_transacao(sessao, membership.empresa_id)
    sessao.info["empresa_id"] = membership.empresa_id
    empresa = await sessao.get(Empresa, membership.empresa_id)
    if empresa is None:
        raise SemPermissao("A empresa selecionada não está disponível.")
    return empresa


async def administrador(
    usuario: Annotated[Usuario, Depends(usuario_atual)],
    empresa: Annotated[Empresa, Depends(empresa_atual)],
    sessao: Sessao,
) -> Usuario:
    membership = await sessao.get(UsuarioEmpresa, (empresa.id, usuario.id))
    if membership is None or not membership.ativo or membership.papel != "admin":
        raise SemPermissao("Só administradores podem gerenciar usuários.")
    return usuario


UsuarioLogado = Annotated[Usuario, Depends(usuario_atual)]
Administrador = Annotated[Usuario, Depends(administrador)]
EmpresaAtual = Annotated[Empresa, Depends(empresa_atual)]
