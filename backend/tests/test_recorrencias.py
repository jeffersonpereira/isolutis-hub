"""Recorrência de títulos (PostgreSQL real): geração, término, edição, pausa, encerramento e job de renovação."""

from contextlib import asynccontextmanager
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.datas import hoje
from app.financeiro import recorrencias
from app.financeiro.models import InstituicaoFinanceira

F = "/api/v1/financeiro"
P = "/api/v1/parceiros"


class _Fabrica:
    """Entrega a sessão do teste (uma transação desfeita no fim) no lugar de abrir sessões novas."""

    def __init__(self, sessao: AsyncSession) -> None:
        self._sessao = sessao

    @asynccontextmanager
    async def __call__(self):  # noqa: ANN204
        yield self._sessao


async def _criar(api: AsyncClient, caminho: str, corpo: dict, esperado: int = 201) -> dict:
    r = await api.post(f"{F}{caminho}", json=corpo)
    assert r.status_code == esperado, r.text
    return r.json()


async def _titulos(api: AsyncClient, rec_id: str) -> list[dict]:
    todos = (await api.get(f"{F}/titulos", params={"tamanho": 100})).json()["itens"]
    return sorted((t for t in todos if t["recorrencia_id"] == rec_id), key=lambda t: t["data_vencimento"])


@pytest.fixture
async def base(api: AsyncClient, sessao: AsyncSession) -> dict:
    banco = InstituicaoFinanceira(codigo="001", nome="Banco do Brasil S.A.")
    sessao.add(banco)
    await sessao.flush()
    rec = await _criar(api, "/plano-contas", {"codigo": "1", "nome": "Receita", "tipo_conta": "S", "natureza": "R"})
    rec1 = await _criar(
        api, "/plano-contas", {"plano_pai_id": rec["id"], "codigo": "1.01", "nome": "Serviços", "tipo_conta": "S"}
    )
    mensalidade = await _criar(
        api,
        "/plano-contas",
        {"plano_pai_id": rec1["id"], "codigo": "1.01.001", "nome": "Mensalidade", "tipo_conta": "A"},
    )
    desp = await _criar(api, "/plano-contas", {"codigo": "2", "nome": "Despesa", "tipo_conta": "S", "natureza": "D"})
    desp1 = await _criar(
        api, "/plano-contas", {"plano_pai_id": desp["id"], "codigo": "2.01", "nome": "Estrutura", "tipo_conta": "S"}
    )
    aluguel = await _criar(
        api, "/plano-contas", {"plano_pai_id": desp1["id"], "codigo": "2.01.001", "nome": "Aluguel", "tipo_conta": "A"}
    )
    conta = await _criar(
        api, "/contas-bancarias", {"instituicao_financeira_id": str(banco.id), "nome": "Principal", "saldo_inicial": 0}
    )
    fornecedor = (await api.post(P, json={"nome": "Imobiliária", "papeis": ["fornecedor"]})).json()
    cliente = (await api.post(P, json={"nome": "Cliente Alfa", "papeis": ["cliente"]})).json()
    return {
        "mensalidade": mensalidade,
        "aluguel": aluguel,
        "conta": conta,
        "fornecedor": fornecedor,
        "cliente": cliente,
    }


def _despesa(base: dict, **extra) -> dict:
    return {
        "tipo_conta": "P", "conta_bancaria_id": base["conta"]["id"], "plano_conta_id": base["aluguel"]["id"],
        "parceiro_id": base["fornecedor"]["id"], "valor_titulo": 3000, "frequencia": "mensal",
        "data_inicio": str(hoje() + timedelta(days=1)), "termino": "quantidade", "quantidade": 12, **extra,
    }  # fmt: skip


async def test_cria_a_recorrencia_e_gera_todos_os_titulos(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base))
    assert rec["titulos_gerados"] == 12 and rec["titulos_abertos"] == 12 and rec["ativa"] is True
    titulos = await _titulos(api, rec["id"])
    assert (
        len(titulos) == 12
        and {t["tipo_conta"] for t in titulos} == {"P"}
        and {t["valor_titulo"] for t in titulos} == {3000}
    )
    assert titulos[0]["data_vencimento"] == rec["data_inicio"]


async def test_receita_recorrente(api: AsyncClient, base: dict):
    corpo = _despesa(
        base, tipo_conta="R", plano_conta_id=base["mensalidade"]["id"], parceiro_id=base["cliente"]["id"], quantidade=3
    )
    rec = await _criar(api, "/recorrencias", corpo)
    assert {t["tipo_conta"] for t in await _titulos(api, rec["id"])} == {"R"}


async def test_termino_por_data_final(api: AsyncClient, base: dict):
    inicio = hoje() + timedelta(days=1)
    fim = inicio + timedelta(days=100)
    rec = await _criar(api, "/recorrencias", _despesa(base, termino="data", data_fim=str(fim), quantidade=None))
    assert all(t["data_vencimento"] <= str(fim) for t in await _titulos(api, rec["id"]))


async def test_sem_fim_gera_ate_o_horizonte_e_o_job_nao_duplica(api: AsyncClient, base: dict, sessao: AsyncSession):
    rec = await _criar(api, "/recorrencias", _despesa(base, termino="sem_fim", quantidade=None))
    antes = len(await _titulos(api, rec["id"]))
    assert 12 <= antes <= 13
    fabrica = _Fabrica(sessao)
    assert await recorrencias.renovar_horizonte(fabrica) == 0
    assert await recorrencias.renovar_horizonte(fabrica) == 0
    assert len(await _titulos(api, rec["id"])) == antes


async def test_titulo_apagado_a_mao_nao_reaparece(api: AsyncClient, base: dict, sessao: AsyncSession):
    rec = await _criar(api, "/recorrencias", _despesa(base, termino="sem_fim", quantidade=None))
    segundo = (await _titulos(api, rec["id"]))[1]
    assert (await api.delete(f"{F}/titulos/{segundo['id']}")).status_code == 204
    await recorrencias.renovar_horizonte(_Fabrica(sessao))
    assert segundo["id"] not in {t["id"] for t in await _titulos(api, rec["id"])}


async def test_editar_um_titulo_nao_muda_o_modelo(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=3))
    t = (await _titulos(api, rec["id"]))[0]
    corpo = {
        k: t[k]
        for k in (
            "tipo_conta",
            "conta_bancaria_id",
            "plano_conta_id",
            "parceiro_id",
            "data_vencimento",
            "data_emissao",
            "anotacao",
        )
    }
    r = await api.put(f"{F}/titulos/{t['id']}", json={**corpo, "valor_titulo": 9999})
    assert r.status_code == 200 and r.json()["recorrencia_id"] == rec["id"]
    outros = (await _titulos(api, rec["id"]))[1:]
    assert {x["valor_titulo"] for x in outros} == {3000}


def _corpo_de_atualizacao(base: dict, **extra) -> dict:
    return {
        "conta_bancaria_id": base["conta"]["id"], "plano_conta_id": base["aluguel"]["id"],
        "parceiro_id": base["fornecedor"]["id"], "valor_titulo": 3000,
        "termino": "quantidade", "quantidade": 12, **extra,
    }  # fmt: skip


async def test_reajuste_so_atinge_titulos_futuros_em_aberto(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=4))
    primeiro = (await _titulos(api, rec["id"]))[0]
    corpo = {
        k: primeiro[k]
        for k in ("tipo_conta", "conta_bancaria_id", "plano_conta_id", "parceiro_id", "data_vencimento", "valor_titulo")
    }
    pago = await api.put(f"{F}/titulos/{primeiro['id']}", json={**corpo, "status": "Q", "data_pagamento": str(hoje())})
    assert pago.status_code == 200, pago.text
    r = await api.put(
        f"{F}/recorrencias/{rec['id']}", json=_corpo_de_atualizacao(base, valor_titulo=3500, quantidade=4)
    )
    assert r.status_code == 200 and r.json()["valor_titulo"] == 3500
    titulos = await _titulos(api, rec["id"])
    assert titulos[0]["status"] == "Q" and titulos[0]["valor_titulo"] == 3000  # o quitado não muda
    assert {t["valor_titulo"] for t in titulos[1:]} == {3500}


async def test_reduzir_o_termino_remove_os_titulos_que_sobram(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=6))
    r = await api.put(f"{F}/recorrencias/{rec['id']}", json=_corpo_de_atualizacao(base, quantidade=2))
    assert r.status_code == 200 and len(await _titulos(api, rec["id"])) == 2


async def test_ampliar_o_termino_gera_os_que_faltam(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=2))
    await api.put(f"{F}/recorrencias/{rec['id']}", json=_corpo_de_atualizacao(base, quantidade=5))
    assert len(await _titulos(api, rec["id"])) == 5


async def test_pausar_nao_gera_e_retomar_nao_cria_o_passado(api: AsyncClient, base: dict, sessao: AsyncSession):
    rec = await _criar(api, "/recorrencias", _despesa(base, termino="sem_fim", quantidade=None))
    antes = len(await _titulos(api, rec["id"]))
    pausada = (await api.post(f"{F}/recorrencias/{rec['id']}/pausar")).json()
    assert pausada["ativa"] is False
    await recorrencias.renovar_horizonte(_Fabrica(sessao))  # o job ignora recorrência pausada
    assert len(await _titulos(api, rec["id"])) == antes
    retomada = (await api.post(f"{F}/recorrencias/{rec['id']}/retomar")).json()
    assert retomada["ativa"] is True and len(await _titulos(api, rec["id"])) == antes


async def test_encerrar_remove_so_os_futuros_em_aberto(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=3))
    primeiro = (await _titulos(api, rec["id"]))[0]
    corpo = {
        k: primeiro[k]
        for k in ("tipo_conta", "conta_bancaria_id", "plano_conta_id", "parceiro_id", "data_vencimento", "valor_titulo")
    }
    await api.put(f"{F}/titulos/{primeiro['id']}", json={**corpo, "status": "Q", "data_pagamento": str(hoje())})
    encerrada = (await api.post(f"{F}/recorrencias/{rec['id']}/encerrar")).json()
    assert encerrada["ativa"] is False and encerrada["encerrada_em"]
    restantes = await _titulos(api, rec["id"])
    assert [t["status"] for t in restantes] == ["Q"]
    # encerrada não se edita, pausa nem retoma
    assert (await api.put(f"{F}/recorrencias/{rec['id']}", json=_corpo_de_atualizacao(base))).status_code == 422
    assert (await api.post(f"{F}/recorrencias/{rec['id']}/retomar")).status_code == 422


@pytest.mark.parametrize(
    "extra",
    [
        {"termino": "data", "quantidade": None},  # falta a data final
        {"termino": "sem_fim"},  # sem_fim com quantidade
        {"termino": "quantidade", "quantidade": None},
        {"termino": "quantidade", "data_fim": "2099-01-01"},  # duas formas de término
        {"valor_titulo": 0},
        {"frequencia": "diaria"},
    ],
)
async def test_cadastro_invalido_e_recusado(api: AsyncClient, base: dict, extra: dict):
    r = await api.post(f"{F}/recorrencias", json=_despesa(base, **extra))
    assert r.status_code == 422


async def test_data_final_antes_do_inicio_e_recusada(api: AsyncClient, base: dict):
    corpo = _despesa(base, termino="data", data_fim=str(hoje() - timedelta(days=5)), quantidade=None)
    assert (await api.post(f"{F}/recorrencias", json=corpo)).status_code == 422


async def test_aplica_as_regras_de_titulo_ao_modelo(api: AsyncClient, base: dict):
    # a pagar para quem é só cliente
    r = await api.post(f"{F}/recorrencias", json=_despesa(base, parceiro_id=base["cliente"]["id"]))
    assert r.status_code == 422 and "fornecedor" in r.json()["erro"]["mensagem"]
    # a pagar numa conta de receita (RN04)
    r = await api.post(f"{F}/recorrencias", json=_despesa(base, plano_conta_id=base["mensalidade"]["id"]))
    assert r.status_code == 422


async def test_recusa_recorrencia_que_geraria_titulos_demais(api: AsyncClient, base: dict):
    corpo = _despesa(base, frequencia="semanal", data_inicio="1990-01-01", termino="sem_fim", quantidade=None)
    r = await api.post(f"{F}/recorrencias", json=corpo)
    assert r.status_code == 422 and "600" in r.json()["erro"]["mensagem"]


async def test_recorrencia_de_outra_empresa_nao_e_visivel(api: AsyncClient, base: dict):
    rec = await _criar(api, "/recorrencias", _despesa(base, quantidade=2))
    api.headers["X-Empresa-ID"] = "00000000-0000-4000-8000-00000000dead"
    assert (await api.put(f"{F}/recorrencias/{rec['id']}", json=_corpo_de_atualizacao(base))).status_code == 403
