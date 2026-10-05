from httpx import AsyncClient

from tests.conftest import SENHA

API = "/api/v1"


async def test_login_e_eu(http: AsyncClient, admin):
    r = await http.post(f"{API}/auth/login", json={"email": "ADMIN@isolutis.com.br", "senha": SENHA})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["usuario"]["nome"] == "Ana Admin" and "senha_hash" not in corpo["usuario"]
    r = await http.get(f"{API}/auth/eu", headers={"Authorization": f"Bearer {corpo['access_token']}"})
    assert r.json()["admin"] is True


async def test_login_com_senha_errada_nao_revela_se_o_email_existe(http: AsyncClient, admin):
    errada = await http.post(f"{API}/auth/login", json={"email": admin.email, "senha": "x"})
    inexistente = await http.post(f"{API}/auth/login", json={"email": "ninguem@isolutis.com.br", "senha": "x"})
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()


async def test_rotas_exigem_login(http: AsyncClient):
    for caminho in ("/clientes", "/painel", "/equipe", "/usuarios"):
        assert (await http.get(f"{API}{caminho}")).status_code == 401


async def test_token_invalido(http: AsyncClient):
    r = await http.get(f"{API}/clientes", headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401


async def test_trocar_senha(api: AsyncClient):
    r = await api.post(f"{API}/auth/trocar-senha", json={"senha_atual": "errada", "nova_senha": "nova-senha-123"})
    assert r.status_code == 422
    r = await api.post(f"{API}/auth/trocar-senha", json={"senha_atual": SENHA, "nova_senha": "curta"})
    assert r.status_code == 422
    r = await api.post(f"{API}/auth/trocar-senha", json={"senha_atual": SENHA, "nova_senha": "nova-senha-123"})
    assert r.status_code == 204
    r = await api.post(f"{API}/auth/login", json={"email": "admin@isolutis.com.br", "senha": "nova-senha-123"})
    assert r.status_code == 200


async def test_gestao_de_usuarios(api: AsyncClient):
    r = await api.post(
        f"{API}/usuarios", json={"nome": "Bia", "email": "bia@isolutis.com.br", "senha": "senha-da-bia-1"}
    )
    assert r.status_code == 201
    bia = r.json()
    assert (
        await api.post(
            f"{API}/usuarios", json={"nome": "Bia", "email": "BIA@isolutis.com.br", "senha": "outra-senha-1"}
        )
    ).status_code == 422

    # a nova pessoa entra, mas não administra
    login = await api.post(f"{API}/auth/login", json={"email": "bia@isolutis.com.br", "senha": "senha-da-bia-1"})
    token_bia = login.json()["access_token"]
    sem_admin = await api.get(f"{API}/usuarios", headers={"Authorization": f"Bearer {token_bia}"})
    assert sem_admin.status_code == 403
    equipe = await api.get(f"{API}/equipe", headers={"Authorization": f"Bearer {token_bia}"})
    assert {m["nome"] for m in equipe.json()} == {"Ana Admin", "Bia"}

    # trocar senha de outra pessoa e remover (desativa e barra o login)
    r = await api.put(
        f"{API}/usuarios/{bia['id']}",
        json={"nome": "Bia S.", "admin": False, "ativo": True, "senha": "senha-nova-bia-2", "versao": bia["versao"]},
    )
    assert r.status_code == 200 and r.json()["nome"] == "Bia S."
    assert (await api.delete(f"{API}/usuarios/{bia['id']}")).status_code == 204
    r = await api.post(f"{API}/auth/login", json={"email": "bia@isolutis.com.br", "senha": "senha-nova-bia-2"})
    assert r.status_code == 401
    assert (await api.get(f"{API}/clientes", headers={"Authorization": f"Bearer {token_bia}"})).status_code == 401


async def test_admin_nao_remove_nem_rebaixa_a_si_mesmo(api: AsyncClient, admin):
    eu = (await api.get(f"{API}/auth/eu")).json()
    assert (await api.delete(f"{API}/usuarios/{eu['id']}")).status_code == 422
    r = await api.put(
        f"{API}/usuarios/{eu['id']}", json={"nome": "x", "admin": False, "ativo": True, "versao": eu["versao"]}
    )
    assert r.status_code == 422


async def test_login_tem_freio_contra_forca_bruta(http: AsyncClient, admin):
    from app.ratelimit import limitador_de_login

    limitador_de_login._falhas.clear()
    for _ in range(8):
        assert (await http.post(f"{API}/auth/login", json={"email": admin.email, "senha": "errada"})).status_code == 401
    r = await http.post(f"{API}/auth/login", json={"email": admin.email, "senha": SENHA})
    assert r.status_code == 429 and r.json()["erro"]["codigo"] == "muitas_tentativas"
    limitador_de_login._falhas.clear()
    assert (await http.post(f"{API}/auth/login", json={"email": admin.email, "senha": SENHA})).status_code == 200


async def test_cabecalhos_de_seguranca(http: AsyncClient):
    r = await http.get("/api/saude")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
