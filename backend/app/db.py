"""Engine, sessão assíncrona e ganchos de transação.

Contrato de auditoria com o banco: antes de gravar, a requisição executa
`select set_config('app.usuario_id', '<uuid>', true)` (local à transação); o trigger `set_audit`
preenche criado_por/atualizado_por/versao a partir dele.
"""

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import Connection, event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ErroApp
from app.realtime import agendar_publicacao

# Tabela -> recurso que a interface precisa recarregar quando a tabela muda.
RECURSO_DA_TABELA = {
    "parceiro_negocio": ("clientes", "financeiro", "negocios"),
    "parceiro_papel": ("clientes", "financeiro"),
    "produtos": "produtos",
    "negocios": "negocios",
    "orcamentos": "orcamentos",
    "orcamento_itens": "orcamentos",
    "lancamentos_receita": "faturamento",
    "projetos": "projetos",
    "projeto_etapas": "projetos",
    "tarefas": "tarefas",
    "tarefa_checklist": "tarefas",
    "usuarios": "equipe",
    "empresa": "empresa",  # cadastro, logomarca e paleta: as outras abas reaplicam a identidade visual
    # equipes mudam o que cada um enxerga: as abas recarregam tudo (escopo de acesso)
    "equipe": "escopo",
    "equipe_membro": "escopo",
    "equipe_lider": "escopo",
    "projeto_participante": ("projetos", "tarefas"),
    # módulo financeiro (tudo o que ele grava avisa a tela "financeiro")
    "plano_contas": "financeiro",
    "conta_bancaria": "financeiro",
    "titulo_financeiro": "financeiro",
    "recorrencia_titulo": "financeiro",
    "parceiro_socio": ("clientes", "financeiro"),
}


def criar_engine(url: str | None = None) -> AsyncEngine:
    cfg = get_settings()
    # Fuso do negócio: "hoje" e vencimentos calculados pelo banco seguem o horário de Brasília.
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


_sessao_plataforma: async_sessionmaker[AsyncSession] | None = None


async def get_session_plataforma() -> AsyncIterator[AsyncSession | None]:
    """Sessão do papel hub_plataforma (sem acesso às tabelas de negócio); None quando a credencial não está configurada."""
    global _sessao_plataforma
    url = get_settings().plataforma_database_url
    if not url:
        yield None
        return
    if _sessao_plataforma is None:
        _sessao_plataforma = async_sessionmaker(criar_engine(url), expire_on_commit=False)
    async with _sessao_plataforma() as sessao:
        yield sessao


def plataforma_indisponivel() -> ErroApp:
    return ErroApp("A área da plataforma não está configurada neste ambiente.", codigo="plataforma_indisponivel", status=503)


async def definir_usuario_da_transacao(sessao: AsyncSession, usuario_id: UUID) -> None:
    sessao.info["usuario_id"] = usuario_id
    await sessao.execute(text("select set_config('app.usuario_id', :u, true)"), {"u": str(usuario_id)})


async def definir_empresa_da_transacao(sessao: AsyncSession, empresa_id: UUID) -> None:
    sessao.info["empresa_id"] = empresa_id
    await sessao.execute(text("select set_config('app.empresa_id', :e, true)"), {"e": str(empresa_id)})


async def definir_escopo_da_transacao(sessao: AsyncSession) -> None:
    """Calcula no banco quem a pessoa enxerga (ela + liderados; admin vê tudo). Ver migração 0015."""
    sessao.info["escopo"] = True
    await sessao.execute(text("select app_definir_escopo()"))


async def definir_empresa_e_escopo_da_transacao(sessao: AsyncSession, empresa_id: UUID) -> None:
    """Empresa ativa e escopo de visibilidade da transação, numa só ida ao banco."""
    sessao.info["empresa_id"] = empresa_id
    sessao.info["escopo"] = True
    await sessao.execute(
        text("select app_iniciar_contexto(cast(:u as uuid), cast(:e as uuid), true)"),
        {"u": str(sessao.info["usuario_id"]) if sessao.info.get("usuario_id") else None, "e": str(empresa_id)},
    )


@event.listens_for(Session, "after_begin")
def _reaplicar_contexto(sessao: Session, _transacao: object, conexao: Connection) -> None:
    """As variáveis da requisição são locais à transação: cada nova transação da sessão (ex.: leitura depois de
    um commit) recebe de novo usuário, empresa e escopo; sem isso o RLS esconderia tudo."""
    usuario, empresa = sessao.info.get("usuario_id"), sessao.info.get("empresa_id")
    if usuario or empresa:  # uma só ida ao banco para usuário, empresa e escopo (migração 0014)
        conexao.execute(
            text("select app_iniciar_contexto(cast(:u as uuid), cast(:e as uuid), :s)"),
            {"u": str(usuario) if usuario else None, "e": str(empresa) if empresa else None, "s": bool(sessao.info.get("escopo"))},
        )


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
