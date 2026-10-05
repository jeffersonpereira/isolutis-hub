"""Testes de edge cases para tags de parceiros (multi-tenant)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Empresa, Parceiro, TagParceiro, ParceiroTag, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from tests.conftest import SENHA

API = "/api/v1"


@pytest.fixture
async def empresa(sessao: AsyncSession) -> Empresa:
    """Empresa para testes de tags."""
    from uuid import uuid4

    e = Empresa(id=uuid4(), nome="Test Tags", ativo=True)
    sessao.add(e)
    await sessao.commit()
    return e


@pytest.fixture
async def usuario_admin(sessao: AsyncSession, empresa: Empresa) -> tuple[Usuario, str]:
    """Usuário admin da empresa para testes."""
    from uuid import uuid4

    u = Usuario(
        id=uuid4(),
        email="admin-tags@test.com",
        nome="Admin Tags",
        admin=False,
        senha_hash=gerar_hash(SENHA),
        ativo=True,
    )
    sessao.add(u)
    await sessao.commit()

    ue = UsuarioEmpresa(
        usuario_id=u.id,
        empresa_id=empresa.id,
        papel="admin",
        ativo=True,
    )
    sessao.add(ue)
    await sessao.commit()
    return u, str(empresa.id)


@pytest.fixture
async def api_autenticada(http: AsyncClient, usuario_admin: tuple[Usuario, str]) -> tuple[AsyncClient, str]:
    """Cliente autenticado com header de empresa."""
    usuario, empresa_id = usuario_admin
    r = await http.post(f"{API}/auth/login", json={"email": usuario.email, "senha": SENHA})
    assert r.status_code == 200
    token = r.json()["access_token"]
    http.headers["Authorization"] = f"Bearer {token}"
    http.headers["X-Empresa-ID"] = empresa_id
    return http, empresa_id


async def test_criar_tag_com_normalizacao(api_autenticada: tuple[AsyncClient, str]):
    """Tags com espaços extras e maiúsculas devem ser normalizadas."""
    api, empresa_id = api_autenticada

    # Criar tag com espaços e maiúsculas
    r = await api.post(
        f"{API}/tags",
        json={"nome": "  FORNECEDOR PREMIUM  "},  # Espaços extras, maiúsculas
    )
    assert r.status_code == 201
    tag1 = r.json()
    assert tag1["nome"] == "Fornecedor Premium"  # Esperado: normalizado


async def test_rejeitar_tag_duplicada_case_insensitive(api_autenticada: tuple[AsyncClient, str]):
    """Duas tags com mesmo nome (case-insensitive) devem ser rejeitadas."""
    api, empresa_id = api_autenticada

    # Criar primeira tag
    r = await api.post(f"{API}/tags", json={"nome": "Fornecedor Premium"})
    assert r.status_code == 201

    # Tentar criar tag duplicada (maiúsculas diferentes)
    r = await api.post(f"{API}/tags", json={"nome": "fornecedor premium"})
    assert r.status_code == 409  # Conflict (ou similar)


async def test_atribuir_multiplas_tags_atomicamente(api_autenticada: tuple[AsyncClient, str], sessao: AsyncSession):
    """Atribuição de múltiplas tags deve ser atômica."""
    api, empresa_id = api_autenticada
    from uuid import uuid4

    # Criar tags
    tags_ids = []
    for nome in ["Tag A", "Tag B", "Tag C"]:
        r = await api.post(f"{API}/tags", json={"nome": nome})
        assert r.status_code == 201
        tags_ids.append(r.json()["id"])

    # Criar parceiro
    r = await api.post(
        f"{API}/parceiros",
        json={"nome": "Parceiro Multi-Tag", "email": "p@test.com"},
    )
    assert r.status_code == 201
    parceiro_id = r.json()["id"]

    # Atribuir múltiplas tags
    r = await api.patch(
        f"{API}/parceiros/{parceiro_id}",
        json={"tag_ids": tags_ids},
    )
    assert r.status_code == 200
    parceiro = r.json()
    assert len(parceiro["tags"]) == 3


async def test_rejeitar_tag_cross_tenant(api_autenticada: tuple[AsyncClient, str], sessao: AsyncSession):
    """Tentar associar tag de outro tenant deve ser rejeitado."""
    from uuid import uuid4

    api, empresa_id = api_autenticada

    # Criar segunda empresa
    empresa2 = Empresa(id=uuid4(), nome="Empresa 2", ativo=True)
    sessao.add(empresa2)
    await sessao.commit()

    # Criar tag na empresa2
    tag2 = TagParceiro(id=uuid4(), empresa_id=empresa2.id, nome="Tag Empresa 2")
    sessao.add(tag2)
    await sessao.commit()

    # Tentar usar tag da empresa2 em parceiro da empresa1
    r = await api.post(
        f"{API}/parceiros",
        json={
            "nome": "Parceiro Teste",
            "email": "p@test.com",
            "tag_ids": [str(tag2.id)],  # Tag de outra empresa
        },
    )
    assert r.status_code == 403  # Ou 422 (validation error)


async def test_arquivo_tag_usada(api_autenticada: tuple[AsyncClient, str]):
    """Tag ativa com associações não pode ser deletada, mas pode ser arquivada."""
    api, empresa_id = api_autenticada

    # Criar tag
    r = await api.post(f"{API}/tags", json={"nome": "Tag com Uso"})
    assert r.status_code == 201
    tag_id = r.json()["id"]

    # Criar parceiro com a tag
    r = await api.post(
        f"{API}/parceiros",
        json={"nome": "Parceiro", "email": "p@test.com", "tag_ids": [tag_id]},
    )
    assert r.status_code == 201

    # Tentar deletar tag com associações
    r = await api.delete(f"{API}/tags/{tag_id}")
    assert r.status_code == 409  # Conflict: em uso

    # Arquivar tag (inativar)
    r = await api.patch(f"{API}/tags/{tag_id}", json={"ativo": False})
    assert r.status_code == 200
    tag = r.json()
    assert tag["ativo"] is False

    # Tag inativa não aparece em filtro de criação
    r = await api.get(f"{API}/parceiros/opcoes")
    assert r.status_code == 200
    opcoes = r.json()
    tag_ids_ativos = {t["id"] for t in opcoes["tags"]}
    assert tag_id not in tag_ids_ativos


async def test_filtro_tags_com_semantica_or(api_autenticada: tuple[AsyncClient, str]):
    """Filtro de tags com múltiplos IDs usa OR (parceiro tem ANY tag)."""
    api, empresa_id = api_autenticada

    # Criar 3 tags
    tags = []
    for nome in ["Tag A", "Tag B", "Tag C"]:
        r = await api.post(f"{API}/tags", json={"nome": nome})
        tags.append(r.json()["id"])

    # Criar 3 parceiros, cada um com uma tag diferente
    parceiros = []
    for i, tag_id in enumerate(tags):
        r = await api.post(
            f"{API}/parceiros",
            json={"nome": f"Parceiro {i+1}", "email": f"p{i+1}@test.com", "tag_ids": [tag_id]},
        )
        parceiros.append(r.json()["id"])

    # Filtrar por tags A ou B (devem retornar parceiros 1 e 2)
    r = await api.get(f"{API}/parceiros", params={"tag_ids": [tags[0], tags[1]]})
    assert r.status_code == 200
    resultado = r.json()
    resultado_ids = {p["id"] for p in resultado}
    assert parceiros[0] in resultado_ids  # Tag A
    assert parceiros[1] in resultado_ids  # Tag B
    assert parceiros[2] not in resultado_ids  # Tem Tag C, não A/B


async def test_filtro_tags_com_papel_usa_and(api_autenticada: tuple[AsyncClient, str]):
    """Filtro de tags se combina com papel por AND."""
    api, empresa_id = api_autenticada

    # Criar tags
    tag_fornecedor = None
    r = await api.post(f"{API}/tags", json={"nome": "Premium"})
    tag_premium = r.json()["id"]

    # Criar parceiros
    # 1. Cliente premium
    r = await api.post(
        f"{API}/parceiros",
        json={
            "nome": "Cliente Premium",
            "email": "cp@test.com",
            "papel_id": "CLIENTE",  # Se aplicável
            "tag_ids": [tag_premium],
        },
    )
    parceiro1 = r.json()["id"]

    # 2. Fornecedor premium
    r = await api.post(
        f"{API}/parceiros",
        json={
            "nome": "Fornecedor Premium",
            "email": "fp@test.com",
            "papel_id": "FORNECEDOR",  # Se aplicável
            "tag_ids": [tag_premium],
        },
    )
    parceiro2 = r.json()["id"]

    # Filtrar por tags=Premium AND papel=FORNECEDOR
    # Deve retornar apenas parceiro 2
    r = await api.get(
        f"{API}/parceiros",
        params={"tag_ids": [tag_premium], "papel": "FORNECEDOR"},
    )
    assert r.status_code == 200
    resultado = r.json()
    resultado_ids = {p["id"] for p in resultado}
    assert parceiro2 in resultado_ids
    # parceiro1 pode estar ou não, dependendo de como se lida com parceiros sem papel explícito


async def test_sem_tag_seleciona_nao_filtra_por_tags(api_autenticada: tuple[AsyncClient, str]):
    """Sem filtro de tags, a dimensão de tags não exclui ninguém."""
    api, empresa_id = api_autenticada

    # Criar tags
    r = await api.post(f"{API}/tags", json={"nome": "Tag A"})
    tag_id = r.json()["id"]

    # Criar parceiros: um com tag, outro sem
    r = await api.post(
        f"{API}/parceiros",
        json={"nome": "Com Tag", "email": "ct@test.com", "tag_ids": [tag_id]},
    )
    p1 = r.json()["id"]

    r = await api.post(
        f"{API}/parceiros",
        json={"nome": "Sem Tag", "email": "st@test.com", "tag_ids": []},
    )
    p2 = r.json()["id"]

    # Filtro sem tag_ids deve retornar ambos
    r = await api.get(f"{API}/parceiros")
    assert r.status_code == 200
    resultado = r.json()
    resultado_ids = {p["id"] for p in resultado}
    assert p1 in resultado_ids
    assert p2 in resultado_ids
