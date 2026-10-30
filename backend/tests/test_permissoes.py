"""Papéis e permissões contra um PostgreSQL real: matriz por papel, painel, lista mínima de clientes, isolamento
entre empresas, atribuição de papel e convites. Exige o banco de testes (ver conftest)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Empresa, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from tests.conftest import SENHA

API = "/api/v1"
PAPEIS = ("admin", "financeiro", "comercial", "membro")


async def _criar_usuario(sessao: AsyncSession, email: str, empresa: Empresa, papel: str) -> Usuario:
    u = Usuario(email=email, nome=email.split("@")[0].title(), senha_hash=gerar_hash(SENHA))
    sessao.add(u)
    await sessao.flush()
    sessao.add(UsuarioEmpresa(empresa_id=empresa.id, usuario_id=u.id, papel=papel, ativo=True))
    await sessao.commit()
    return u


async def _headers(http: AsyncClient, email: str, empresa: Empresa) -> dict[str, str]:
    r = await http.post(f"{API}/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}", "X-Empresa-ID": str(empresa.id)}


@pytest.fixture
async def empresa(sessao: AsyncSession) -> Empresa:
    e = Empresa(nome="Alfa")
    sessao.add(e)
    await sessao.commit()
    return e


@pytest.fixture
async def por_papel(http: AsyncClient, sessao: AsyncSession, empresa: Empresa) -> dict[str, dict[str, str]]:
    """Cabeçalhos autenticados de um usuário de cada papel na empresa Alfa."""
    cabecalhos: dict[str, dict[str, str]] = {}
    for papel in PAPEIS:
        email = f"{papel}@alfa.com"
        await _criar_usuario(sessao, email, empresa, papel)
        cabecalhos[papel] = await _headers(http, email, empresa)
    return cabecalhos


# GET de cada permissão e os papéis que devem entrar (o resto deve receber 403)
ACESSO = [
    ("/painel", {"admin", "financeiro", "comercial", "membro"}),
    ("/tarefas", {"admin", "financeiro", "comercial", "membro"}),
    ("/projetos", {"admin", "financeiro", "comercial", "membro"}),
    ("/equipe", {"admin", "financeiro", "comercial", "membro"}),
    ("/clientes/referencias", {"admin", "financeiro", "comercial", "membro"}),
    ("/clientes", {"admin", "comercial"}),
    ("/negocios", {"admin", "comercial"}),
    ("/orcamentos", {"admin", "comercial"}),
    ("/produtos", {"admin", "comercial"}),
    ("/faturamento", {"admin", "financeiro"}),
    ("/financeiro/recorrencias", {"admin", "financeiro"}),
    ("/relatorios/dre", {"admin", "financeiro"}),
    ("/financeiro/titulos", {"admin", "financeiro"}),
    ("/financeiro/titulos/exportar", {"admin", "financeiro"}),
    ("/parceiros", {"admin", "financeiro"}),
    ("/usuarios", {"admin"}),
    ("/convites", {"admin"}),
]


@pytest.mark.parametrize(("caminho", "permitidos"), ACESSO)
async def test_matriz_por_papel(http: AsyncClient, por_papel: dict, caminho: str, permitidos: set[str]):
    for papel in PAPEIS:
        r = await http.get(f"{API}{caminho}", headers=por_papel[papel])
        if papel in permitidos:
            assert r.status_code != 403, f"{papel} deveria acessar {caminho}: {r.text}"
        else:
            assert r.status_code == 403, f"{papel} não deveria acessar {caminho}"
            assert r.json()["erro"]["codigo"] == "sem_permissao"


async def test_empresas_traz_papel_e_permissoes(http: AsyncClient, por_papel: dict, empresa: Empresa):
    r = await http.get(f"{API}/empresas", headers=por_papel["financeiro"])
    assert r.status_code == 200
    item = next(e for e in r.json() if e["id"] == str(empresa.id))
    assert item["papel"] == "financeiro"
    assert item["permissoes"] == ["base", "financeiro"]


async def test_nao_existe_post_empresas(http: AsyncClient, por_papel: dict):
    r = await http.post(f"{API}/empresas", json={"nome": "Nova"}, headers=por_papel["admin"])
    assert r.status_code == 405


async def test_membro_ve_nome_do_cliente_sem_dados_de_contato(http: AsyncClient, por_papel: dict):
    criado = await http.post(
        f"{API}/clientes",
        json={"nome": "Distribuidora Alfa", "email": "x@y.com", "telefone": "7199"},
        headers=por_papel["comercial"],
    )
    assert criado.status_code == 201, criado.text
    # Escopo de acesso: o cliente nasce com o comercial como dono; o membro só recebe nomes de clientes
    # ligados a algo que ele enxerga (aqui, nada) — e nunca contato ou documento.
    r = await http.get(f"{API}/clientes/referencias", headers=por_papel["membro"])
    assert r.status_code == 200
    assert r.json() == []
    assert (await http.get(f"{API}/clientes/referencias", headers=por_papel["comercial"])).json() == [
        {"id": criado.json()["id"], "nome": "Distribuidora Alfa"}
    ]
    assert (await http.get(f"{API}/clientes", headers=por_papel["membro"])).status_code == 403


async def test_painel_omite_blocos_sem_permissao(http: AsyncClient, por_papel: dict):
    membro = (await http.get(f"{API}/painel", headers=por_papel["membro"])).json()
    for campo in ("funil_abertos", "ganhos", "orcamentos_aguardando", "recebido_no_mes", "serie", "por_etapa"):
        assert campo not in membro
    assert set(membro["alertas"]) == {"projetos_atrasados"}

    financeiro = (await http.get(f"{API}/painel", headers=por_papel["financeiro"])).json()
    assert "recebido_no_mes" in financeiro and "funil_abertos" not in financeiro

    admin = (await http.get(f"{API}/painel", headers=por_papel["admin"])).json()
    assert "recebido_no_mes" in admin and "funil_abertos" in admin
    assert {"lancamentos_vencidos", "orcamentos_parados", "projetos_atrasados"} <= set(admin["alertas"])


async def test_rebaixar_papel_vale_na_proxima_requisicao(
    http: AsyncClient, por_papel: dict, sessao: AsyncSession, empresa
):
    assert (await http.get(f"{API}/negocios", headers=por_papel["comercial"])).status_code == 200
    u = await sessao.scalar(select(Usuario).where(Usuario.email == "comercial@alfa.com"))
    membership = await sessao.get(UsuarioEmpresa, (empresa.id, u.id))
    membership.papel = "membro"
    await sessao.commit()
    assert (await http.get(f"{API}/negocios", headers=por_papel["comercial"])).status_code == 403


# ----------------------------------------------------------------------------- isolamento entre empresas
async def test_mesmo_usuario_com_papeis_diferentes_em_duas_empresas(
    http: AsyncClient, sessao: AsyncSession, empresa: Empresa
):
    outra = Empresa(nome="Beta")
    sessao.add(outra)
    await sessao.flush()
    u = await _criar_usuario(sessao, "duplo@x.com", empresa, "admin")
    sessao.add(UsuarioEmpresa(empresa_id=outra.id, usuario_id=u.id, papel="membro", ativo=True))
    await sessao.commit()

    na_alfa = await _headers(http, "duplo@x.com", empresa)
    na_beta = {**na_alfa, "X-Empresa-ID": str(outra.id)}
    assert (await http.get(f"{API}/usuarios", headers=na_alfa)).status_code == 200
    assert (await http.get(f"{API}/usuarios", headers=na_beta)).status_code == 403


async def test_empresa_sem_membership_e_recusada(http: AsyncClient, por_papel: dict, sessao: AsyncSession):
    estranha = Empresa(nome="Gama")
    sessao.add(estranha)
    await sessao.commit()
    r = await http.get(f"{API}/painel", headers={**por_papel["admin"], "X-Empresa-ID": str(estranha.id)})
    assert r.status_code == 403
    assert r.json()["erro"]["codigo"] == "empresa_inacessivel"  # o front reabre a escolha de empresa


# ----------------------------------------------------------------------------- atribuição de papel
async def test_admin_atribui_papel_e_resposta_traz_papel(http: AsyncClient, por_papel: dict):
    r = await http.post(
        f"{API}/usuarios",
        json={"nome": "Nova", "email": "nova@alfa.com", "senha": "senha-longa-1", "papel": "financeiro"},
        headers=por_papel["admin"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["papel"] == "financeiro" and "admin" not in r.json()


async def test_papel_invalido_e_recusado_na_criacao(http: AsyncClient, por_papel: dict):
    r = await http.post(
        f"{API}/usuarios",
        json={"nome": "X", "email": "x@alfa.com", "senha": "senha-longa-1", "papel": "root"},
        headers=por_papel["admin"],
    )
    assert r.status_code == 422


async def test_nao_admin_nao_atribui_papel(http: AsyncClient, por_papel: dict):
    r = await http.post(
        f"{API}/usuarios",
        json={"nome": "X", "email": "x@alfa.com", "senha": "senha-longa-1", "papel": "admin"},
        headers=por_papel["financeiro"],
    )
    assert r.status_code == 403


async def test_admin_nao_rebaixa_a_si_mesmo(http: AsyncClient, por_papel: dict):
    lista = (await http.get(f"{API}/usuarios", headers=por_papel["admin"])).json()
    eu = next(u for u in lista if u["email"] == "admin@alfa.com")
    r = await http.put(
        f"{API}/usuarios/{eu['id']}",
        json={"nome": eu["nome"], "papel": "membro", "ativo": True, "versao": eu["versao"]},
        headers=por_papel["admin"],
    )
    assert r.status_code == 422 and "próprio acesso de administrador" in r.json()["erro"]["mensagem"]


async def test_convite_aceita_os_quatro_papeis(http: AsyncClient, por_papel: dict):
    for papel in PAPEIS:
        r = await http.post(
            f"{API}/convite",
            json={"nome": papel, "email": f"conv-{papel}@x.com", "papel": papel},
            headers=por_papel["admin"],
        )
        assert r.status_code == 201, r.text
        assert r.json()["papel"] == papel
    r = await http.post(
        f"{API}/convite", json={"nome": "x", "email": "conv-x@x.com", "papel": "root"}, headers=por_papel["admin"]
    )
    assert r.status_code == 422


# ----------------------------------------------------------------------------- cadastros por papel de parceiro
async def _novo_parceiro(http: AsyncClient, cab: dict[str, str], nome: str, papeis: list[str], **extra) -> dict:
    r = await http.post(f"{API}/parceiros", headers=cab, json={"nome": nome, "papeis": papeis, **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def test_financeiro_nao_ve_funcionarios_nem_socios(http: AsyncClient, por_papel: dict):
    admin, fin = por_papel["admin"], por_papel["financeiro"]
    await _novo_parceiro(http, admin, "Fornecedora", ["fornecedor"])
    await _novo_parceiro(http, admin, "Maria Sócia", ["socio"], participacao_percentual=50)
    await _novo_parceiro(http, admin, "Zé Funcionário", ["funcionario"])
    nomes = [p["nome"] for p in (await http.get(f"{API}/parceiros", headers=fin)).json()]
    assert nomes == ["Fornecedora"]
    papeis = (await http.get(f"{API}/parceiros/papeis", headers=fin)).json()
    assert [p["codigo"] for p in papeis] == ["cliente", "fornecedor"]
    assert (await http.get(f"{API}/parceiros", headers=fin, params={"papel": "socio"})).status_code == 403


async def test_financeiro_nao_cria_nem_edita_socio(http: AsyncClient, por_papel: dict):
    admin, fin = por_papel["admin"], por_papel["financeiro"]
    corpo_socio = {"nome": "X", "papeis": ["socio"], "participacao_percentual": 10}
    r = await http.post(f"{API}/parceiros", headers=fin, json=corpo_socio)
    assert r.status_code == 403
    socia = await _novo_parceiro(http, admin, "Maria Sócia", ["socio"], participacao_percentual=50)
    corpo = {"nome": "Maria", "papeis": ["fornecedor"], "versao": socia["versao"]}
    assert (await http.put(f"{API}/parceiros/{socia['id']}", headers=fin, json=corpo)).status_code == 404
    assert (await http.delete(f"{API}/parceiros/{socia['id']}", headers=fin)).status_code == 404


async def test_parceiro_com_papel_oculto_aparece_sem_ele_e_o_mantem(http: AsyncClient, por_papel: dict):
    admin, fin = por_papel["admin"], por_papel["financeiro"]
    p = await _novo_parceiro(http, admin, "Alfa", ["fornecedor", "funcionario"])
    visto = (await http.get(f"{API}/parceiros", headers=fin)).json()
    assert [x["papeis"] for x in visto] == [["fornecedor"]]
    # o financeiro troca fornecedor por cliente: o papel de funcionário, que ele nem vê, continua
    corpo = {"nome": "Alfa", "papeis": ["cliente"], "versao": p["versao"]}
    r = await http.put(f"{API}/parceiros/{p['id']}", headers=fin, json=corpo)
    assert r.status_code == 200 and r.json()["papeis"] == ["cliente"]
    como_admin = (await http.get(f"{API}/parceiros", headers=admin, params={"papel": "funcionario"})).json()
    assert [x["papeis"] for x in como_admin] == [["cliente", "funcionario"]]


async def test_financeiro_nao_exclui_parceiro_com_papel_que_nao_gerencia(http: AsyncClient, por_papel: dict):
    admin, fin = por_papel["admin"], por_papel["financeiro"]
    p = await _novo_parceiro(http, admin, "Alfa", ["fornecedor", "funcionario"])
    assert (await http.delete(f"{API}/parceiros/{p['id']}", headers=fin)).status_code == 403


async def test_participacao_do_socio_so_aparece_para_o_admin(http: AsyncClient, por_papel: dict):
    admin, fin = por_papel["admin"], por_papel["financeiro"]
    await _novo_parceiro(http, admin, "Maria", ["socio", "cliente"], participacao_percentual=30)
    como_fin = (await http.get(f"{API}/parceiros", headers=fin)).json()
    assert como_fin[0]["papeis"] == ["cliente"] and como_fin[0]["participacao_percentual"] is None
    como_admin = (await http.get(f"{API}/parceiros", headers=admin)).json()
    assert como_admin[0]["participacao_percentual"] == 30
