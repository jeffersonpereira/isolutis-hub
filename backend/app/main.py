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
from app.deps import empresa_atual, usuario_atual
from app.errors import registrar_tratadores
from app.financeiro import rotas as financeiro
from app.routers import (
    auth,
    clientes,
    despesas,
    equipe,
    faturamento,
    negocios,
    orcamentos,
    painel,
    parceiros,
    produtos,
    projetos,
    tarefas,
    ws,
)

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
    # Públicos (cada um cuida da própria autenticação): login, equipe e WebSocket.
    for modulo in (auth, equipe, ws):
        api.include_router(modulo.router)
    # Todo o restante exige login; o usuário autenticado também alimenta a auditoria no banco.
    protegidos = (clientes, produtos, negocios, orcamentos, faturamento, despesas, projetos, tarefas, painel)
    for modulo in protegidos:
        api.include_router(modulo.router, dependencies=[Depends(empresa_atual)])
    # Módulo financeiro: exige administrador (a dependência já está no próprio router).
    api.include_router(financeiro.router)
    api.include_router(financeiro.router_referencias)
    # Hub de parceiros: lista/edita todos os papéis (administradores); os papéis disponíveis qualquer logado consulta.
    api.include_router(parceiros.router, dependencies=[Depends(empresa_atual)])
    api.include_router(parceiros.router_papeis, dependencies=[Depends(empresa_atual)])
    app.include_router(api)

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
