"""Convites por e-mail para ingressar na equipe de uma empresa."""

import smtplib
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import NaoAutenticado, NaoEncontrado, RegraDeNegocio, SemPermissao


def _com_tz(dt: datetime) -> datetime:
    """Garante que o datetime tem timezone (PostgreSQL TIMESTAMPTZ já devolve com tz; naive assume UTC)."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
from app.models import Convite, Empresa, Usuario, UsuarioEmpresa
from app.schemas.convite import ConviteEntrada
from app.security import gerar_hash
from app.services.base import confirmar


async def criar_convite(
    sessao: AsyncSession,
    empresa_id: UUID,
    dados: ConviteEntrada,
    criado_por_id: UUID,
) -> Convite:
    email = str(dados.email).lower()

    # Verifica se já é membro ativo
    membro = await sessao.scalar(
        select(UsuarioEmpresa)
        .join(Usuario, Usuario.id == UsuarioEmpresa.usuario_id)
        .where(
            UsuarioEmpresa.empresa_id == empresa_id,
            UsuarioEmpresa.ativo == True,  # noqa: E712
            Usuario.email == email,
            Usuario.ativo == True,  # noqa: E712
        )
    )
    if membro:
        raise RegraDeNegocio("Este e-mail já é membro da equipe.")

    # Invalida convites pendentes anteriores para o mesmo e-mail + empresa
    agora = datetime.now(UTC)
    await sessao.execute(
        delete(Convite).where(
            Convite.empresa_id == empresa_id,
            Convite.email == email,
            Convite.usado_em.is_(None),
            Convite.expira_em > agora,
        )
    )

    convite = Convite(
        email=email,
        empresa_id=empresa_id,
        papel=dados.papel,
        criado_por=criado_por_id,
        expira_em=agora + timedelta(hours=72),
    )
    sessao.add(convite)
    await confirmar(sessao)
    await sessao.refresh(convite)

    from app.config import get_settings

    enviar_email_convite(get_settings(), convite, dados.nome)
    return convite


async def listar_pendentes(sessao: AsyncSession, empresa_id: UUID) -> list[Convite]:
    agora = datetime.now(UTC)
    resultado = await sessao.scalars(
        select(Convite)
        .where(
            Convite.empresa_id == empresa_id,
            Convite.usado_em.is_(None),
            Convite.expira_em > agora,
        )
        .order_by(Convite.criado_em.desc())
    )
    return list(resultado.all())


async def cancelar_convite(sessao: AsyncSession, convite_id: int, empresa_id: UUID) -> None:
    convite = await sessao.scalar(
        select(Convite).where(Convite.id == convite_id, Convite.empresa_id == empresa_id)
    )
    if convite is None:
        raise NaoEncontrado("Convite")
    await sessao.delete(convite)
    await confirmar(sessao)


async def verificar_convite_publico(sessao: AsyncSession, token: str) -> dict[str, object]:
    """Retorna as informações públicas de um convite para exibir na tela de aceitação."""
    convite = await sessao.scalar(select(Convite).where(Convite.token == token))
    if convite is None:
        raise NaoEncontrado("Convite")

    empresa = await sessao.get(Empresa, convite.empresa_id)
    criador = await sessao.get(Usuario, convite.criado_por)
    conta_existente = await sessao.scalar(select(Usuario.id).where(Usuario.email == convite.email)) is not None

    agora = datetime.now(UTC)
    if convite.usado_em is not None:
        estado = "usado"
    elif _com_tz(convite.expira_em) < agora:
        estado = "expirado"
    else:
        estado = "valido"

    return {
        "email": convite.email,
        "papel": convite.papel,
        "empresa_nome": empresa.nome if empresa else "",
        "criado_por_nome": criador.nome if criador else "",
        "estado": estado,
        "conta_existente": conta_existente,
    }


async def aceitar_convite(
    sessao: AsyncSession, token: str, senha: str | None, autenticado: Usuario | None
) -> Usuario:
    """Aceita o convite.

    Conta nova: cria o usuário com a senha informada. Conta existente: exige que quem aceita esteja
    autenticado (login normal, com 2FA se ativo) como o dono do e-mail do convite; a senha e o estado
    da conta nunca são alterados por este fluxo.
    """
    # FOR UPDATE: dois aceites simultâneos do mesmo token são serializados e só o primeiro conclui.
    convite = await sessao.scalar(select(Convite).where(Convite.token == token).with_for_update())
    if convite is None:
        raise NaoEncontrado("Convite")

    agora = datetime.now(UTC)
    if convite.usado_em is not None:
        raise RegraDeNegocio("Este convite já foi utilizado. Faça login normalmente.")
    if _com_tz(convite.expira_em) < agora:
        raise RegraDeNegocio("Este convite expirou. Peça ao administrador que envie um novo convite.")

    usuario = await sessao.scalar(select(Usuario).where(Usuario.email == convite.email))
    if usuario is None:
        if not senha:
            raise RegraDeNegocio("Defina uma senha para aceitar o convite.")
        usuario = Usuario(
            email=convite.email,
            nome=convite.email.split("@")[0],  # nome provisório; pode ser atualizado depois
            senha_hash=gerar_hash(senha),
        )
        sessao.add(usuario)
        await sessao.flush()
    else:
        if autenticado is None:
            raise NaoAutenticado(f"Entre com a conta {convite.email} para aceitar este convite.")
        if autenticado.id != usuario.id:
            raise SemPermissao("Este convite é para outro e-mail.")
        if not usuario.ativo:
            raise RegraDeNegocio("Esta conta está desativada. Procure o administrador da empresa.")

    # A membership sai por função SECURITY DEFINER (migração 0009): o aceite é público e quem aceita ainda não é
    # admin da empresa, então as políticas RLS de usuario_empresa recusariam um INSERT/UPDATE direto. A função
    # revalida convite e usuário, cria ou reativa a membership com o papel do convite e consome o convite.
    await sessao.execute(
        text("select vincular_membro_por_convite(:convite, :usuario)"),
        {"convite": convite.id, "usuario": usuario.id},
    )

    await confirmar(sessao)
    await sessao.refresh(usuario)
    return usuario


def enviar_email_convite(settings: object, convite: Convite, nome_convidado: str) -> None:
    """Envia o e-mail de convite. Se SMTP não estiver configurado, ignora silenciosamente."""
    smtp_host = getattr(settings, "smtp_host", "")
    if not smtp_host:
        return

    smtp_port = getattr(settings, "smtp_port", 587)
    smtp_user = getattr(settings, "smtp_user", "")
    smtp_password = getattr(settings, "smtp_password", "")
    smtp_from = getattr(settings, "smtp_from", "")
    base_url = getattr(settings, "base_url", "http://localhost:5173")

    link = f"{base_url}/convite/{convite.token}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Você foi convidado para o iSolutis Hub"
    msg["From"] = smtp_from
    msg["To"] = convite.email

    html_body = f"""
    <p>Olá {nome_convidado},</p>
    <p>Você foi convidado para acessar o iSolutis Hub.</p>
    <p><a href="{link}">Clique aqui para aceitar o convite</a></p>
    <p>Este link expira em 72 horas.</p>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [convite.email], msg.as_string())
    except Exception as exc:  # noqa: BLE001
        # Falha no envio não deve bloquear a criação do convite; logar e continuar.
        import logging

        logging.getLogger(__name__).warning("Falha ao enviar e-mail de convite: %s", exc)
