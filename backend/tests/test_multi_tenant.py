"""Testes de isolamento e segurança multi-tenant."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Empresa, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from tests.conftest import SENHA

API = "/api/v1"


@pytest.fixture
async def empresa1(sessao: AsyncSession) -> Empresa:
    """Primeira empresa para testes (iSolutis)."""
    e = Empresa(id=uuid4(), nome="iSolutis", ativo=True)
    sessao.add(e)
    await sessao.commit()
    return e


@pytest.fixture
async def empresa2(sessao: AsyncSession) -> Empresa:
    """Segunda empresa para testes (outra organização)."""
    e = Empresa(id=uuid4(), nome="Acme Corp", ativo=True)
    sessao.add(e)
    await sessao.commit()
    return e


@pytest.fixture
async def usuario1(sessao: AsyncSession, empresa1: Empresa) -> Usuario:
    """Usuário membro da empresa1."""
    u = Usuario(
        email="usuario1@test.com",
        nome="Usuário Um",
        admin=False,
        senha_hash=gerar_hash(SENHA),
        ativo=True,
    )
    sessao.add(u)
    await sessao.commit()

    # Adicionar a empresa1
    ue = UsuarioEmpresa(
        usuario_id=u.id,
        empresa_id=empresa1.id,
        papel="membro",
        ativo=True,
    )
    sessao.add(ue)
    await sessao.commit()
    return u


@pytest.fixture
async def usuario2(sessao: AsyncSession, empresa2: Empresa) -> Usuario:
    """Usuário membro da empresa2."""
    u = Usuario(
        email="usuario2@test.com",
        nome="Usuário Dois",
        admin=False,
        senha_hash=gerar_hash(SENHA),
        ativo=True,
    )
    sessao.add(u)
    await sessao.commit()

    # Adicionar a empresa2
    ue = UsuarioEmpresa(
        usuario_id=u.id,
        empresa_id=empresa2.id,
        papel="membro",
        ativo=True,
    )
    sessao.add(ue)
    await sessao.commit()
    return u


async def test_sem_header_empresa_retorna_erro(http: AsyncClient, usuario1: Usuario):
    """Requisição autenticada sem X-Empresa-ID deve ser rejeitada."""
    # Login
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Tentar acessar rota sem header X-Empresa-ID
    r = await http.get(
        f"{API}/parceiros",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403  # SemPermissao
    assert "X-Empresa-ID" in r.json()["detail"]


async def test_com_empresa_invalida_retorna_erro(http: AsyncClient, usuario1: Usuario):
    """Requisição com X-Empresa-ID que não pertence ao usuário deve ser rejeitada."""
    # Login
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Tentar acessar com ID de empresa inexistente
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Empresa-ID": str(uuid4()),
        },
    )
    assert r.status_code == 403  # SemPermissao
    assert "não tem acesso ativo" in r.json()["detail"]


async def test_usuario1_so_ve_seus_dados(
    http: AsyncClient,
    usuario1: Usuario,
    usuario2: Usuario,
    empresa1: Empresa,
    empresa2: Empresa,
):
    """Usuário1 só deve ver dados da empresa1, não da empresa2."""
    # Login usuario1
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    token1 = r.json()["access_token"]

    # Acessar parceiros da empresa1
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token1}",
            "X-Empresa-ID": str(empresa1.id),
        },
    )
    assert r.status_code == 200
    dados1 = r.json()
    assert isinstance(dados1, list)  # Esperado ser lista


async def test_usuario2_so_ve_seus_dados(
    http: AsyncClient,
    usuario1: Usuario,
    usuario2: Usuario,
    empresa1: Empresa,
    empresa2: Empresa,
):
    """Usuário2 só deve ver dados da empresa2, não da empresa1."""
    # Login usuario2
    r = await http.post(f"{API}/auth/login", json={"email": usuario2.email, "senha": SENHA})
    assert r.status_code == 200
    token2 = r.json()["access_token"]

    # Tentar acessar parceiros da empresa1 (não deve ter acesso)
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token2}",
            "X-Empresa-ID": str(empresa1.id),
        },
    )
    assert r.status_code == 403  # SemPermissao


async def test_alternancia_de_empresa_na_mesma_conexao(
    http: AsyncClient,
    usuario1: Usuario,
    sessao: AsyncSession,
    empresa1: Empresa,
    empresa2: Empresa,
):
    """Usuário com múltiplas empresas pode alternar entre elas."""
    # Adicionar usuario1 também a empresa2
    ue = UsuarioEmpresa(
        usuario_id=usuario1.id,
        empresa_id=empresa2.id,
        papel="membro",
        ativo=True,
    )
    sessao.add(ue)
    await sessao.commit()

    # Login
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Acessar empresa1
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Empresa-ID": str(empresa1.id),
        },
    )
    assert r.status_code == 200

    # Na mesma conexão, acessar empresa2
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Empresa-ID": str(empresa2.id),
        },
    )
    assert r.status_code == 200


async def test_listagem_empresas_do_usuario(
    http: AsyncClient,
    usuario1: Usuario,
    sessao: AsyncSession,
    empresa1: Empresa,
    empresa2: Empresa,
):
    """Usuário só vê empresas às quais está vinculado."""
    # Adicionar usuario1 também a empresa2
    ue = UsuarioEmpresa(
        usuario_id=usuario1.id,
        empresa_id=empresa2.id,
        papel="membro",
        ativo=True,
    )
    sessao.add(ue)
    await sessao.commit()

    # Login
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    corpo = r.json()
    token = corpo["access_token"]

    # Acessar /auth/empresas para listar suas empresas
    r = await http.get(
        f"{API}/auth/empresas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    empresas = r.json()
    assert len(empresas) == 2
    ids = {e["id"] for e in empresas}
    assert empresa1.id in ids
    assert empresa2.id in ids


async def test_inativacao_remove_acesso(
    http: AsyncClient,
    usuario1: Usuario,
    sessao: AsyncSession,
    empresa1: Empresa,
):
    """Desativar membership deve remover acesso."""
    # Login
    r = await http.post(f"{API}/auth/login", json={"email": usuario1.email, "senha": SENHA})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Acessar com sucesso
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Empresa-ID": str(empresa1.id),
        },
    )
    assert r.status_code == 200

    # Desativar membership
    ue = (
        await sessao.query(UsuarioEmpresa)
        .where(UsuarioEmpresa.usuario_id == usuario1.id, UsuarioEmpresa.empresa_id == empresa1.id)
        .first()
    )
    if ue:
        ue.ativo = False
        await sessao.commit()

    # Tentar acessar novamente deve falhar
    r = await http.get(
        f"{API}/parceiros",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Empresa-ID": str(empresa1.id),
        },
    )
    assert r.status_code == 403  # SemPermissao
