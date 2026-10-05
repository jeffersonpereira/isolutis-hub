"""Login, troca de senha e gestão da equipe."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.errors import ErroApp, NaoAutenticado, RegraDeNegocio
from app.models import Usuario, UsuarioEmpresa
from app.schemas.usuario import UsuarioAtualizar, UsuarioCriar
from app.security import gerar_hash, precisa_rehash, verificar_senha
from app.services.base import aplicar, conferir_versao, confirmar, obter

# Hash fictício para gastar o mesmo tempo quando o e-mail não existe (evita revelar quem é da equipe).
_HASH_FALSO = gerar_hash("senha-inexistente")
MSG_CREDENCIAIS = "E-mail ou senha incorretos. Confira e tente de novo."


async def autenticar(sessao: AsyncSession, email: str, senha: str) -> Usuario:
    usuario = await sessao.scalar(select(Usuario).where(Usuario.email == email))
    hash_ = usuario.senha_hash if usuario and usuario.senha_hash else _HASH_FALSO
    senha_ok = verificar_senha(senha, hash_)
    if not (usuario and usuario.ativo and usuario.senha_hash and senha_ok):
        raise NaoAutenticado(MSG_CREDENCIAIS)
    usuario.ultimo_acesso = datetime.now(UTC)
    if precisa_rehash(usuario.senha_hash):
        usuario.senha_hash = gerar_hash(senha)
    await confirmar(sessao)
    await sessao.refresh(usuario)
    return usuario


async def trocar_senha(sessao: AsyncSession, usuario: Usuario, atual: str, nova: str) -> None:
    if not (usuario.senha_hash and verificar_senha(atual, usuario.senha_hash)):
        raise RegraDeNegocio("A senha atual não confere.")
    if verificar_senha(nova, usuario.senha_hash):
        raise RegraDeNegocio("Essa já é a sua senha atual. Escolha uma diferente.")
    usuario.senha_hash = gerar_hash(nova)
    usuario.versao_sessao += 1
    await confirmar(sessao)


async def equipe(sessao: AsyncSession, empresa_id: UUID) -> list[Usuario]:
    linhas = (await sessao.execute(
        select(Usuario, UsuarioEmpresa.papel)
        .join(UsuarioEmpresa, UsuarioEmpresa.usuario_id == Usuario.id)
        .where(UsuarioEmpresa.empresa_id == empresa_id, UsuarioEmpresa.ativo, Usuario.ativo)
        .order_by(Usuario.nome)
    )).all()
    usuarios = []
    for usuario, papel in linhas:
        set_committed_value(usuario, "admin", papel == "admin")
        usuarios.append(usuario)
    return usuarios


async def criar(sessao: AsyncSession, empresa_id: UUID, dados: UsuarioCriar) -> Usuario:
    existente = await sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if existente:
        membership = await sessao.get(UsuarioEmpresa, (empresa_id, existente.id))
        if membership:
            raise RegraDeNegocio("Este usuário já faz parte da equipe da empresa.")
        usuario = existente
    else:
        usuario = Usuario(
            email=str(dados.email).lower(), nome=dados.nome, admin=False, senha_hash=gerar_hash(dados.senha)
        )
        sessao.add(usuario)
        await sessao.flush()
    sessao.add(UsuarioEmpresa(empresa_id=empresa_id, usuario_id=usuario.id, papel="admin" if dados.admin else "membro"))
    await _salvar(sessao)
    return usuario


async def atualizar(
    sessao: AsyncSession, quem: Usuario, empresa_id: UUID, id_: UUID, dados: UsuarioAtualizar
) -> Usuario:
    usuario = await obter(sessao, Usuario, id_, "Usuário")
    membership = await sessao.get(UsuarioEmpresa, (empresa_id, id_))
    if membership is None:
        from app.errors import NaoEncontrado
        raise NaoEncontrado("Membro")
    conferir_versao(usuario, dados.versao)
    if usuario.id == quem.id and not (dados.admin and dados.ativo):
        raise RegraDeNegocio("Você não pode tirar o seu próprio acesso de administrador nem se desativar.")
    aplicar(usuario, {"nome": dados.nome})
    membership.papel = "admin" if dados.admin else "membro"
    membership.ativo = dados.ativo
    if dados.senha:
        usuario.senha_hash = gerar_hash(dados.senha)
        usuario.versao_sessao += 1
    await _garantir_algum_admin(sessao, empresa_id)
    await _salvar(sessao)
    return usuario


async def desativar(sessao: AsyncSession, quem: Usuario, empresa_id: UUID, id_: UUID) -> None:
    """ "Remover da equipe": o histórico (quem criou/alterou) é preservado, por isso o usuário só é desativado."""
    usuario = await obter(sessao, Usuario, id_, "Usuário")
    if usuario.id == quem.id:
        raise RegraDeNegocio("Você não pode remover a si mesma.")
    membership = await sessao.get(UsuarioEmpresa, (empresa_id, id_))
    if membership is None:
        from app.errors import NaoEncontrado
        raise NaoEncontrado("Membro")
    membership.ativo = False
    await _garantir_algum_admin(sessao, empresa_id)
    await confirmar(sessao)


async def _garantir_algum_admin(sessao: AsyncSession, empresa_id: UUID) -> None:
    await sessao.flush()
    total = await sessao.scalar(select(func.count()).select_from(UsuarioEmpresa).where(
        UsuarioEmpresa.empresa_id == empresa_id, UsuarioEmpresa.papel == "admin", UsuarioEmpresa.ativo
    ))
    if not total:
        await sessao.rollback()
        raise RegraDeNegocio("Precisa existir pelo menos um administrador ativo.")


async def _salvar(sessao: AsyncSession) -> None:
    try:
        await confirmar(sessao)
    except IntegrityError as e:  # corrida na criação do mesmo e-mail
        await sessao.rollback()
        raise ErroApp("Já existe um usuário com este e-mail.", status=422) from e
