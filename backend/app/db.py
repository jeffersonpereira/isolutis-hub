"""Engine, sessão assíncrona e ganchos de transação.

Contrato de auditoria com o banco: antes de gravar, a requisição executa
`select set_config('app.usuario_id', '<uuid>', true)` (local à transação); o trigger `set_audit`
preenche criado_por/atualizado_por/versao a partir dele.
"""

import os
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.realtime import agendar_publicacao

# Tabela -> recurso que a interface precisa recarregar quando a tabela muda.
RECURSO_DA_TABELA = {
    "parceiro_negocio": ("clientes", "financeiro"),
    "parceiro_papel": ("clientes", "financeiro"),
    "produtos": "produtos",
    "negocios": "negocios",
    "orcamentos": "orcamentos",
    "orcamento_itens": "orcamentos",
    "lancamentos_receita": "faturamento",
    "despesas": "despesas",
    "investimentos": "despesas",
    "categorias_despesa": "despesas",
    "investidores": "despesas",
    "projetos": "projetos",
    "projeto_etapas": "projetos",
    "tarefas": "tarefas",
    "tarefa_checklist": "tarefas",
    "usuarios": "equipe",
    # módulo financeiro (tudo o que ele grava avisa a tela "financeiro")
    "plano_contas": "financeiro",
    "conta_bancaria": "financeiro",
    "titulo_financeiro": "financeiro",
}


def criar_engine(url: str | None = None) -> AsyncEngine:
    cfg = get_settings()
    # Fuso do negócio: "hoje" e vencimentos calculados pelo banco seguem o horário de Brasília.
    if os.getenv("VERCEL") == "1":
        return create_async_engine(
            url or cfg.database_url,
            echo=cfg.sql_echo,
            poolclass=NullPool,
            connect_args={"options": "-c timezone=America/Sao_Paulo"},
        )
    return create_async_engine(
        url or cfg.database_url,
        echo=cfg.sql_echo,
        pool_pre_ping=True,
        connect_args={"options": "-c timezone=America/Sao_Paulo"},
    )


engine = criar_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as sessao:
        yield sessao


async def definir_usuario_da_transacao(sessao: AsyncSession, usuario_id: UUID) -> None:
    await sessao.execute(text("select set_config('app.usuario_id', :u, true)"), {"u": str(usuario_id)})


async def definir_empresa_da_transacao(sessao: AsyncSession, empresa_id: UUID) -> None:
    await sessao.execute(text("select set_config('app.empresa_id', :e, true)"), {"e": str(empresa_id)})


# --- Tempo real: avisa os clientes conectados depois que a transação é confirmada --------------------
_CHAVE = "recursos_alterados"


@event.listens_for(Session, "after_flush")
def _coletar_recursos(sessao: Session, _contexto: object) -> None:
    alterados: set[str] = sessao.info.setdefault(_CHAVE, set())
    for obj in (*sessao.new, *sessao.dirty, *sessao.deleted):
        recurso = RECURSO_DA_TABELA.get(getattr(obj, "__tablename__", ""))
        if recurso:
            alterados.update((recurso,) if isinstance(recurso, str) else recurso)


@event.listens_for(Session, "after_commit")
def _publicar(sessao: Session) -> None:
    alterados = sessao.info.pop(_CHAVE, None)
    if alterados:
        agendar_publicacao(alterados, sessao.info.get("empresa_id"))


@event.listens_for(Session, "after_rollback")
def _descartar(sessao: Session) -> None:
    sessao.info.pop(_CHAVE, None)
