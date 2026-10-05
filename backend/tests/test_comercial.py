from datetime import date, timedelta

from httpx import AsyncClient

API = "/api/v1"
HOJE = date.today()


async def test_cliente_crud_cnpj_e_exclusao(api: AsyncClient, novo_cliente):
    c = await novo_cliente("Alfa Ltda", cpf_cnpj="11.222.333/0001-81", telefone="(71) 99239-0992")
    assert (
        c["cpf_cnpj"] == "11222333000181"
        and c["papeis"] == ["cliente"]
        and c["tipo_pessoa"] == "PJ"
        and c["versao"] == 1
        and c["criado_por"]
    )

    # CNPJ inválido e duplicado
    r = await api.post(f"{API}/clientes", json={"nome": "X", "cpf_cnpj": "123"})
    assert r.status_code == 422 and "CNPJ inválido" in r.json()["erro"]["mensagem"]
    r = await api.post(f"{API}/clientes", json={"nome": "Y", "cpf_cnpj": "11222333000181"})
    assert r.status_code == 422 and "CNPJ" in r.json()["erro"]["mensagem"]

    r = await api.put(
        f"{API}/clientes/{c['id']}", json={"nome": "Alfa S.A.", "versao": c["versao"], "cargo": "Diretora"}
    )
    assert (
        r.status_code == 200
        and r.json()["versao"] == 2
        and r.json()["cpf_cnpj"] is None
        and r.json()["papeis"] == ["cliente"]
    )

    lista = (await api.get(f"{API}/clientes")).json()
    assert lista[0]["nome"] == "Alfa S.A." and lista[0]["negocios_abertos"] == 0 and lista[0]["faturado"] == 0

    assert (await api.delete(f"{API}/clientes/{c['id']}")).status_code == 204
    assert (await api.delete(f"{API}/clientes/{c['id']}")).status_code == 404


async def test_edicao_concorrente_devolve_409(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    ok = await api.put(f"{API}/clientes/{c['id']}", json={"nome": "Primeira edição", "versao": 1})
    assert ok.status_code == 200
    velha = await api.put(f"{API}/clientes/{c['id']}", json={"nome": "Edição atrasada", "versao": 1})
    assert velha.status_code == 409 and velha.json()["erro"]["codigo"] == "conflito"


async def test_cliente_com_negocio_nao_pode_ser_excluido(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    await api.post(f"{API}/negocios", json={"titulo": "Portal", "cliente_id": c["id"]})
    r = await api.delete(f"{API}/clientes/{c['id']}")
    assert r.status_code == 422 and "Exclua esses registros" in r.json()["erro"]["mensagem"]


async def test_funil_regras_de_etapa(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    n = (await api.post(f"{API}/negocios", json={"titulo": "Portal", "cliente_id": c["id"], "valor": 10000})).json()
    assert n["etapa"] == "lead" and n["fechado_em"] is None and n["faturado"] is False

    # perdido exige motivo (no payload e na mudança de etapa)
    r = await api.put(
        f"{API}/negocios/{n['id']}", json={"titulo": "Portal", "cliente_id": c["id"], "etapa": "perdido", "versao": 1}
    )
    assert r.status_code == 422
    r = await api.patch(f"{API}/negocios/{n['id']}/etapa", json={"etapa": "perdido", "versao": 1})
    assert r.status_code == 422

    ganho = (await api.patch(f"{API}/negocios/{n['id']}/etapa", json={"etapa": "ganho", "versao": 1})).json()
    assert ganho["fechado_em"] == HOJE.isoformat()
    perdido = await api.patch(
        f"{API}/negocios/{n['id']}/etapa", json={"etapa": "perdido", "motivo_perda": "Preço", "versao": ganho["versao"]}
    )
    assert perdido.json()["fechado_em"] is None and perdido.json()["motivo_perda"] == "Preço"
    reaberto = await api.patch(
        f"{API}/negocios/{n['id']}/etapa", json={"etapa": "negociacao", "versao": perdido.json()["versao"]}
    )
    assert reaberto.json()["motivo_perda"] is None


async def test_nao_troca_cliente_do_negocio(api: AsyncClient, novo_cliente):
    a, b = await novo_cliente("A"), await novo_cliente("B")
    n = (await api.post(f"{API}/negocios", json={"titulo": "X", "cliente_id": a["id"]})).json()
    r = await api.put(f"{API}/negocios/{n['id']}", json={"titulo": "X", "cliente_id": b["id"], "versao": 1})
    assert r.status_code == 422


def _orc(cliente_id: str, **extra) -> dict:
    return {
        "cliente_id": cliente_id,
        "data": HOJE.isoformat(),
        "itens": [
            {"descricao": "Sistema sob medida", "qtd": 1, "preco_unitario": 10000},
            {"descricao": "Treinamento", "qtd": 2, "preco_unitario": 500.5},
            {"descricao": "Manutenção", "qtd": 1, "preco_unitario": 800, "mensal": True},
        ],
        **extra,
    }


async def test_orcamento_numeracao_totais_e_itens(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    o1 = (await api.post(f"{API}/orcamentos", json=_orc(c["id"], desconto=1000))).json()
    o2 = (await api.post(f"{API}/orcamentos", json=_orc(c["id"]))).json()
    ano = HOJE.year
    assert (o1["numero"], o2["numero"]) == (f"{ano}-001", f"{ano}-002")
    assert o1["total_projeto"] == 10001.0 and o1["total_mensal"] == 800.0
    assert [i["subtotal"] for i in o1["itens"]] == [10000.0, 1001.0, 800.0]

    # lista: mais recente primeiro
    assert [o["numero"] for o in (await api.get(f"{API}/orcamentos")).json()] == [o2["numero"], o1["numero"]]

    # edita: mantém um item (por id), remove os outros, adiciona um novo, reordena
    primeiro = o1["itens"][0]
    corpo = _orc(c["id"], versao=o1["versao"])
    corpo["itens"] = [
        {"descricao": "Item novo", "qtd": 3, "preco_unitario": 100},
        {"id": primeiro["id"], "descricao": primeiro["descricao"], "qtd": 1, "preco_unitario": 12000},
    ]
    r = await api.put(f"{API}/orcamentos/{o1['id']}", json=corpo)
    assert r.status_code == 200, r.text
    editado = r.json()
    assert [i["descricao"] for i in editado["itens"]] == ["Item novo", "Sistema sob medida"]
    assert editado["itens"][1]["id"] == primeiro["id"]  # identidade preservada
    assert editado["total_projeto"] == 12300.0 and editado["total_mensal"] == 0.0
    assert editado["numero"] == o1["numero"]  # número é imutável


async def test_orcamento_validacoes(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    assert (await api.post(f"{API}/orcamentos", json=_orc(c["id"], desconto=999999))).status_code == 422
    assert (await api.post(f"{API}/orcamentos", json={**_orc(c["id"]), "itens": []})).status_code == 422
    outro = await novo_cliente("Outro")
    n = (await api.post(f"{API}/negocios", json={"titulo": "X", "cliente_id": outro["id"]})).json()
    r = await api.post(f"{API}/orcamentos", json=_orc(c["id"], negocio_id=n["id"]))
    assert r.status_code == 422 and "outro cliente" in r.json()["erro"]["mensagem"]


async def test_orcamento_vencido_e_derivado(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    antigo = (HOJE - timedelta(days=40)).isoformat()
    o = (
        await api.post(f"{API}/orcamentos", json=_orc(c["id"], data=antigo, status="enviado", validade_dias=15))
    ).json()
    assert o["status"] == "enviado" and o["status_exibido"] == "vencido"
    assert [x["id"] for x in (await api.get(f"{API}/orcamentos", params={"status": "vencido"})).json()] == [o["id"]]


async def test_enviar_orcamento_avanca_o_negocio_e_aprovar_ganha(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    n = (await api.post(f"{API}/negocios", json={"titulo": "Portal", "cliente_id": c["id"]})).json()
    o = (await api.post(f"{API}/orcamentos", json=_orc(c["id"], negocio_id=n["id"], status="enviado"))).json()
    negs = (await api.get(f"{API}/negocios")).json()
    assert negs[0]["etapa"] == "proposta"

    r = await api.post(f"{API}/orcamentos/{o['id']}/aprovar")
    assert r.status_code == 200
    assert r.json()["orcamento"]["status"] == "aprovado" and r.json()["orcamento"]["aprovado_em"] == HOJE.isoformat()
    n2 = (await api.get(f"{API}/negocios")).json()[0]
    assert (
        n2["etapa"] == "ganho"
        and n2["valor"] == 11001.0
        and n2["mensal"] == 800.0
        and n2["fechado_em"] == HOJE.isoformat()
    )


async def test_documento_do_orcamento_escapa_html(api: AsyncClient, novo_cliente):
    c = await novo_cliente("<script>alert(1)</script> Ltda")
    o = (await api.post(f"{API}/orcamentos", json=_orc(c["id"], obs="Pagamento <b>à vista</b>"))).json()
    r = await api.get(f"{API}/orcamentos/{o['id']}/documento")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    html = r.text
    assert "<script>alert(1)" not in html and "&lt;script&gt;" in html
    assert "&lt;b&gt;à vista" in html
    assert "R$ 10.000,00" in html and "(mensal)" in html and f"Orçamento Nº {o['numero']}" in html


async def test_produtos_e_catalogo(api: AsyncClient):
    r = await api.post(
        f"{API}/produtos", json={"nome": "Consultoria", "tipo": "consultoria", "unidade": "hora", "preco": 350}
    )
    assert r.status_code == 201 and r.json()["preco"] == 350
    cat = await api.post(f"{API}/produtos/catalogo")
    assert cat.status_code == 201 and len(cat.json()) == 8
    p = r.json()
    r = await api.put(
        f"{API}/produtos/{p['id']}",
        json={"nome": "Consultoria", "tipo": "consultoria", "unidade": "hora", "preco": 400, "versao": 1},
    )
    assert r.json()["preco"] == 400
    assert (await api.post(f"{API}/produtos", json={"nome": "x", "tipo": "invalido"})).status_code == 422


async def test_campos_opcionais_aceitam_null_explicito(api: AsyncClient, novo_cliente):
    """O frontend envia `null` (não omite) nos campos vazios: nenhum schema pode quebrar com isso."""
    r = await api.post(
        f"{API}/clientes",
        json={
            k: None
            for k in (
                "cpf_cnpj",
                "segmento",
                "contato",
                "cargo",
                "telefone",
                "email",
                "endereco",
                "cep",
                "municipio_id",
                "origem",
                "obs",
            )
        }
        | {"nome": "Nulos"},
    )
    assert r.status_code == 201, r.text
    c = r.json()
    n = await api.post(
        f"{API}/negocios",
        json={
            "titulo": "N",
            "cliente_id": c["id"],
            "previsao": None,
            "responsavel_id": None,
            "origem": None,
            "motivo_perda": None,
            "obs": None,
        },
    )
    assert n.status_code == 201, n.text
    o = await api.post(
        f"{API}/orcamentos",
        json={
            "cliente_id": c["id"],
            "negocio_id": None,
            "data": HOJE.isoformat(),
            "obs": None,
            "itens": [{"id": None, "produto_id": None, "descricao": "x", "preco_unitario": 1}],
        },
    )
    assert o.status_code == 201, o.text
    p = await api.post(
        f"{API}/projetos",
        json={
            "titulo": "P",
            "cliente_id": c["id"],
            "negocio_id": None,
            "objetivo": None,
            "escopo": None,
            "etapas": [
                {
                    "id": None,
                    "titulo": "E",
                    "inicio": None,
                    "fim": None,
                    "descricao": None,
                    "entregaveis": None,
                    "responsavel_id": None,
                }
            ],
        },
    )
    assert p.status_code == 201, p.text
    t = await api.post(
        f"{API}/tarefas",
        json={
            "titulo": "T",
            "descricao": None,
            "prazo": None,
            "cliente_id": None,
            "checklist": [{"id": None, "texto": "x"}],
        },
    )
    assert t.status_code == 201, t.text
    f = await api.post(
        f"{API}/faturamento",
        json={
            "cliente_id": c["id"],
            "tipo": "projeto",
            "descricao": "d",
            "valor": 1,
            "vencimento": HOJE.isoformat(),
            "nf": None,
        },
    )
    assert f.status_code == 201, f.text
    cat = (await api.get(f"{API}/despesas/opcoes")).json()["categorias"][0]["id"]
    d = await api.post(
        f"{API}/despesas",
        json={
            "data": HOJE.isoformat(),
            "descricao": "d",
            "valor": 1,
            "categoria_id": cat,
            "fornecedor": None,
            "obs": None,
        },
    )
    assert d.status_code == 201, d.text
