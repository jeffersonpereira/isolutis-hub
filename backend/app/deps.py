"""Dependências do FastAPI: sessão, usuário autenticado, empresa ativa e permissões por papel."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (
    definir_empresa_e_escopo_da_transacao,
    definir_usuario_da_transacao,
    get_session,
    get_session_plataforma,
    plataforma_indisponivel,
)
from app.domain.papeis import Permissao, permissoes_do_papel
from app.errors import NaoAutenticado, SemPermissao
from app.models import Empresa, Usuario, UsuarioEmpresa
from sqlalchemy import select
from app.security import ler_token

# Código de erro 403 que avisa o cliente de que a empresa ativa não vale mais (ele reabre a escolha de empresa).
CODIGO_EMPRESA_INACESSIVEL = "empresa_inacessivel"

Sessao = Annotated[AsyncSession, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


async def _usuario_do_token(sessao: AsyncSession, token: str) -> Usuario | None:
    identidade = ler_token(token)
    usuario = await sessao.get(Usuario, identidade[0]) if identidade else None
    if usuario is None or not usuario.ativo or usuario.versao_sessao != identidade[1]:
        return None
    # Contrato de auditoria com o banco: o trigger set_audit usa este usuário.
    await definir_usuario_da_transacao(sessao, usuario.id)
    return usuario


async def usuario_atual(
    sessao: Sessao, credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario:
    if credenciais is None:
        raise NaoAutenticado("Entre com seu e-mail e senha.")
    usuario = await _usuario_do_token(sessao, credenciais.credentials)
    if usuario is None:
        raise NaoAutenticado("Sua sessão expirou. Entre de novo no Hub.")
    return usuario


async def usuario_opcional(
    sessao: Sessao, credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> Usuario | None:
    """Usuário autenticado, ou None se não há token ou ele é inválido (rotas públicas com modo autenticado)."""
    if credenciais is None:
        return None
    return await _usuario_do_token(sessao, credenciais.credentials)


async def empresa_atual(
    sessao: Sessao,
    usuario: Annotated[Usuario, Depends(usuario_atual)],
    empresa_id: Annotated[UUID | None, Header(alias="X-Empresa-ID")] = None,
) -> Empresa:
    if empresa_id is None:
        raise SemPermissao("Selecione a empresa ativa enviando o cabeçalho X-Empresa-ID.", codigo=CODIGO_EMPRESA_INACESSIVEL)
    consulta = select(UsuarioEmpresa).where(UsuarioEmpresa.usuario_id == usuario.id, UsuarioEmpresa.ativo)
    # populate_existing: papel, vínculo e status valem na requisição seguinte, sem depender de objeto em cache.
    consulta = consulta.where(UsuarioEmpresa.empresa_id == empresa_id).execution_options(populate_existing=True)
    memberships = list((await sessao.scalars(consulta)).all())
    if not memberships:
        raise SemPermissao("Você não tem acesso ativo à empresa selecionada.", codigo=CODIGO_EMPRESA_INACESSIVEL)
    membership = memberships[0]
    await definir_empresa_e_escopo_da_transacao(sessao, membership.empresa_id)
    sessao.info["papel"] = membership.papel
    empresa = await sessao.get(Empresa, membership.empresa_id, populate_existing=True)
    if empresa is None or empresa.status != "ativa":  # suspensa pelo operador: dados preservados, acesso recusado
        raise SemPermissao("A empresa selecionada não está disponível.", codigo=CODIGO_EMPRESA_INACESSIVEL)
    return empresa


async def sessao_operador(
    sessao: Sessao,
    usuario: Annotated[Usuario, Depends(usuario_atual)],
    plataforma: Annotated[AsyncSession | None, Depends(get_session_plataforma)],
) -> AsyncSession:
    """Sessão do papel hub_plataforma para o operador autenticado; recusa quem não é operador.

    A identidade é conferida no banco (função eh_operador_plataforma) e de novo dentro de cada função plataforma_*.
    """
    if not await sessao.scalar(text("select eh_operador_plataforma()")):
        raise SemPermissao("Esta área é restrita ao operador da plataforma.")
    if plataforma is None:
        raise plataforma_indisponivel()
    await definir_usuario_da_transacao(plataforma, usuario.id)
    return plataforma


sessao_operador.permissao_exigida = "plataforma"  # type: ignore[attr-defined]  # o teste estrutural de rotas reconhece

MENSAGEM_SEM_PERMISSAO = "Seu papel nesta empresa não permite acessar esta área."
MENSAGENS_POR_PERMISSAO: dict[str, str] = {"administracao": "Só administradores podem gerenciar usuários."}


def exige(permissao: Permissao):  # noqa: ANN201
    """Fábrica de dependência: exige a permissão no papel que o usuário tem na empresa ativa (lido a cada requisição).

    A função devolvida carrega `permissao_exigida`; o teste de rotas usa isso para garantir que nenhuma rota
    de dados fique sem checagem.
    """

    async def verificar(
        usuario: Annotated[Usuario, Depends(usuario_atual)],
        _empresa: Annotated[Empresa, Depends(empresa_atual)],
        sessao: Sessao,
    ) -> Usuario:
        if permissao not in permissoes_do_papel(sessao.info.get("papel")):
            raise SemPermissao(MENSAGENS_POR_PERMISSAO.get(permissao, MENSAGEM_SEM_PERMISSAO))
        return usuario

    verificar.permissao_exigida = permissao  # type: ignore[attr-defined]
    return verificar


requer_base = exige("base")
requer_comercial = exige("comercial")
requer_financeiro = exige("financeiro")
requer_administracao = exige("administracao")
administrador = requer_administracao  # nome histórico, mantido nos usos existentes

UsuarioLogado = Annotated[Usuario, Depends(usuario_atual)]
UsuarioOpcional = Annotated[Usuario | None, Depends(usuario_opcional)]
Administrador = Annotated[Usuario, Depends(administrador)]
EmpresaAtual = Annotated[Empresa, Depends(empresa_atual)]
SessaoOperador = Annotated[AsyncSession, Depends(sessao_operador)]
