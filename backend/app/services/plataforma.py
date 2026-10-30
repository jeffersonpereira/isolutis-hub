"""Área da plataforma: o operador cria empresas e gerencia membros sem tocar nos dados de negócio.

Tudo passa por funções plataforma_* do banco (migração 0017), executadas com o papel hub_plataforma: elas conferem o
operador, aplicam as regras e gravam a auditoria. Este módulo só chama as funções, traduz os erros e envia os e-mails.
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.errors import ErroApp, NaoEncontrado, RegraDeNegocio, SemPermissao
from app.models import Convite
from app.schemas.convite import ConviteEntrada
from app.schemas.plataforma import EmpresaNova
from app.services.convites import enviar_email_convite

Linha = dict[str, Any]


def _traduzir(exc: DBAPIError) -> Exception | None:
    """Erros levantados pelas funções do banco (RAISE com mensagem em português) viram erros da API."""
    origem = exc.orig
    estado = getattr(origem, "sqlstate", None)
    diag = getattr(origem, "diag", None)
    mensagem = getattr(diag, "message_primary", None) or str(origem)
    if estado == "42501":
        return SemPermissao(mensagem)
    if estado == "23514":
        return RegraDeNegocio(mensagem)
    if estado == "23505":
        return RegraDeNegocio("Já existe uma empresa com este CNPJ.")
    if estado == "P0002":
        return ErroApp(mensagem, codigo=NaoEncontrado.codigo, status=NaoEncontrado.status)
    return None


async def _chamar(sessao: AsyncSession, sql: str, **parametros: object) -> Sequence[Linha]:
    """Executa uma função do banco; o savepoint mantém a sessão utilizável depois de uma recusa."""
    try:
        async with sessao.begin_nested():
            resultado = await sessao.execute(text(sql), parametros)
            return [dict(linha) for linha in resultado.mappings().all()] if resultado.returns_rows else []
    except DBAPIError as exc:
        traduzido = _traduzir(exc)
        if traduzido is None:
            raise
        raise traduzido from exc


async def eh_operador(sessao: AsyncSession) -> bool:
    return bool(await sessao.scalar(text("select eh_operador_plataforma()")))


async def listar_empresas(sessao: AsyncSession, busca: str | None) -> list[Linha]:
    linhas = await _chamar(
        sessao, "select * from plataforma_listar_empresas(cast(:busca as text), cast(null as uuid))", busca=busca
    )
    return list(linhas)


async def obter_empresa(sessao: AsyncSession, empresa_id: UUID) -> Linha:
    linhas = await _chamar(
        sessao, "select * from plataforma_listar_empresas(cast(null as text), cast(:id as uuid))", id=empresa_id
    )
    if not linhas:
        raise NaoEncontrado("Empresa")
    return linhas[0]


async def detalhe_empresa(sessao: AsyncSession, empresa_id: UUID) -> dict[str, object]:
    empresa = await obter_empresa(sessao, empresa_id)
    membros = await _chamar(sessao, "select * from plataforma_listar_membros(cast(:id as uuid))", id=empresa_id)
    convites = await _chamar(sessao, "select * from plataforma_listar_convites(cast(:id as uuid))", id=empresa_id)
    return {"empresa": empresa, "membros": list(membros), "convites": list(convites)}


def _enviar_convite(email: str, token: UUID, nome: str) -> None:
    # O e-mail só sai depois do commit; o convite transitório só carrega o que o e-mail usa (token e destinatário).
    enviar_email_convite(get_settings(), Convite(email=email, token=token), nome)


async def criar_empresa(sessao: AsyncSession, dados: EmpresaNova) -> Linha:
    email = str(dados.admin_email).lower()
    linhas = await _chamar(
        sessao,
        "select * from plataforma_criar_empresa(cast(:nome as text), cast(:inscricao as text), cast(:email as text))",
        nome=dados.nome, inscricao=dados.inscricao, email=email,
    )
    criada = linhas[0]
    await sessao.commit()
    _enviar_convite(email, criada["token"], dados.admin_nome)
    return await obter_empresa(sessao, criada["empresa_id"])


async def definir_status(sessao: AsyncSession, empresa_id: UUID, status: str) -> Linha:
    await _chamar(
        sessao, "select plataforma_definir_status(cast(:id as uuid), cast(:status as text))", id=empresa_id, status=status
    )
    await sessao.commit()
    return await obter_empresa(sessao, empresa_id)


async def convidar(sessao: AsyncSession, empresa_id: UUID, dados: ConviteEntrada) -> bool:
    """Adiciona o membro à empresa. E-mail de conta já existente entra direto (sem convite); devolve se foi direto."""
    email = str(dados.email).lower()
    linhas = await _chamar(
        sessao,
        "select * from plataforma_convidar(cast(:id as uuid), cast(:email as text), cast(:papel as text))",
        id=empresa_id, email=email, papel=dados.papel,
    )
    await sessao.commit()
    resultado = linhas[0]
    if resultado["usuario_id"] is not None:
        return True
    _enviar_convite(email, resultado["token"], dados.nome)
    return False


async def cancelar_convite(sessao: AsyncSession, empresa_id: UUID, convite_id: int) -> None:
    await _chamar(
        sessao,
        "select plataforma_cancelar_convite(cast(:empresa as uuid), cast(:convite as integer))",
        empresa=empresa_id, convite=convite_id,
    )
    await sessao.commit()


async def definir_membro(sessao: AsyncSession, empresa_id: UUID, usuario_id: UUID, papel: str, ativo: bool) -> None:
    await _chamar(
        sessao,
        "select plataforma_definir_membro(cast(:empresa as uuid), cast(:usuario as uuid), cast(:papel as text), cast(:ativo as boolean))",
        empresa=empresa_id, usuario=usuario_id, papel=papel, ativo=ativo,
    )
    await sessao.commit()
