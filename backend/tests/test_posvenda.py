from datetime import date, timedelta

from httpx import AsyncClient

API = "/api/v1"
HOJE = date.today()


async def test_projeto_etapas_progresso_e_um_por_negocio(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    n = (await api.post(f"{API}/negocios", json={"titulo": "Portal", "cliente_id": c["id"]})).json()
    corpo = {
        "titulo": "Portal do cliente",
        "cliente_id": c["id"],
        "negocio_id": n["id"],
        "etapas": [
            {"titulo": "Diagnóstico", "status": "concluida"},
            {"titulo": "Desenvolvimento", "status": "andamento", "inicio": "2026-03-01", "fim": "2026-03-20"},
            {"titulo": "Entrega", "status": "a_fazer"},
        ],
    }
    p = (await api.post(f"{API}/projetos", json=corpo)).json()
    assert p["progresso"] == 33 and [e["ordem"] for e in p["etapas"]] == [1, 2, 3] and p["cliente_nome"] == c["nome"]

    r = await api.post(f"{API}/projetos", json={**corpo, "titulo": "Duplicado"})
    assert r.status_code == 422 and "Já existe um projeto" in r.json()["erro"]["mensagem"]

    # reordena e conclui uma etapa preservando identidade
    ids = [e["id"] for e in p["etapas"]]
    novo = {
        **corpo,
        "versao": p["versao"],
        "etapas": [
            {"id": ids[2], "titulo": "Entrega", "status": "concluida"},
            {"id": ids[0], "titulo": "Diagnóstico", "status": "concluida"},
        ],
    }
    r = await api.put(f"{API}/projetos/{p['id']}", json=novo)
    assert r.status_code == 200, r.text
    assert [e["id"] for e in r.json()["etapas"]] == [ids[2], ids[0]] and r.json()["progresso"] == 100


async def test_validacao_de_datas_da_etapa(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    r = await api.post(
        f"{API}/projetos",
        json={
            "titulo": "P",
            "cliente_id": c["id"],
            "etapas": [{"titulo": "E", "inicio": "2026-05-02", "fim": "2026-05-01"}],
        },
    )
    assert r.status_code == 422


async def test_modelo_do_negocio_e_etapas_padrao(api: AsyncClient, novo_cliente):
    c = await novo_cliente()
    n = (await api.post(f"{API}/negocios", json={"titulo": "Portal", "cliente_id": c["id"]})).json()
    await api.post(
        f"{API}/orcamentos",
        json={
            "cliente_id": c["id"],
            "negocio_id": n["id"],
            "data": HOJE.isoformat(),
            "itens": [
                {"descricao": "Sistema", "preco_unitario": 100},
                {"descricao": "Manutenção", "preco_unitario": 10, "mensal": True},
            ],
        },
    )
    m = (await api.get(f"{API}/projetos/modelo", params={"negocio_id": n["id"]})).json()
    assert (
        m["titulo"] == "Portal"
        and m["escopo"] == "• Sistema"
        and m["orcamento_id"]
        and "hospedagem" in m["pos_entrega"]
    )

    ini, fim = HOJE, HOJE + timedelta(days=60)
    etapas = (
        await api.get(f"{API}/projetos/etapas-padrao", params={"inicio": ini.isoformat(), "entrega": fim.isoformat()})
    ).json()
    assert len(etapas) == 7 and etapas[0]["inicio"] == ini.isoformat()
    assert all(e["fim"] >= e["inicio"] for e in etapas)
    assert all(a["fim"] < b["inicio"] for a, b in zip(etapas, etapas[1:], strict=False))  # sem sobreposição
    assert etapas[2]["titulo"] == "Desenvolvimento"


async def test_relatorio_do_projeto(api: AsyncClient, novo_cliente):
    c = await novo_cliente("Cliente <i>X</i>", contato="Maria")
    corpo = {
        "titulo": "Portal & Cia",
        "cliente_id": c["id"],
        "objetivo": "Reduzir retrabalho",
        "escopo": "• Login\n• Relatórios",
        "fora_escopo": "App móvel",
        "pos_entrega": "Suporte mensal",
        "inicio": "2026-03-01",
        "entrega": "2026-04-30",
        "etapas": [
            {
                "titulo": "Desenvolvimento",
                "status": "andamento",
                "inicio": "2026-03-01",
                "fim": "2026-03-31",
                "entregaveis": "Versão 1\nVersão 2",
            }
        ],
    }
    p = (await api.post(f"{API}/projetos", json=corpo)).json()
    r = await api.get(f"{API}/projetos/{p['id']}/relatorio")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    h = r.text
    assert "Portal &amp; Cia" in h and "Cliente &lt;i&gt;X&lt;/i&gt;" in h
    assert "<i>X</i>" not in h
    assert "O que será entregue" in h and "<li>Login</li>" in h and "Fora do escopo" in h and "Cronograma" in h
    assert "A/C Maria" in h and "Versão 2" in h


async def test_tarefas_kanban_checklist_e_busca(api: AsyncClient, novo_cliente):
    eu = (await api.get(f"{API}/auth/eu")).json()
    t = (
        await api.post(
            f"{API}/tarefas",
            json={
                "titulo": "Enviar proposta revisada",
                "responsavel_id": eu["id"],
                "prioridade": "alta",
                "prazo": HOJE.isoformat(),
                "checklist": [{"texto": "Revisar valores"}, {"texto": "Anexar PDF", "feito": True}],
            },
        )
    ).json()
    assert t["coluna"] == "a_fazer" and t["concluida_em"] is None and [i["ordem"] for i in t["checklist"]] == [1, 2]

    movida = (
        await api.patch(f"{API}/tarefas/{t['id']}/coluna", json={"coluna": "concluido", "versao": t["versao"]})
    ).json()
    assert movida["coluna"] == "concluido" and movida["concluida_em"]
    reaberta = (
        await api.patch(f"{API}/tarefas/{t['id']}/coluna", json={"coluna": "fazendo", "versao": movida["versao"]})
    ).json()
    assert reaberta["concluida_em"] is None

    # edição: marca item do checklist, mantendo ids
    item = reaberta["checklist"][0]
    corpo = {
        "titulo": "Enviar proposta revisada",
        "prioridade": "alta",
        "versao": reaberta["versao"],
        "checklist": [{"id": item["id"], "texto": item["texto"], "feito": True}],
    }
    r = (await api.put(f"{API}/tarefas/{t['id']}", json=corpo)).json()
    assert len(r["checklist"]) == 1 and r["checklist"][0]["feito"] is True and r["responsavel_id"] is None

    # busca sem acento e sem diferença de maiúsculas
    await api.post(f"{API}/tarefas", json={"titulo": "Reunião de diagnóstico"})
    achadas = (await api.get(f"{API}/tarefas", params={"busca": "DIAGNOSTICO"})).json()
    assert [x["titulo"] for x in achadas] == ["Reunião de diagnóstico"]

    # ordenação: prioridade alta antes de baixa dentro da coluna
    await api.post(f"{API}/tarefas", json={"titulo": "Baixa", "prioridade": "baixa"})
    await api.post(f"{API}/tarefas", json={"titulo": "Alta", "prioridade": "alta"})
    a_fazer = [x["titulo"] for x in (await api.get(f"{API}/tarefas")).json() if x["coluna"] == "a_fazer"]
    assert a_fazer.index("Alta") < a_fazer.index("Baixa")

    assert (await api.delete(f"{API}/tarefas/{t['id']}")).status_code == 204


async def test_painel(api: AsyncClient, novo_cliente):
    vazio = (await api.get(f"{API}/painel")).json()
    assert vazio["banco_vazio"] is True and vazio["conversao_pct"] is None and len(vazio["serie"]) == 12

    c = await novo_cliente()
    for titulo, etapa, valor, mensal, previsao in [
        ("A", "lead", 1000, 100, (HOJE + timedelta(days=5)).isoformat()),
        ("B", "proposta", 2000, 0, (HOJE - timedelta(days=2)).isoformat()),
    ]:
        await api.post(
            f"{API}/negocios",
            json={
                "titulo": titulo,
                "cliente_id": c["id"],
                "etapa": etapa,
                "valor": valor,
                "mensal": mensal,
                "previsao": previsao,
            },
        )
    g = (await api.post(f"{API}/negocios", json={"titulo": "G", "cliente_id": c["id"], "etapa": "ganho"})).json()
    await api.post(
        f"{API}/negocios", json={"titulo": "P", "cliente_id": c["id"], "etapa": "perdido", "motivo_perda": "Preço"}
    )
    assert g["etapa"] == "ganho"
    await api.post(
        f"{API}/faturamento",
        json={
            "cliente_id": c["id"],
            "tipo": "mensal",
            "descricao": "m",
            "valor": 300,
            "vencimento": HOJE.isoformat(),
            "status": "recebido",
        },
    )
    await api.post(
        f"{API}/faturamento",
        json={"cliente_id": c["id"], "tipo": "projeto", "descricao": "p", "valor": 700, "vencimento": HOJE.isoformat()},
    )
    await api.post(
        f"{API}/orcamentos",
        json={
            "cliente_id": c["id"],
            "data": HOJE.isoformat(),
            "status": "enviado",
            "itens": [{"descricao": "x", "preco_unitario": 900}],
        },
    )

    p = (await api.get(f"{API}/painel")).json()
    assert p["banco_vazio"] is False
    assert (p["recebido_no_mes"], p["previsto_no_mes"], p["recorrente_no_mes"]) == (300, 1000, 300)
    assert (p["funil_abertos"], p["funil_valor"], p["funil_mensal"]) == (2, 3000, 100)
    assert (p["ganhos"], p["perdidos"], p["conversao_pct"]) == (1, 1, 50)
    assert (p["orcamentos_aguardando_qtd"], p["orcamentos_aguardando_valor"]) == (1, 900)
    assert p["serie"][-1] == {"ano": HOJE.year, "mes": HOJE.month, "recebido": 300, "previsto": 700}
    por_etapa = {e["etapa"]: e for e in p["por_etapa"]}
    assert por_etapa["lead"]["valor"] == 1000 + 12 * 100 and por_etapa["proposta"]["quantidade"] == 1
    assert [x["titulo"] for x in p["proximos_fechamentos"]] == ["B", "A"]  # ordenados por previsão
