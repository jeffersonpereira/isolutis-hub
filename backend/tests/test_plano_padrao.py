"""Importação do plano de contas padrão: só com o plano vazio, ids novos por empresa, aporte de sócio marcado."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.financeiro.plano_padrao import CODIGO_APORTE_SOCIO, ler_plano_padrao
from app.models import Empresa, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from tests.conftest import SENHA

F = "/api/v1/financeiro"
IMPORTAR = f"{F}/plano-contas/importar-padrao"


async def _entrar(http: AsyncClient, email: str) -> dict[str, str]:
    r = await http.post("/api/v1/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _usuario_em(sessao: AsyncSession, empresa: Empresa, email: str, papel: str) -> Usuario:
    u = Usuario(email=email, nome=email.split("@")[0], senha_hash=gerar_hash(SENHA))
    sessao.add(u)
    await sessao.flush()
    sessao.add(UsuarioEmpresa(empresa_id=empresa.id, usuario_id=u.id, papel=papel, ativo=True))
    await sessao.commit()
    return u


# ----------------------------------------------------------------------------- o arquivo do plano padrão
def test_csv_do_plano_padrao_e_consistente():
    plano = ler_plano_padrao()
    assert len(plano) == 149
    assert [c.nivel for c in plano] == sorted(c.nivel for c in plano)  # pai antes da filha
    assert [c.codigo for c in plano if c.codigo == CODIGO_APORTE_SOCIO] == [CODIGO_APORTE_SOCIO]
    por_chave = {c.chave: c for c in plano}
    assert all(c.pai is None or c.codigo.startswith(por_chave[c.pai].codigo + ".") for c in plano)
    assert all(c.tipo_conta == "A" for c in plano if c.nivel == 3)


# ----------------------------------------------------------------------------- a rota
async def test_empresa_sem_plano_importa_o_padrao(api: AsyncClient):
    r = await api.post(IMPORTAR)
    assert r.status_code == 201, r.text
    contas = r.json()
    assert len(contas) == 149
    por_id = {c["id"]: c for c in contas}
    assert all(c["plano_pai_id"] is None or c["plano_pai_id"] in por_id for c in contas)
    assert [c["codigo"] for c in contas] == sorted((c["codigo"] for c in contas), key=lambda x: [int(p) for p in x.split(".")])
    assert [c["codigo"] for c in contas if c["aporte_socio"]] == [CODIGO_APORTE_SOCIO]
    assert len((await api.get(f"{F}/plano-contas")).json()) == 149


async def test_empresa_com_conta_recusa_e_nao_altera(api: AsyncClient):
    criada = await api.post(f"{F}/plano-contas", json={"codigo": "1", "nome": "Receita", "tipo_conta": "S", "natureza": "R"})
    assert criada.status_code == 201
    r = await api.post(IMPORTAR)
    assert r.status_code == 409 and "já tem plano" in r.json()["erro"]["mensagem"]
    assert [c["nome"] for c in (await api.get(f"{F}/plano-contas")).json()] == ["Receita"]


async def test_importar_duas_vezes_recusa_a_segunda(api: AsyncClient):
    assert (await api.post(IMPORTAR)).status_code == 201
    assert (await api.post(IMPORTAR)).status_code == 409
    assert len((await api.get(f"{F}/plano-contas")).json()) == 149


async def test_duas_empresas_importam_sem_conflito_de_ids(api: AsyncClient, http: AsyncClient, admin: Usuario, sessao: AsyncSession):
    outra = Empresa(nome="Outra Empresa")
    sessao.add(outra)
    await sessao.flush()
    dono = await _usuario_em(sessao, outra, "dono@outra.com.br", "admin")
    primeira = (await api.post(IMPORTAR)).json()
    cab = {**await _entrar(http, dono.email), "X-Empresa-ID": str(outra.id)}
    r = await http.post(IMPORTAR, headers=cab)
    assert r.status_code == 201, r.text
    segunda = r.json()
    assert len(segunda) == 149
    assert not {c["id"] for c in primeira} & {c["id"] for c in segunda}
    assert len((await http.get(f"{F}/plano-contas", headers=cab)).json()) == 149


@pytest.mark.parametrize("papel", ["membro", "comercial"])
async def test_papel_sem_permissao_financeira_e_recusado(api: AsyncClient, http: AsyncClient, admin: Usuario, sessao: AsyncSession, papel: str):
    empresa = await sessao.get(Empresa, admin.empresa_id)
    u = await _usuario_em(sessao, empresa, f"{papel}@isolutis.com.br", papel)
    cab = {**await _entrar(http, u.email), "X-Empresa-ID": str(admin.empresa_id)}
    r = await http.post(IMPORTAR, headers=cab)
    assert r.status_code == 403


async def test_financeiro_importa(api: AsyncClient, http: AsyncClient, admin: Usuario, sessao: AsyncSession):
    empresa = await sessao.get(Empresa, admin.empresa_id)
    u = await _usuario_em(sessao, empresa, "fin@isolutis.com.br", "financeiro")
    cab = {**await _entrar(http, u.email), "X-Empresa-ID": str(admin.empresa_id)}
    assert (await http.post(IMPORTAR, headers=cab)).status_code == 201


async def test_sem_login_e_401(http: AsyncClient):
    assert (await http.post(IMPORTAR)).status_code == 401
