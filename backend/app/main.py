"""Fábrica da aplicação FastAPI."""

from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings
from app.db import engine
from app.deps import requer_base, requer_comercial, requer_financeiro
from app.errors import registrar_tratadores
from app.financeiro import rotas as financeiro
from app.routers import (
    auth,
    clientes,
    despesas,
    equipe,
    faturamento,
    negocios,
    onboarding as router_onboarding,
    orcamentos,
    painel,
    parceiros,
    produtos,
    projetos,
    tarefas,
    ws,
)

try:
    from app.routers import relatorios as router_relatorios

    _relatorios_disponivel = True
except ImportError:
    _relatorios_disponivel = False

try:
    from app.routers import auth_2fa as router_auth_2fa

    _auth_2fa_disponivel = True
except ImportError:
    _auth_2fa_disponivel = False

try:
    from app.scheduler import iniciar_scheduler, parar_scheduler

    _scheduler_disponivel = True
except ImportError:
    _scheduler_disponivel = False

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' ws: wss:; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


class CabecalhosDeSeguranca(BaseHTTPMiddleware):
    """Cabeçalhos defensivos em todas as respostas (a CSP vale para o site; a API só devolve JSON/arquivos)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        resposta = await call_next(request)
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        if not request.url.path.startswith("/api/"):
            resposta.headers.setdefault("Content-Security-Policy", CSP)
        return resposta


def criar_app() -> FastAPI:
    cfg = get_settings()
    cfg.validar_para_producao()
    app = FastAPI(
        title="Hub Comercial iSolutis — API",
        version="2.0.0",
        docs_url="/api/docs" if cfg.ambiente != "producao" else None,
        openapi_url="/api/openapi.json" if cfg.ambiente != "producao" else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "X-Empresa-ID"],
    )
    registrar_tratadores(app)
    app.add_middleware(CabecalhosDeSeguranca)

    api = APIRouter(prefix="/api/v1")
    # Cada um cuida da própria autenticação e permissão: login, equipe (rota a rota) e WebSocket.
    for modulo in (auth, equipe, ws):
        api.include_router(modulo.router)
    # Toda rota de dados declara a permissão exigida pelo papel na empresa ativa (ver app.domain.papeis);
    # tests/test_permissoes.py falha se uma rota nova ficar sem checagem. A dependência também alimenta a auditoria.
    for modulo in (projetos, tarefas, painel):  # `base`: qualquer papel
        api.include_router(modulo.router, dependencies=[Depends(requer_base)])
    api.include_router(clientes.router_referencias)  # `base`: só id e nome
    for modulo in (clientes, produtos, negocios, orcamentos):  # `comercial`
        api.include_router(modulo.router, dependencies=[Depends(requer_comercial)])
    for modulo in (faturamento, despesas):  # `financeiro`
        api.include_router(modulo.router, dependencies=[Depends(requer_financeiro)])
    # Módulo financeiro (`financeiro`) e referências de apoio a formulários (`base`): dependências nos próprios routers.
    api.include_router(financeiro.router)
    api.include_router(financeiro.router_referencias)
    # Hub de parceiros (`financeiro`); os papéis disponíveis qualquer papel consulta (`base`).
    api.include_router(parceiros.router)
    api.include_router(parceiros.router_papeis)
    # Onboarding: configuração inicial da empresa (`administracao`; o status é `base`).
    api.include_router(router_onboarding.router, tags=["onboarding"])
    # Módulos opcionais da Onda 2 (registrados somente quando os arquivos existirem).
    if _relatorios_disponivel:
        api.include_router(router_relatorios.router, tags=["relatorios"])  # type: ignore[possibly-undefined]
    if _auth_2fa_disponivel:
        api.include_router(router_auth_2fa.router, tags=["auth"])  # type: ignore[possibly-undefined]
    app.include_router(api)

    if _scheduler_disponivel:

        @app.on_event("startup")
        async def startup() -> None:
            iniciar_scheduler()  # type: ignore[possibly-undefined]

        @app.on_event("shutdown")
        async def shutdown() -> None:
            parar_scheduler()  # type: ignore[possibly-undefined]

    @app.get("/api/saude", tags=["Infra"])
    async def saude() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/prontidao", tags=["Infra"])
    async def prontidao() -> dict[str, str]:
        async with engine.connect() as conexao:
            await conexao.execute(text("SELECT 1"))
        return {"status": "ok", "banco": "ok"}

    _servir_frontend(app, cfg.frontend_dist)
    return app


def _servir_frontend(app: FastAPI, pasta: str | None) -> None:
    """Deploy em um serviço só: a API também entrega o build do frontend (com fallback para a SPA)."""
    if not pasta or not Path(pasta).is_dir():
        return
    raiz = Path(pasta).resolve()
    app.mount("/assets", StaticFiles(directory=raiz / "assets"), name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    async def spa(caminho: str) -> FileResponse:
        arquivo = (raiz / caminho).resolve()
        if caminho and raiz in arquivo.parents and arquivo.is_file():
            return FileResponse(arquivo)
        return FileResponse(raiz / "index.html", headers={"Cache-Control": "no-cache"})


app = criar_app()
