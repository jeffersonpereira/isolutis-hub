"""Alertas automáticos por e-mail: vencimentos do dia e orçamentos sem resposta."""

import logging
import smtplib
from datetime import UTC, date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comercial import Orcamento
from app.models.financeiro import LancamentoReceita
from app.models.parceiro import Empresa
from app.models.tenant import UsuarioEmpresa
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Jobs principais chamados pelo scheduler
# ---------------------------------------------------------------------------

async def enviar_alertas_vencimentos(db: AsyncSession) -> None:
    """Envia e-mails para lançamentos que vencem hoje e ainda não foram notificados."""
    hoje = date.today()

    result = await db.execute(
        select(LancamentoReceita).where(
            LancamentoReceita.vencimento == hoje,
            LancamentoReceita.status != "recebido",
            LancamentoReceita.notificado_em.is_(None),
        )
    )
    lancamentos = result.scalars().all()

    por_empresa: dict[UUID, list[LancamentoReceita]] = {}
    for l in lancamentos:
        por_empresa.setdefault(l.empresa_id, []).append(l)

    for empresa_id, items in por_empresa.items():
        try:
            admin = await _buscar_admin(db, empresa_id)
            if not admin:
                logger.warning("Nenhum admin encontrado para empresa %s; alerta ignorado.", empresa_id)
                continue

            html = _render_template_vencimentos(items)
            _enviar_email_simples(admin.email, "Lançamentos vencendo hoje — iSolutis Hub", html)

            agora = datetime.now(UTC)
            for l in items:
                l.notificado_em = agora
            await db.commit()
        except Exception:
            logger.exception("Erro ao notificar vencimentos para empresa %s.", empresa_id)
            await db.rollback()


async def enviar_alertas_orcamentos(db: AsyncSession) -> None:
    """Envia e-mails para orçamentos sem resposta há 7 ou mais dias."""
    limite = date.today() - timedelta(days=7)

    result = await db.execute(
        select(Orcamento).where(
            Orcamento.status == "enviado",
            Orcamento.data <= limite,
            Orcamento.notificado_em.is_(None),
        )
    )
    orcamentos = result.scalars().all()

    por_empresa: dict[UUID, list[Orcamento]] = {}
    for o in orcamentos:
        por_empresa.setdefault(o.empresa_id, []).append(o)

    for empresa_id, items in por_empresa.items():
        try:
            admin = await _buscar_admin(db, empresa_id)
            if not admin:
                logger.warning("Nenhum admin encontrado para empresa %s; alerta ignorado.", empresa_id)
                continue

            html = _render_template_orcamentos(items)
            _enviar_email_simples(admin.email, "Orçamentos aguardando resposta — iSolutis Hub", html)

            agora = datetime.now(UTC)
            for o in items:
                o.notificado_em = agora
            await db.commit()
        except Exception:
            logger.exception("Erro ao notificar orçamentos para empresa %s.", empresa_id)
            await db.rollback()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _buscar_admin(db: AsyncSession, empresa_id: UUID) -> Usuario | None:
    """Retorna o primeiro usuário admin ativo da empresa, ou None."""
    result = await db.execute(
        select(Usuario)
        .join(UsuarioEmpresa, UsuarioEmpresa.usuario_id == Usuario.id)
        .where(
            UsuarioEmpresa.empresa_id == empresa_id,
            UsuarioEmpresa.papel == "admin",
            UsuarioEmpresa.ativo.is_(True),
            Usuario.ativo.is_(True),
        )
        .order_by(Usuario.nome)
        .limit(1)
    )
    return result.scalar_one_or_none()


def _enviar_email_simples(destinatario: str, assunto: str, html: str) -> None:
    """Envia e-mail HTML simples via SMTP. Ignora silenciosamente se SMTP não estiver configurado."""
    from app.config import get_settings

    cfg = get_settings()
    if not cfg.smtp_host:
        logger.debug("SMTP não configurado; e-mail para '%s' ignorado.", destinatario)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = cfg.smtp_from
    msg["To"] = destinatario
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
            server.starttls()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.sendmail(cfg.smtp_from, [destinatario], msg.as_string())
    except Exception:
        logger.exception("Falha ao enviar e-mail para '%s'.", destinatario)


def _render_template_vencimentos(lancamentos: list[LancamentoReceita]) -> str:
    """Renderiza o HTML do e-mail de vencimentos do dia."""
    from pathlib import Path

    template_path = Path(__file__).parent.parent / "documents" / "templates" / "_email_vencimentos.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        itens_html = "".join(
            f"<tr>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb'>{l.descricao}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right'>"
            f"R$ {l.valor:,.2f}</td>"
            f"</tr>"
            for l in lancamentos
        )
        return template.replace("{{itens}}", itens_html).replace("{{total}}", str(len(lancamentos)))

    # Fallback inline
    itens_html = "".join(
        f"<li style='margin-bottom:4px'><strong>{l.descricao}</strong> — R$ {l.valor:,.2f}</li>"
        for l in lancamentos
    )
    return (
        "<h2 style='color:#111'>Lançamentos vencendo hoje</h2>"
        f"<ul style='padding-left:20px'>{itens_html}</ul>"
        "<p style='color:#666;font-size:13px'>Acesse o iSolutis Hub para marcar como recebidos.</p>"
    )


def _render_template_orcamentos(orcamentos: list[Orcamento]) -> str:
    """Renderiza o HTML do e-mail de orçamentos sem resposta."""
    from pathlib import Path

    template_path = Path(__file__).parent.parent / "documents" / "templates" / "_email_orcamentos.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        itens_html = "".join(
            f"<tr>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb'>{o.numero}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e5e7eb'>"
            f"{(date.today() - o.data).days} dias</td>"
            f"</tr>"
            for o in orcamentos
        )
        return template.replace("{{itens}}", itens_html).replace("{{total}}", str(len(orcamentos)))

    # Fallback inline
    itens_html = "".join(
        f"<li style='margin-bottom:4px'>"
        f"Orçamento <strong>#{o.numero}</strong> — aguardando há {(date.today() - o.data).days} dias"
        f"</li>"
        for o in orcamentos
    )
    return (
        "<h2 style='color:#111'>Orçamentos aguardando resposta</h2>"
        f"<ul style='padding-left:20px'>{itens_html}</ul>"
        "<p style='color:#666;font-size:13px'>Acesse o iSolutis Hub para acompanhar o status.</p>"
    )
