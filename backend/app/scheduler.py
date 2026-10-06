"""Scheduler de background para jobs periódicos (APScheduler).

Uso esperado em main.py:
    from app.scheduler import iniciar_scheduler, parar_scheduler
    app.add_event_handler("startup", iniciar_scheduler)
    app.add_event_handler("shutdown", parar_scheduler)
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")


def _executar_job_notificacoes() -> None:
    """Wrapper síncrono que executa os jobs assíncronos de notificação."""
    try:
        from app.db import SessionLocal
        from app.services.notificacoes import enviar_alertas_orcamentos, enviar_alertas_vencimentos

        async def _run() -> None:
            async with SessionLocal() as db:
                await enviar_alertas_vencimentos(db)
                await enviar_alertas_orcamentos(db)

        asyncio.run(_run())
    except Exception:
        logger.exception("Erro no job de notificações.")


def iniciar_scheduler() -> None:
    """Registra e inicia o scheduler. Chamado no evento startup da aplicação."""
    _scheduler.add_job(
        _executar_job_notificacoes,
        trigger="interval",
        hours=1,
        id="notificacoes",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler de notificações iniciado (intervalo: 1 hora).")


def parar_scheduler() -> None:
    """Para o scheduler graciosamente. Chamado no evento shutdown da aplicação."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler de notificações parado.")
