"""Área da plataforma: operador cria empresa e gerencia membros, sem acesso a dados de negócio.

As rotas usam o papel hub_plataforma em produção; aqui a sessão de teste (uma só, com rollback) faz o papel dela, e os
testes de privilégio trocam de papel com SET ROLE para provar o que o banco recusa.
"""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_plataforma
from app.main import app
from app.models import Empresa, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from tests.conftest import SENHA

P = "/api/v1/plataforma"


@pytest_asyncio.fixture
async def plataforma(http: AsyncClient, sessao: AsyncSession) -> AsyncClient:
    async def _sessao() -> AsyncIterator[AsyncSession]:
        yield sessao

    app.dependency_overrides[get_session_plataforma] = _sessao
    return http


@pytest_asyncio.fixture
async def operador(sessao: AsyncSession) -> Usuario:
    u = Usuario(email="operador@aimetech.com.br", nome="Olga Operadora", senha_hash=gerar_hash(SENHA))
    sessao.add(u)
    await sessao.flush()
    await sessao.execute(text("insert into operador_plataforma (usuario_id) values (:u)"), {"u": u.id})
    await sessao.commit()
    return u


async def entrar(cliente: AsyncClient, usuario: Usuario, empresa_id: object = None) -> None:
    r = await cliente.post("/api/v1/auth/login", json={"email": usuario.email, "senha": SENHA})
    assert r.status_code == 200, r.text
    cliente.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    cliente.headers.pop("X-Empresa-ID", None)
    if empresa_id:
        cliente.headers["X-Empresa-ID"] = str(empresa_id)


async def nova_empresa(cliente: AsyncClient, nome: str = "Cliente Beta", email: str = "dona@beta.com.br", **extra: object) -> dict:
    r = await cliente.post(f"{P}/empresas", json={"nome": nome, "admin_nome": "Dona Beta", "admin_email": email, **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def convite_pendente(sessao: AsyncSession, email: str) -> dict:
    linha = (await sessao.execute(text("select token, papel, empresa_id from convites where email = :e and usado_em is null"), {"e": email})).one()
    return {"token": str(linha.token), "papel": linha.papel, "empresa_id": linha.empresa_id}


# ----------------------------------------------------------------------------- acesso restrito ao operador
async def test_admin_de_empresa_nao_acessa_a_area(plataforma: AsyncClient, api: AsyncClient):
    assert (await api.get(f"{P}/acesso")).json() == {"operador": False}
    assert (await api.get(f"{P}/empresas")).status_code == 403
    r = await api.post(f"{P}/empresas", json={"nome": "X", "admin_nome": "Y", "admin_email": "y@x.com"})
    assert r.status_code == 403


async def test_operador_acessa(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    assert (await plataforma.get(f"{P}/acesso")).json() == {"operador": True}
    nomes = [e["nome"] for e in (await plataforma.get(f"{P}/empresas")).json()]
    assert "iSolutis" in nomes


async def test_sem_login_e_401(plataforma: AsyncClient):
    assert (await plataforma.get(f"{P}/empresas")).status_code == 401


# ----------------------------------------------------------------------------- criar empresa
async def test_criar_empresa_emite_convite_de_admin(plataforma: AsyncClient, operador: Usuario, sessao: AsyncSession):
    await entrar(plataforma, operador)
    empresa = await nova_empresa(plataforma, inscricao="12.345.678/0001-95")
    assert empresa["status"] == "ativa" and empresa["membros_ativos"] == 0 and empresa["inscricao"] == "12345678000195"
    convite = await convite_pendente(sessao, "dona@beta.com.br")
    assert convite["papel"] == "admin" and str(convite["empresa_id"]) == empresa["id"]
    auditoria = (await sessao.execute(text("select acao, operador_id from auditoria_plataforma where empresa_id = :e"), {"e": empresa["id"]})).all()
    assert [(a.acao, a.operador_id) for a in auditoria] == [("empresa_criada", operador.id)]


async def test_administrador_aceita_o_convite_e_entra(plataforma: AsyncClient, operador: Usuario, sessao: AsyncSession):
    await entrar(plataforma, operador)
    empresa = await nova_empresa(plataforma)
    token = (await convite_pendente(sessao, "dona@beta.com.br"))["token"]
    plataforma.headers.pop("Authorization")
    r = await plataforma.post(f"/api/v1/auth/convite/{token}/aceitar", json={"senha": SENHA, "confirmar_senha": SENHA})
    assert r.status_code == 200, r.text
    plataforma.headers["Authorization"] = f"Bearer {r.json()['access_token']}"
    empresas = (await plataforma.get("/api/v1/empresas")).json()
    assert [(e["id"], e["papel"]) for e in empresas] == [(empresa["id"], "admin")]


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "  ", "admin_nome": "A", "admin_email": "a@b.com"},
        {"nome": "X", "admin_nome": "A", "admin_email": "nao-e-email"},
        {"nome": "X", "admin_nome": "A", "admin_email": "a@b.com", "inscricao": "123"},
    ],
)
async def test_dados_invalidos_nao_criam_empresa(plataforma: AsyncClient, operador: Usuario, sessao: AsyncSession, corpo: dict):
    await entrar(plataforma, operador)
    antes = await sessao.scalar(text("select count(*) from empresa"))
    assert (await plataforma.post(f"{P}/empresas", json=corpo)).status_code in (422,)
    assert await sessao.scalar(text("select count(*) from empresa")) == antes


async def test_cnpj_duplicado_e_recusado(plataforma: AsyncClient, operador: Usuario):
    await entrar(plataforma, operador)
    await nova_empresa(plataforma, inscricao="12345678000195")
    r = await plataforma.post(f"{P}/empresas", json={"nome": "Outra", "admin_nome": "A", "admin_email": "a@b.com", "inscricao": "12345678000195"})
    assert r.status_code == 422 and "CNPJ" in r.json()["erro"]["mensagem"]


async def test_busca_por_nome_e_cnpj(plataforma: AsyncClient, operador: Usuario):
    await entrar(plataforma, operador)
    await nova_empresa(plataforma, nome="Padaria Estrela", inscricao="12345678000195")
    await nova_empresa(plataforma, nome="Oficina Lua", email="lua@x.com", inscricao="98765432000110")
    por_nome = (await plataforma.get(f"{P}/empresas", params={"busca": "estrela"})).json()
    por_cnpj = (await plataforma.get(f"{P}/empresas", params={"busca": "98.765.432/0001-10"})).json()
    assert [e["nome"] for e in por_nome] == ["Padaria Estrela"]
    assert [e["nome"] for e in por_cnpj] == ["Oficina Lua"]


# ----------------------------------------------------------------------------- suspender e reativar
async def test_suspender_bloqueia_membros_e_reativar_libera(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    r = await plataforma.patch(f"{P}/empresas/{admin.empresa_id}/status", json={"status": "suspensa"})
    assert r.status_code == 200 and r.json()["status"] == "suspensa"

    await entrar(plataforma, admin, admin.empresa_id)
    r = await plataforma.get("/api/v1/equipe")
    assert r.status_code == 403 and r.json()["erro"]["codigo"] == "empresa_inacessivel"
    assert (await plataforma.get("/api/v1/empresas")).json() == []

    await entrar(plataforma, operador)
    await plataforma.patch(f"{P}/empresas/{admin.empresa_id}/status", json={"status": "ativa"})
    await entrar(plataforma, admin, admin.empresa_id)
    assert (await plataforma.get("/api/v1/equipe")).status_code == 200
    assert len((await plataforma.get("/api/v1/empresas")).json()) == 1


async def test_admin_da_empresa_nao_reativa_a_propria_empresa(plataforma: AsyncClient, operador: Usuario, admin: Usuario, sessao: AsyncSession):
    await entrar(plataforma, operador)
    await plataforma.patch(f"{P}/empresas/{admin.empresa_id}/status", json={"status": "suspensa"})
    await sessao.execute(text("select set_config('app.usuario_id', :u, true), set_config('app.empresa_id', :e, true)"),
                         {"u": str(admin.id), "e": str(admin.empresa_id)})
    await sessao.execute(text("set role hub_runtime"))
    with pytest.raises(DBAPIError, match="area da plataforma"):
        await sessao.execute(text("update empresa set status = 'ativa' where id = :e"), {"e": admin.empresa_id})
    await sessao.rollback()


# ----------------------------------------------------------------------------- membros
async def test_detalhe_traz_membros_e_convites(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    r = await plataforma.post(f"{P}/empresas/{admin.empresa_id}/convites", json={"nome": "Caio", "email": "caio@x.com", "papel": "financeiro"})
    assert r.status_code == 204
    d = (await plataforma.get(f"{P}/empresas/{admin.empresa_id}")).json()
    assert [(m["email"], m["papel"], m["ativo"]) for m in d["membros"]] == [("admin@isolutis.com.br", "admin", True)]
    assert [(c["email"], c["papel"]) for c in d["convites"]] == [("caio@x.com", "financeiro")]
    assert set(d) == {"empresa", "membros", "convites"}


async def test_reenviar_convite_substitui_o_anterior(plataforma: AsyncClient, operador: Usuario, admin: Usuario, sessao: AsyncSession):
    await entrar(plataforma, operador)
    corpo = {"nome": "Caio", "email": "caio@x.com", "papel": "membro"}
    await plataforma.post(f"{P}/empresas/{admin.empresa_id}/convites", json=corpo)
    await plataforma.post(f"{P}/empresas/{admin.empresa_id}/convites", json={**corpo, "papel": "comercial"})
    assert (await sessao.scalar(text("select count(*) from convites where email = 'caio@x.com'"))) == 1
    assert (await convite_pendente(sessao, "caio@x.com"))["papel"] == "comercial"


async def test_convidar_quem_ja_e_membro_e_recusado(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    r = await plataforma.post(f"{P}/empresas/{admin.empresa_id}/convites", json={"nome": "Ana", "email": admin.email, "papel": "membro"})
    assert r.status_code == 422 and "já é membro" in r.json()["erro"]["mensagem"]


async def test_trocar_papel_e_desativar_valem_na_proxima_requisicao(plataforma: AsyncClient, operador: Usuario, admin: Usuario, sessao: AsyncSession):
    outro = Usuario(email="bia@isolutis.com.br", nome="Bia", senha_hash=gerar_hash(SENHA))
    sessao.add(outro)
    await sessao.flush()
    sessao.add(UsuarioEmpresa(empresa_id=admin.empresa_id, usuario_id=outro.id, papel="admin", ativo=True))
    await sessao.commit()
    await entrar(plataforma, operador)
    url = f"{P}/empresas/{admin.empresa_id}/membros/{outro.id}"
    assert (await plataforma.patch(url, json={"papel": "membro", "ativo": True})).status_code == 204
    await entrar(plataforma, outro, admin.empresa_id)
    assert (await plataforma.get("/api/v1/usuarios")).status_code == 403  # deixou de ser admin
    await entrar(plataforma, operador)
    assert (await plataforma.patch(url, json={"papel": "membro", "ativo": False})).status_code == 204
    await entrar(plataforma, outro, admin.empresa_id)
    assert (await plataforma.get("/api/v1/equipe")).status_code == 403


async def test_ultimo_administrador_nao_sai(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    url = f"{P}/empresas/{admin.empresa_id}/membros/{admin.id}"
    for corpo in ({"papel": "membro", "ativo": True}, {"papel": "admin", "ativo": False}):
        r = await plataforma.patch(url, json=corpo)
        assert r.status_code == 422 and "administrador" in r.json()["erro"]["mensagem"]
    d = (await plataforma.get(f"{P}/empresas/{admin.empresa_id}")).json()
    assert [(m["papel"], m["ativo"]) for m in d["membros"]] == [("admin", True)]


async def test_membro_ou_empresa_inexistente_da_404(plataforma: AsyncClient, operador: Usuario, admin: Usuario):
    await entrar(plataforma, operador)
    assert (await plataforma.get(f"{P}/empresas/{uuid4()}")).status_code == 404
    r = await plataforma.patch(f"{P}/empresas/{admin.empresa_id}/membros/{uuid4()}", json={"papel": "membro", "ativo": True})
    assert r.status_code == 404


async def test_toda_acao_do_operador_e_auditada(plataforma: AsyncClient, operador: Usuario, admin: Usuario, sessao: AsyncSession):
    await entrar(plataforma, operador)
    e = admin.empresa_id
    await plataforma.post(f"{P}/empresas/{e}/convites", json={"nome": "C", "email": "c@x.com", "papel": "membro"})
    await plataforma.patch(f"{P}/empresas/{e}/status", json={"status": "suspensa"})
    acoes = (await sessao.execute(text("select acao from auditoria_plataforma where empresa_id = :e order by id"), {"e": e})).scalars().all()
    assert acoes == ["membro_convidado", "empresa_suspensa"]


async def test_sem_credencial_da_plataforma_e_503(http: AsyncClient, sessao: AsyncSession, operador: Usuario):
    """Sem HUB_PLATAFORMA_DATABASE_URL o dependency devolve None (o override dos outros testes não está ativo aqui)."""
    await entrar(http, operador)
    r = await http.get(f"{P}/empresas")
    assert r.status_code == 503 and r.json()["erro"]["codigo"] == "plataforma_indisponivel"


# ----------------------------------------------------------------------------- o que o banco recusa
async def test_hub_plataforma_nao_le_dados_de_negocio(sessao: AsyncSession, admin: Usuario):
    await sessao.execute(text("set role hub_plataforma"))
    for tabela in ("negocios", "parceiro_negocio", "usuario_empresa", "usuarios", "convites", "auditoria_plataforma"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with sessao.begin_nested():
                await sessao.execute(text(f"select count(*) from {tabela}"))
    await sessao.execute(text("reset role"))


async def test_funcao_recusa_quem_nao_e_operador(sessao: AsyncSession, admin: Usuario):
    await sessao.execute(text("select set_config('app.usuario_id', :u, true)"), {"u": str(admin.id)})
    await sessao.execute(text("set role hub_plataforma"))
    with pytest.raises(DBAPIError, match="restrito ao operador"):
        await sessao.execute(text("select * from plataforma_listar_empresas(null, null)"))
    await sessao.rollback()


async def test_aplicacao_nao_cria_empresa_nem_mexe_na_auditoria(sessao: AsyncSession, admin: Usuario):
    await sessao.execute(text("set role hub_runtime"))
    for sql in (
        "select criar_empresa('Pirata')",
        "select count(*) from auditoria_plataforma",
        "insert into auditoria_plataforma (operador_id, acao) values (gen_random_uuid(), 'x')",
        "select count(*) from operador_plataforma",
    ):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with sessao.begin_nested():
                await sessao.execute(text(sql))
    await sessao.execute(text("reset role"))


async def test_auditoria_nao_se_altera_nem_pelo_dono(sessao: AsyncSession, operador: Usuario, admin: Usuario):
    await sessao.execute(text("select set_config('app.usuario_id', :u, true)"), {"u": str(operador.id)})
    await sessao.execute(text("select plataforma_definir_status(:e, 'suspensa')"), {"e": admin.empresa_id})
    for sql in ("update auditoria_plataforma set acao = 'x'", "delete from auditoria_plataforma"):
        with pytest.raises(DBAPIError, match="nao pode ser alterada"):
            async with sessao.begin_nested():
                await sessao.execute(text(sql))
