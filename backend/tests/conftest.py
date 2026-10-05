"""Testes de integração contra um PostgreSQL real (o schema do DBA é aplicado pelo Alembic).

Cada teste roda numa transação externa que é desfeita no fim; os `commit()` dos serviços viram
SAVEPOINTs (join_transaction_mode="create_savepoint"), então os testes são isolados e rápidos.
"""

import os

os.environ.setdefault("HUB_DATABASE_URL", "postgresql+psycopg://hub:hub@localhost:5432/hub_test")
os.environ["HUB_AMBIENTE"] = "teste"
os.environ["HUB_SECRET_KEY"] = "chave-de-testes-com-mais-de-32-caracteres"

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import criar_engine, get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Usuario  # noqa: E402
from app.security import gerar_hash  # noqa: E402

SENHA = "senha-de-teste-123"


@pytest.fixture(scope="session", autouse=True)
def banco_migrado() -> None:
    """Recria o schema do zero com as migrações (testa também o upgrade do Alembic)."""
    url = get_settings().database_url
    sync = create_engine(url, isolation_level="AUTOCOMMIT")
    with sync.connect() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    sync.dispose()
    command.upgrade(Config("alembic.ini"), "head")


@pytest_asyncio.fixture(scope="session")
async def engine():  # noqa: ANN201
    eng = criar_engine()
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessao(engine) -> AsyncIterator[AsyncSession]:  # noqa: ANN001
    async with engine.connect() as conexao:
        externa = await conexao.begin()
        async with AsyncSession(conexao, join_transaction_mode="create_savepoint", expire_on_commit=False) as s:
            yield s
        await externa.rollback()


@pytest_asyncio.fixture
async def admin(sessao: AsyncSession) -> Usuario:
    u = Usuario(email="admin@isolutis.com.br", nome="Ana Admin", admin=True, senha_hash=gerar_hash(SENHA))
    sessao.add(u)
    await sessao.commit()
    return u


@pytest_asyncio.fixture
async def http(sessao: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _sessao() -> AsyncIterator[AsyncSession]:
        yield sessao

    app.dependency_overrides[get_session] = _sessao
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://teste") as cliente:
        yield cliente
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def api(http: AsyncClient, admin: Usuario) -> AsyncClient:
    """Cliente já autenticado como administrador."""
    r = await http.post("/api/v1/auth/login", json={"email": admin.email, "senha": SENHA})
    assert r.status_code == 200, r.text
    http.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    return http


@pytest.fixture
def novo_cliente(api: AsyncClient):  # noqa: ANN201
    async def _criar(nome: str = "Distribuidora Alfa", **extra: object) -> dict:
        r = await api.post("/api/v1/clientes", json={"nome": nome, **extra})
        assert r.status_code == 201, r.text
        return r.json()

    return _criar
