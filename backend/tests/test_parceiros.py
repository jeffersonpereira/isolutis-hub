"""Parceiro de negócio como hub de papéis: a antiga tabela de clientes virou o papel "cliente"."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Municipio

P = "/api/v1/parceiros"
C = "/api/v1/clientes"
API = "/api/v1"
CNPJ_1, CNPJ_2 = "11222333000181", "11444777000161"
CPF = "52998224725"


async def _parceiro(api: AsyncClient, nome: str, papeis: list[str], **extra) -> dict:
    r = await api.post(P, json={"nome": nome, "papeis": papeis, **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def test_papeis_disponiveis(api: AsyncClient):
    papeis = (await api.get(f"{P}/papeis")).json()
    assert [p["codigo"] for p in papeis] == [
        "cliente",
        "fornecedor",
        "funcionario",
    ]  # por nome: Cliente, Fornecedor, Funcionário


async def test_um_parceiro_assume_varios_papeis(api: AsyncClient):
    p = await _parceiro(api, "Alfa Serviços", ["fornecedor", "cliente"], cpf_cnpj=CNPJ_1)
    assert p["papeis"] == ["cliente", "fornecedor"] and p["versao"] == 1 and p["criado_por"]

    # aparece nos dois recortes: o hub (com filtro por papel) e a lista de clientes
    assert [x["nome"] for x in (await api.get(P, params={"papel": "fornecedor"})).json()] == ["Alfa Serviços"]
    assert [x["nome"] for x in (await api.get(P, params={"papel": "funcionario"})).json()] == []
    assert [x["nome"] for x in (await api.get(C)).json()] == ["Alfa Serviços"]


async def test_clientes_so_mostra_quem_tem_o_papel_cliente(api: AsyncClient):
    forn = await _parceiro(api, "Só Fornecedor", ["fornecedor"])
    assert (await api.get(C)).json() == []
    assert (await api.put(f"{C}/{forn['id']}", json={"nome": "x", "versao": 1})).status_code == 404
    assert (await api.get(f"{C}/{forn['id']}/relacionados")).status_code == 404
    assert (await api.delete(f"{C}/{forn['id']}")).status_code == 404
    # promover a cliente pelo hub o faz aparecer
    r = await api.put(
        f"{P}/{forn['id']}",
        json={"nome": "Só Fornecedor", "papeis": ["fornecedor", "cliente"], "versao": forn["versao"]},
    )
    assert r.status_code == 200 and r.json()["papeis"] == ["cliente", "fornecedor"]
    assert [x["nome"] for x in (await api.get(C)).json()] == ["Só Fornecedor"]


async def test_negocio_so_aceita_parceiro_com_papel_cliente(api: AsyncClient):
    forn = await _parceiro(api, "Fornecedor", ["fornecedor"])
    r = await api.post(f"{API}/negocios", json={"titulo": "N", "cliente_id": forn["id"]})
    assert r.status_code == 404  # "Cliente não encontrado": não tem o papel
    await api.put(
        f"{P}/{forn['id']}", json={"nome": "Fornecedor", "papeis": ["fornecedor", "cliente"], "versao": forn["versao"]}
    )
    assert (await api.post(f"{API}/negocios", json={"titulo": "N", "cliente_id": forn["id"]})).status_code == 201


async def test_nao_perde_o_papel_cliente_com_vinculos(api: AsyncClient):
    p = await _parceiro(api, "Cliente e Fornecedor", ["cliente", "fornecedor"])
    await api.post(f"{API}/negocios", json={"titulo": "N", "cliente_id": p["id"]})
    r = await api.put(f"{P}/{p['id']}", json={"nome": p["nome"], "papeis": ["fornecedor"], "versao": p["versao"]})
    assert r.status_code == 422 and "não pode deixar de ser cliente" in r.json()["erro"]["mensagem"]
    assert (await api.delete(f"{P}/{p['id']}")).status_code == 422  # tampouco pode ser excluído


async def test_excluir_cliente_que_tem_outro_papel_so_retira_o_papel(api: AsyncClient):
    p = await _parceiro(api, "Cliente e Fornecedor", ["cliente", "fornecedor"])
    assert (await api.delete(f"{C}/{p['id']}")).status_code == 204
    restante = (await api.get(P)).json()
    assert [(x["nome"], x["papeis"]) for x in restante] == [("Cliente e Fornecedor", ["fornecedor"])]
    assert (await api.get(C)).json() == []
    # sem outro papel, a exclusão remove o parceiro
    so_cliente = await _parceiro(api, "Só Cliente", ["cliente"])
    assert (await api.delete(f"{C}/{so_cliente['id']}")).status_code == 204
    assert [x["nome"] for x in (await api.get(P)).json()] == ["Cliente e Fornecedor"]


async def test_fachada_de_clientes_preserva_os_demais_papeis(api: AsyncClient):
    p = await _parceiro(api, "Alfa", ["cliente", "funcionario"])
    r = await api.put(f"{C}/{p['id']}", json={"nome": "Alfa Renomeada", "cargo": "Diretor", "versao": p["versao"]})
    assert r.status_code == 200 and r.json()["papeis"] == ["cliente", "funcionario"] and r.json()["versao"] == 2


async def test_papel_invalido_e_obrigatorio(api: AsyncClient):
    assert (await api.post(P, json={"nome": "x", "papeis": []})).status_code == 422
    r = await api.post(P, json={"nome": "x", "papeis": ["marciano"]})
    assert r.status_code == 422 and "Papel inválido" in r.json()["erro"]["mensagem"]


async def test_documento_e_unicidade_valem_para_todos_os_papeis(api: AsyncClient):
    await _parceiro(api, "Alfa", ["fornecedor"], cpf_cnpj=CNPJ_1)
    r = await api.post(C, json={"nome": "Outro", "cpf_cnpj": CNPJ_1})
    assert r.status_code == 422 and "já existe" in r.json()["erro"]["mensagem"].lower()
    pf = (await api.post(C, json={"nome": "Maria", "cpf_cnpj": "529.982.247-25"})).json()
    assert pf["tipo_pessoa"] == "PF" and pf["cpf_cnpj"] == CPF  # tipo deduzido do documento
    assert (await api.post(C, json={"nome": "Sem documento"})).status_code == 201  # documento é opcional
    assert (await api.post(C, json={"nome": "Doc ruim", "cpf_cnpj": "52998224726"})).status_code == 422


async def test_cliente_com_municipio(api: AsyncClient, sessao: AsyncSession):
    mun = Municipio(nome="Salvador", uf="BA")
    sessao.add(mun)
    await sessao.flush()
    c = (await api.post(C, json={"nome": "Alfa", "municipio_id": str(mun.id), "cep": "40000-000"})).json()
    assert (c["municipio_nome"], c["uf"], c["cep"]) == ("Salvador", "BA", "40000000")
    assert (
        await api.post(C, json={"nome": "x", "municipio_id": "00000000-0000-0000-0000-000000000000"})
    ).status_code == 422


async def test_membro_nao_administrador_ve_clientes_mas_nao_o_hub(
    api: AsyncClient, http: AsyncClient, sessao: AsyncSession
):
    from app.models import Usuario
    from app.security import gerar_hash
    from tests.conftest import SENHA

    await _parceiro(api, "Fornecedor reservado", ["fornecedor"])
    await _parceiro(api, "Cliente visível", ["cliente"])
    sessao.add(Usuario(email="membro@isolutis.com.br", nome="Membro", admin=False, senha_hash=gerar_hash(SENHA)))
    await sessao.commit()
    token = (await http.post(f"{API}/auth/login", json={"email": "membro@isolutis.com.br", "senha": SENHA})).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {token}"}
    assert [x["nome"] for x in (await http.get(C, headers=h)).json()] == ["Cliente visível"]  # nunca vê fornecedores
    assert (await http.get(P, headers=h)).status_code == 403
    assert (await http.get(f"{P}/papeis", headers=h)).status_code == 200
    assert (await http.get(f"{API}/financeiro/municipios", headers=h)).status_code == 200  # referência aberta
    assert (await http.get(f"{API}/financeiro/titulos", headers=h)).status_code == 403


async def test_edicao_concorrente_do_parceiro(api: AsyncClient):
    p = await _parceiro(api, "Alfa", ["cliente"])
    ok = await api.put(f"{P}/{p['id']}", json={"nome": "Alfa 2", "papeis": ["cliente"], "versao": 1})
    assert ok.status_code == 200 and ok.json()["versao"] == 2
    velha = await api.put(f"{P}/{p['id']}", json={"nome": "Alfa 3", "papeis": ["cliente"], "versao": 1})
    assert velha.status_code == 409


async def _falha(sessao: AsyncSession, sql: str, params: dict | None = None) -> str:
    with pytest.raises(DBAPIError) as e:
        async with sessao.begin_nested():
            await sessao.execute(text(sql), params or {})
    return str(e.value.orig)


async def test_banco_garante_o_papel_cliente(api: AsyncClient, sessao: AsyncSession):
    forn = await _parceiro(api, "Fornecedor", ["fornecedor"])
    cli = await _parceiro(api, "Cliente", ["cliente"])
    ins = "insert into negocios (titulo, cliente_id) values ('x', :c)"
    assert "papel de cliente" in await _falha(sessao, ins, {"c": forn["id"]})
    await sessao.execute(text(ins), {"c": cli["id"]})
    erro = await _falha(
        sessao, "delete from parceiro_papel where parceiro_id = :c and papel = 'cliente'", {"c": cli["id"]}
    )
    assert "não pode deixar de ser cliente" in erro
    assert "ck_parceiro_negocio_documento" in await _falha(
        sessao,
        "update parceiro_negocio set tipo_pessoa = 'PF', cpf_cnpj = :d where id = :c",
        {"d": CNPJ_2, "c": forn["id"]},
    )


async def test_clientes_existentes_tem_titulos_e_documentos_com_o_mesmo_parceiro(
    api: AsyncClient, sessao: AsyncSession
):
    """O mesmo cadastro serve de cliente (negócio, orçamento) e de parceiro em títulos financeiros."""
    cli = await _parceiro(api, "Alfa", ["cliente"], cpf_cnpj=CNPJ_1)
    orc = await api.post(
        f"{API}/orcamentos",
        json={
            "cliente_id": cli["id"],
            "data": date.today().isoformat(),
            "itens": [{"descricao": "x", "preco_unitario": 10}],
        },
    )
    assert orc.status_code == 201 and orc.json()["cliente_nome"] == "Alfa"
    doc = await api.get(f"{API}/orcamentos/{orc.json()['id']}/documento")
    assert doc.status_code == 200 and "CNPJ 11.222.333/0001-81" in doc.text
