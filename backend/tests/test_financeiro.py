from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.financeiro.models import InstituicaoFinanceira
from app.models import Empresa, Municipio, Usuario
from app.security import gerar_hash
from tests.conftest import SENHA

F = "/api/v1/financeiro"
P = "/api/v1/parceiros"
ANO = date.today().year
CNPJ = "11222333000181"
CPF = "52998224725"


@pytest.fixture
async def ref(sessao: AsyncSession) -> dict:
    """Referências mínimas (a carga completa é feita por app.financeiro.popular)."""
    mun = Municipio(nome="Salvador", uf="BA")
    banco = InstituicaoFinanceira(codigo="001", nome="Banco do Brasil S.A.")
    outro = InstituicaoFinanceira(codigo="341", nome="Itaú Unibanco S.A.")
    sessao.add_all([mun, banco, outro])
    await sessao.flush()
    return {"municipio": str(mun.id), "banco": str(banco.id), "outro_banco": str(outro.id)}


async def _criar_parceiro(api: AsyncClient, corpo: dict) -> dict:
    r = await api.post(P, json={"papeis": ["fornecedor"], **corpo})
    assert r.status_code == 201, r.text
    return r.json()


async def _criar(api: AsyncClient, caminho: str, corpo: dict, esperado: int = 201) -> dict:
    r = await api.post(f"{F}{caminho}", json=corpo)
    assert r.status_code == esperado, r.text
    return r.json()


@pytest.fixture
async def plano(api: AsyncClient) -> dict:
    """1 Receita > 1.01 Contrato de Sistemas > 1.01.001 GT   ·   2 Despesa > 2.01 Pessoal > 2.01.001 Salário"""
    rec = await _criar(api, "/plano-contas", {"codigo": "1", "nome": "Receita", "tipo_conta": "S", "natureza": "R"})
    rec1 = await _criar(
        api,
        "/plano-contas",
        {"plano_pai_id": rec["id"], "codigo": "1.01", "nome": "Contrato de Sistemas", "tipo_conta": "S"},
    )
    gt = await _criar(
        api, "/plano-contas", {"plano_pai_id": rec1["id"], "codigo": "1.01.001", "nome": "GT", "tipo_conta": "A"}
    )
    desp = await _criar(api, "/plano-contas", {"codigo": "2", "nome": "Despesa", "tipo_conta": "S", "natureza": "D"})
    desp1 = await _criar(
        api, "/plano-contas", {"plano_pai_id": desp["id"], "codigo": "2.01", "nome": "Pessoal", "tipo_conta": "S"}
    )
    sal = await _criar(
        api, "/plano-contas", {"plano_pai_id": desp1["id"], "codigo": "2.01.001", "nome": "Salário", "tipo_conta": "A"}
    )
    return {"receita": rec, "contrato": rec1, "gt": gt, "despesa": desp, "pessoal": desp1, "salario": sal}


@pytest.fixture
async def conta_bancaria(api: AsyncClient, ref: dict) -> dict:
    return await _criar(
        api,
        "/contas-bancarias",
        {"instituicao_financeira_id": ref["banco"], "nome": "Conta principal", "saldo_inicial": 1000},
    )


@pytest.fixture
async def parceiro(api: AsyncClient, ref: dict) -> dict:
    r = await api.post(
        P,
        json={
            "tipo_pessoa": "PJ",
            "cpf_cnpj": "11.222.333/0001-81",
            "nome": "Fornecedor Alfa",
            "municipio_id": ref["municipio"],
            "papeis": ["fornecedor"],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# ============================================================================ acesso
async def test_modulo_exige_administrador(http: AsyncClient, admin: Usuario, sessao: AsyncSession):
    assert (await http.get(f"{F}/plano-contas")).status_code == 401
    sessao.add(Usuario(email="membro@isolutis.com.br", nome="Membro", admin=False, senha_hash=gerar_hash(SENHA)))
    await sessao.commit()
    token = (await http.post("/api/v1/auth/login", json={"email": "membro@isolutis.com.br", "senha": SENHA})).json()[
        "access_token"
    ]
    r = await http.get(f"{F}/plano-contas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403 and r.json()["erro"]["codigo"] == "sem_permissao"


async def test_empresa_unica_foi_criada_pela_migracao(sessao: AsyncSession):
    assert [e.nome for e in (await sessao.scalars(__import__("sqlalchemy").select(Empresa))).all()] == ["iSolutis"]


# ============================================================================ US01 / RN01 plano de contas
async def test_plano_de_contas_hierarquia_e_heranca(api: AsyncClient, plano: dict):
    arvore = (await api.get(f"{F}/plano-contas")).json()
    assert [c["codigo"] for c in arvore] == ["1", "1.01", "1.01.001", "2", "2.01", "2.01.001"]
    por_codigo = {c["codigo"]: c for c in arvore}
    assert [por_codigo[c]["nivel"] for c in ("1", "1.01", "1.01.001")] == [1, 2, 3]
    assert por_codigo["1.01.001"]["natureza"] == "R" and por_codigo["2.01.001"]["natureza"] == "D"  # herdada do pai
    assert por_codigo["1"]["possui_filhas"] and not por_codigo["1.01.001"]["possui_filhas"]


async def test_natureza_enviada_na_filha_e_ignorada(api: AsyncClient, plano: dict):
    filha = await _criar(
        api,
        "/plano-contas",
        {
            "plano_pai_id": plano["contrato"]["id"],
            "codigo": "1.01.002",
            "nome": "Outro",
            "tipo_conta": "A",
            "natureza": "D",
        },
    )
    assert filha["natureza"] == "R"


@pytest.mark.parametrize(
    ("corpo", "trecho"),
    [
        ({"codigo": "1.01", "nome": "x", "tipo_conta": "S", "natureza": "R"}, "número"),  # raiz com ponto
        ({"codigo": "3", "nome": "x", "tipo_conta": "S"}, "natureza"),  # raiz sem natureza
        ({"codigo": "1", "nome": "dup", "tipo_conta": "S", "natureza": "R"}, "já existe"),
    ],
)
async def test_regras_de_raiz(api: AsyncClient, plano: dict, corpo: dict, trecho: str):
    r = await api.post(f"{F}/plano-contas", json=corpo)
    assert r.status_code == 422
    assert trecho in r.text.lower()


async def test_regras_de_filhas(api: AsyncClient, plano: dict):
    pai_sintetico, pai_analitico = plano["contrato"]["id"], plano["gt"]["id"]
    casos = [
        (
            {"plano_pai_id": pai_analitico, "codigo": "1.01.001.001", "nome": "x", "tipo_conta": "A"},
            "analítica não pode ter",
        ),
        ({"plano_pai_id": pai_sintetico, "codigo": "1.01.01", "nome": "x", "tipo_conta": "A"}, "código deve ser"),
        ({"plano_pai_id": pai_sintetico, "codigo": "2.01.005", "nome": "x", "tipo_conta": "A"}, "código deve ser"),
        ({"plano_pai_id": pai_sintetico, "codigo": "1.01.002", "nome": "x", "tipo_conta": "S"}, "terceiro nível"),
        ({"plano_pai_id": pai_sintetico, "codigo": "1.01.001", "nome": "x", "tipo_conta": "A"}, "já existe"),
    ]
    for corpo, trecho in casos:
        r = await api.post(f"{F}/plano-contas", json=corpo)
        assert r.status_code == 422 and trecho in r.json()["erro"]["mensagem"].lower(), (corpo, r.text)


async def test_proximo_codigo_sugerido(api: AsyncClient, plano: dict):
    assert (await api.get(f"{F}/plano-contas/proximo-codigo")).json() == {"codigo": "3"}
    assert (await api.get(f"{F}/plano-contas/proximo-codigo", params={"pai_id": plano["receita"]["id"]})).json() == {
        "codigo": "1.02"
    }
    assert (await api.get(f"{F}/plano-contas/proximo-codigo", params={"pai_id": plano["contrato"]["id"]})).json() == {
        "codigo": "1.01.002"
    }
    assert (await api.get(f"{F}/plano-contas/proximo-codigo", params={"pai_id": plano["gt"]["id"]})).status_code == 422


async def test_editar_e_excluir_conta_do_plano(api: AsyncClient, plano: dict):
    gt = plano["gt"]
    r = await api.put(
        f"{F}/plano-contas/{gt['id']}",
        json={"plano_pai_id": plano["contrato"]["id"], "codigo": "1.01.001", "nome": "GT Sistemas", "tipo_conta": "A"},
    )
    assert r.status_code == 200 and r.json()["nome"] == "GT Sistemas"
    # conta com filhas: não muda código nem vira analítica; não pode ser excluída
    r = await api.put(
        f"{F}/plano-contas/{plano['receita']['id']}",
        json={"codigo": "9", "nome": "Receita", "tipo_conta": "S", "natureza": "R"},
    )
    assert r.status_code == 422 and "filhas" in r.json()["erro"]["mensagem"]
    r = await api.put(
        f"{F}/plano-contas/{plano['receita']['id']}",
        json={"codigo": "1", "nome": "Receita", "tipo_conta": "A", "natureza": "R"},
    )
    assert r.status_code == 422
    assert (await api.delete(f"{F}/plano-contas/{plano['receita']['id']}")).status_code == 422
    assert (await api.delete(f"{F}/plano-contas/{gt['id']}")).status_code == 204
    assert (await api.delete(f"{F}/plano-contas/{gt['id']}")).status_code == 404


# ============================================================================ US02 / RN02 contas bancárias
async def test_contas_bancarias_crud_e_duplicidade(api: AsyncClient, ref: dict):
    c = await _criar(
        api,
        "/contas-bancarias",
        {"instituicao_financeira_id": ref["banco"], "nome": "Principal", "saldo_inicial": 2500.5},
    )
    assert c["instituicao_codigo"] == "001" and c["saldo_inicial"] == 2500.5
    # mesma instituição + mesmo nome (sem diferenciar maiúsculas/espaços) na empresa: recusado
    r = await api.post(
        f"{F}/contas-bancarias", json={"instituicao_financeira_id": ref["banco"], "nome": "  principal "}
    )
    assert r.status_code == 422 and "já existe" in r.json()["erro"]["mensagem"].lower()
    # outra instituição com o mesmo nome é permitido
    await _criar(api, "/contas-bancarias", {"instituicao_financeira_id": ref["outro_banco"], "nome": "Principal"})
    r = await api.put(
        f"{F}/contas-bancarias/{c['id']}",
        json={"instituicao_financeira_id": ref["banco"], "nome": "Principal PJ", "saldo_inicial": 0},
    )
    assert r.status_code == 200 and r.json()["nome"] == "Principal PJ"
    assert len((await api.get(f"{F}/contas-bancarias")).json()) == 2
    assert (
        await api.post(
            f"{F}/contas-bancarias",
            json={"instituicao_financeira_id": "00000000-0000-0000-0000-000000000000", "nome": "x"},
        )
    ).status_code == 422
    assert (await api.delete(f"{F}/contas-bancarias/{c['id']}")).status_code == 204


# ============================================================================ US04 parceiros
async def test_parceiros_validam_documento_e_unicidade(api: AsyncClient, ref: dict):
    base = {
        "papeis": ["fornecedor"],
        "tipo_pessoa": "PJ",
        "nome": "Alfa",
        "municipio_id": ref["municipio"],
        "cep": "40.000-000",
        "endereco": " Rua A, 10 ",
    }
    r = await api.post(f"{P}", json={**base, "cpf_cnpj": "11.222.333/0001-80"})
    assert r.status_code == 422 and "CNPJ inválido" in r.json()["erro"]["mensagem"]
    p = await _criar_parceiro(api, {**base, "cpf_cnpj": "11.222.333/0001-81"})
    assert (
        p["cpf_cnpj"] == CNPJ
        and p["cep"] == "40000000"
        and p["endereco"] == "Rua A, 10"
        and (p["municipio_nome"], p["uf"]) == ("Salvador", "BA")
    )
    r = await api.post(f"{P}", json={**base, "nome": "Duplicado", "cpf_cnpj": CNPJ})
    assert r.status_code == 422 and "já existe" in r.json()["erro"]["mensagem"].lower()
    pf = await _criar_parceiro(
        api,
        {"tipo_pessoa": "PF", "cpf_cnpj": "529.982.247-25", "nome": "Maria", "municipio_id": ref["municipio"]},
    )
    assert pf["cpf_cnpj"] == CPF and pf["cep"] is None
    assert (
        await api.post(f"{P}", json={**base, "tipo_pessoa": "PF", "cpf_cnpj": CNPJ})
    ).status_code == 422  # CNPJ marcado como PF
    assert (
        await api.post(f"{P}", json={**base, "cpf_cnpj": "52998224726", "tipo_pessoa": "PF", "cep": "123"})
    ).status_code == 422
    achados = (await api.get(f"{P}", params={"busca": "mar"})).json()
    assert [x["nome"] for x in achados] == ["Maria"]
    assert [x["nome"] for x in (await api.get(f"{P}", params={"busca": "11.222"})).json()] == ["Alfa"]
    r = await api.put(
        f"{P}/{p['id']}", json={**base, "cpf_cnpj": CNPJ, "nome": "Alfa Renomeada", "versao": p["versao"]}
    )
    assert r.json()["nome"] == "Alfa Renomeada"
    assert (await api.delete(f"{P}/{pf['id']}")).status_code == 204


# ============================================================================ US03 / RN03 / RN04 títulos
def _titulo(plano: dict, conta: dict, parceiro: dict, **extra) -> dict:
    return {
        "tipo_conta": "R", "conta_bancaria_id": conta["id"], "plano_conta_id": plano["gt"]["id"], "parceiro_id": parceiro["id"],
        "data_emissao": f"{ANO}-01-05", "data_vencimento": f"{ANO}-01-20", "valor_titulo": 1000, **extra,
    }  # fmt: skip


async def test_titulo_so_em_conta_analitica_e_com_natureza_compativel(
    api: AsyncClient, plano: dict, conta_bancaria: dict, parceiro: dict
):
    r = await api.post(
        f"{F}/titulos", json=_titulo(plano, conta_bancaria, parceiro, plano_conta_id=plano["contrato"]["id"])
    )
    assert r.status_code == 422 and "conta analítica" in r.json()["erro"]["mensagem"]  # RN03
    r = await api.post(
        f"{F}/titulos", json=_titulo(plano, conta_bancaria, parceiro, tipo_conta="P")
    )  # a pagar numa conta de receita
    assert r.status_code == 422 and "despesa" in r.json()["erro"]["mensagem"]  # RN04
    r = await api.post(
        f"{F}/titulos", json=_titulo(plano, conta_bancaria, parceiro, plano_conta_id=plano["salario"]["id"])
    )  # a receber em despesa
    assert r.status_code == 422
    ok = await _criar(
        api, "/titulos", _titulo(plano, conta_bancaria, parceiro, tipo_conta="P", plano_conta_id=plano["salario"]["id"])
    )
    assert ok["status"] == "A" and ok["plano_conta_codigo"] == "2.01.001" and ok["parceiro_nome"] == "Fornecedor Alfa"


async def test_titulo_valores_quitacao_e_cancelamento(
    api: AsyncClient, plano: dict, conta_bancaria: dict, parceiro: dict
):
    base = _titulo(plano, conta_bancaria, parceiro, valor_desconto=50, valor_multa=10, valor_juros=5.25)
    t = await _criar(api, "/titulos", base)
    assert t["valor_devido"] == 965.25 and t["valor_quitacao"] == 0 and t["data_pagamento"] is None
    # quitar exige a data; sem valor assume o valor devido
    r = await api.put(f"{F}/titulos/{t['id']}", json={**base, "status": "Q"})
    assert r.status_code == 422 and "data de pagamento" in r.json()["erro"]["mensagem"]
    q = (await api.put(f"{F}/titulos/{t['id']}", json={**base, "status": "Q", "data_pagamento": f"{ANO}-01-22"})).json()
    assert (q["status"], q["valor_quitacao"], q["data_pagamento"]) == ("Q", 965.25, f"{ANO}-01-22")
    # reabrir limpa a quitação; cancelar também
    aberto = (
        await api.put(
            f"{F}/titulos/{t['id']}",
            json={**base, "status": "A", "data_pagamento": f"{ANO}-01-22", "valor_quitacao": 10},
        )
    ).json()
    assert (aberto["data_pagamento"], aberto["valor_quitacao"]) == (None, 0)
    assert (await api.put(f"{F}/titulos/{t['id']}", json={**base, "status": "C"})).json()["status"] == "C"
    # validações
    assert (await api.post(f"{F}/titulos", json={**base, "valor_titulo": 0})).status_code == 422
    assert (
        await api.post(f"{F}/titulos", json={**base, "valor_desconto": 1020})
    ).status_code == 422  # desconto maior que o valor devido
    assert (
        await api.post(f"{F}/titulos", json={**base, "data_emissao": f"{ANO}-02-01"})
    ).status_code == 422  # emissão depois do vencimento
    assert (await api.post(f"{F}/titulos", json={**base, "status": "X"})).status_code == 422


async def test_titulo_filtros_e_exclusao_com_bloqueios(
    api: AsyncClient, plano: dict, conta_bancaria: dict, parceiro: dict
):
    a = await _criar(api, "/titulos", _titulo(plano, conta_bancaria, parceiro))
    b = await _criar(
        api,
        "/titulos",
        _titulo(
            plano,
            conta_bancaria,
            parceiro,
            tipo_conta="P",
            plano_conta_id=plano["salario"]["id"],
            data_vencimento=f"{ANO}-03-10",
            valor_titulo=300,
        ),
    )
    assert [t["id"] for t in (await api.get(f"{F}/titulos")).json()] == [a["id"], b["id"]]  # por vencimento
    assert [t["id"] for t in (await api.get(f"{F}/titulos", params={"tipo": "P"})).json()] == [b["id"]]
    assert [t["id"] for t in (await api.get(f"{F}/titulos", params={"de": f"{ANO}-02-01"})).json()] == [b["id"]]
    assert (await api.get(f"{F}/titulos", params={"status": "Q"})).json() == []
    assert len((await api.get(f"{F}/titulos", params={"busca": "alfa"})).json()) == 2
    # com título lançado, conta bancária / parceiro / conta do plano não podem ser excluídos nem mudar de natureza
    assert (await api.delete(f"{F}/contas-bancarias/{conta_bancaria['id']}")).status_code == 422
    assert (await api.delete(f"{P}/{parceiro['id']}")).status_code == 422
    assert (await api.delete(f"{F}/plano-contas/{plano['gt']['id']}")).status_code == 422
    r = await api.put(
        f"{F}/plano-contas/{plano['gt']['id']}",
        json={"plano_pai_id": plano["contrato"]["id"], "codigo": "1.01.001", "nome": "GT", "tipo_conta": "A"},
    )
    assert r.status_code == 200
    assert (await api.delete(f"{F}/titulos/{a['id']}")).status_code == 204
    assert (await api.delete(f"{F}/titulos/{a['id']}")).status_code == 404


# ============================================================================ US05 fluxo de caixa
async def test_fluxo_de_caixa_mensal(api: AsyncClient, plano: dict, conta_bancaria: dict, parceiro: dict):
    rec = _titulo(plano, conta_bancaria, parceiro, valor_titulo=1000)
    pag = _titulo(
        plano,
        conta_bancaria,
        parceiro,
        tipo_conta="P",
        plano_conta_id=plano["salario"]["id"],
        valor_titulo=400,
        data_vencimento=f"{ANO}-01-25",
    )
    await _criar(
        api, "/titulos", {**rec, "status": "Q", "data_pagamento": f"{ANO}-01-21"}
    )  # entrada realizada em janeiro
    await _criar(
        api, "/titulos", {**rec, "data_vencimento": f"{ANO}-02-10", "valor_titulo": 500, "valor_juros": 20}
    )  # entrada prevista em fevereiro (520 devidos)
    await _criar(api, "/titulos", pag)  # saída prevista em janeiro
    await _criar(
        api,
        "/titulos",
        {
            **pag,
            "data_vencimento": f"{ANO}-02-25",
            "valor_titulo": 100,
            "status": "Q",
            "data_pagamento": f"{ANO}-02-26",
        },
    )  # saída realizada em fevereiro
    await _criar(api, "/titulos", {**rec, "status": "C", "valor_titulo": 9999})  # cancelado não entra
    await _criar(
        api,
        "/titulos",
        {
            **rec,
            "status": "Q",
            "data_emissao": None,
            "data_vencimento": f"{ANO - 1}-12-10",
            "data_pagamento": f"{ANO - 1}-12-12",
            "valor_titulo": 250,
        },
    )  # realizado antes do ano: vira saldo

    f = (await api.get(f"{F}/fluxo-de-caixa", params={"ano": ANO})).json()
    assert f["saldo_inicial"] == 1250  # 1000 da conta bancária + 250 recebidos em dezembro do ano anterior
    jan, fev, mar = f["meses"][0], f["meses"][1], f["meses"][2]
    assert (
        jan["entradas_realizadas"],
        jan["entradas_previstas"],
        jan["saidas_realizadas"],
        jan["saidas_previstas"],
    ) == (1000, 0, 0, 400)
    assert (jan["saldo_do_mes"], jan["saldo_acumulado"]) == (600, 1850)
    assert (fev["entradas_previstas"], fev["saidas_realizadas"], fev["saldo_do_mes"], fev["saldo_acumulado"]) == (
        520,
        100,
        420,
        2270,
    )
    assert mar["saldo_do_mes"] == 0 and mar["saldo_acumulado"] == 2270 and len(f["meses"]) == 12
    assert (f["total_entradas"], f["total_saidas"]) == (1520, 500)
    assert ANO in f["anos_disponiveis"] and ANO - 1 in f["anos_disponiveis"]


# ============================================================================ o banco repete as regras (defesa em profundidade)
async def _sql_deve_falhar(sessao: AsyncSession, sql: str, params: dict | None = None) -> str:
    """Executa o SQL num SAVEPOINT, espera que o banco o recuse e devolve a mensagem do banco."""
    with pytest.raises(DBAPIError) as e:
        async with sessao.begin_nested():
            await sessao.execute(text(sql), params or {})
    return str(e.value.orig)


async def test_banco_impoe_hierarquia_e_regras_do_titulo(
    api: AsyncClient, sessao: AsyncSession, plano: dict, conta_bancaria: dict, parceiro: dict
):
    empresa = await sessao.scalar(text("select id from companies limit 1"))
    ins = "insert into plano_contas (company_id, plano_pai_id, codigo, nome, tipo_conta, natureza, nivel) values (:c, :p, :cod, 'x', :t, :n, :nv)"
    # filha de conta analítica
    erro = await _sql_deve_falhar(
        sessao, ins, {"c": empresa, "p": plano["gt"]["id"], "cod": "1.01.001.001", "t": "A", "n": "R", "nv": 3}
    )
    assert "chk" in erro.lower() or "check" in erro.lower() or "analítica" in erro or "nivel" in erro.lower()
    # código fora do padrão do nível
    erro = await _sql_deve_falhar(
        sessao, ins, {"c": empresa, "p": plano["receita"]["id"], "cod": "1.1", "t": "A", "n": "R", "nv": 2}
    )
    assert "ck_plano_contas_codigo" in erro
    # código sem o prefixo do pai (o trigger também deriva a natureza e o nível)
    erro = await _sql_deve_falhar(
        sessao, ins, {"c": empresa, "p": plano["receita"]["id"], "cod": "2.09", "t": "S", "n": "R", "nv": 2}
    )
    assert "começar com o código do pai" in erro
    # título em conta sintética e com natureza trocada
    tit = "insert into titulo_financeiro (company_id, conta_bancaria_id, plano_conta_id, parceiro_id, tipo_conta, data_vencimento, valor_titulo) values (:c, :cb, :pc, :pa, :t, current_date, 10)"
    base = {"c": empresa, "cb": conta_bancaria["id"], "pa": parceiro["id"]}
    assert "conta analítica" in await _sql_deve_falhar(sessao, tit, {**base, "pc": plano["contrato"]["id"], "t": "R"})
    assert "despesa" in await _sql_deve_falhar(sessao, tit, {**base, "pc": plano["gt"]["id"], "t": "P"})
    # quitado sem data de pagamento
    ins_q = "insert into titulo_financeiro (company_id, conta_bancaria_id, plano_conta_id, parceiro_id, tipo_conta, data_vencimento, valor_titulo, status, valor_quitacao) values (:c, :cb, :pc, :pa, 'R', current_date, 10, 'Q', 10)"
    assert "ck_titulo_financeiro_quitacao" in await _sql_deve_falhar(sessao, ins_q, {**base, "pc": plano["gt"]["id"]})


async def test_banco_isola_empresas(sessao: AsyncSession, plano: dict):
    """FKs compostas: uma conta de outra empresa não pode ser pai nem receber título."""
    outra = Empresa(nome="Outra Empresa")
    sessao.add(outra)
    await sessao.flush()
    erro = await _sql_deve_falhar(
        sessao,
        "insert into plano_contas (company_id, plano_pai_id, codigo, nome, tipo_conta, natureza, nivel) values (:c, :p, '1.01', 'x', 'S', 'R', 2)",
        {"c": outra.id, "p": plano["receita"]["id"]},
    )
    assert "fk_plano_contas_pai" in erro or "conta pai" in erro
