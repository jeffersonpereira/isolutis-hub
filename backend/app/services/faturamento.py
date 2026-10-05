import csv
import io
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import extract, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.datas import adicionar_meses, hoje
from app.domain.dinheiro import ZERO, dividir_em_parcelas
from app.errors import RegraDeNegocio
from app.models import Despesa, Investimento, LancamentoReceita, Negocio, Orcamento
from app.schemas.faturamento import FaturamentoEmLote, LancamentoAtualizar, LancamentoEntrada
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.parceiros import exigir_cliente

ROTULO_TIPO = {
    "projeto": "Projeto sob medida",
    "mensal": "Manutenção mensal",
    "consultoria": "Consultoria",
    "outro": "Outro",
}


def _consulta():
    return select(LancamentoReceita).options(joinedload(LancamentoReceita.cliente))


async def listar(sessao: AsyncSession, ano: int | None = None, mes: int | None = None) -> list[LancamentoReceita]:
    consulta = _consulta().order_by(LancamentoReceita.vencimento, LancamentoReceita.criado_em, LancamentoReceita.id)
    if ano and mes:
        inicio = date(ano, mes, 1)
        fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
        consulta = consulta.where(LancamentoReceita.vencimento >= inicio, LancamentoReceita.vencimento < fim)
    elif ano:
        consulta = consulta.where(
            LancamentoReceita.vencimento >= date(ano, 1, 1), LancamentoReceita.vencimento < date(ano + 1, 1, 1)
        )
    elif mes:
        consulta = consulta.where(extract("month", LancamentoReceita.vencimento) == mes)
    return list((await sessao.scalars(consulta)).all())


async def _recarregar(sessao: AsyncSession, ids: list[UUID]) -> list[LancamentoReceita]:
    consulta = (
        _consulta()
        .where(LancamentoReceita.id.in_(ids))
        .order_by(LancamentoReceita.vencimento, LancamentoReceita.parcela)
    )
    return list((await sessao.scalars(consulta.execution_options(populate_existing=True))).all())


async def _validar_vinculos(
    sessao: AsyncSession, cliente_id: UUID, negocio_id: UUID | None, orcamento_id: UUID | None
) -> None:
    await exigir_cliente(sessao, cliente_id)
    if negocio_id and (await obter(sessao, Negocio, negocio_id, "Negócio")).cliente_id != cliente_id:
        raise RegraDeNegocio("O negócio vinculado pertence a outro cliente.")
    if orcamento_id and (await obter(sessao, Orcamento, orcamento_id, "Orçamento")).cliente_id != cliente_id:
        raise RegraDeNegocio("O orçamento vinculado pertence a outro cliente.")


def _definir_status(lanc: LancamentoReceita, status: str) -> None:
    lanc.status = status
    lanc.recebido_em = (lanc.recebido_em or hoje()) if status == "recebido" else None


def _serie(
    base: dict,
    valores: list[Decimal],
    primeira: date,
    descricao: callable,
    status_primeira: str = "previsto",  # type: ignore[valid-type]
) -> list[LancamentoReceita]:
    n = len(valores)
    grupo = uuid4() if n > 1 else None
    lancamentos = []
    for i, valor in enumerate(valores):
        lanc = LancamentoReceita(
            **base,
            valor=valor,
            vencimento=adicionar_meses(primeira, i),
            descricao=descricao(i + 1, n),
            grupo_id=grupo,
            parcela=i + 1 if grupo else None,
            total_parcelas=n if grupo else None,
        )
        _definir_status(lanc, status_primeira if i == 0 else "previsto")
        lancamentos.append(lanc)
    return lancamentos


def _sufixo(n_atual: int, total: int) -> str:
    return f" · {n_atual}/{total}" if total > 1 else ""


async def criar(sessao: AsyncSession, dados: LancamentoEntrada) -> list[LancamentoReceita]:
    await _validar_vinculos(sessao, dados.cliente_id, dados.negocio_id, dados.orcamento_id)
    base = dados.model_dump(include={"cliente_id", "tipo", "nf", "negocio_id", "orcamento_id"})
    lancs = _serie(
        base, [dados.valor] * dados.repetir, dados.vencimento,
        lambda i, n: dados.descricao + _sufixo(i, n), dados.status,
    )  # fmt: skip
    sessao.add_all(lancs)
    await confirmar(sessao)
    return await _recarregar(sessao, [lanc.id for lanc in lancs])


async def criar_em_lote(sessao: AsyncSession, dados: FaturamentoEmLote) -> list[LancamentoReceita]:
    """Gera, numa única transação, as parcelas do projeto e/ou as mensalidades de uma venda fechada."""
    await _validar_vinculos(sessao, dados.cliente_id, dados.negocio_id, dados.orcamento_id)
    base = {"cliente_id": dados.cliente_id, "negocio_id": dados.negocio_id, "orcamento_id": dados.orcamento_id}
    titulo = dados.titulo
    lancs: list[LancamentoReceita] = []
    if dados.projeto and dados.projeto.valor:
        p = dados.projeto
        lancs += _serie(
            {**base, "tipo": "projeto"}, dividir_em_parcelas(p.valor, p.parcelas), p.primeiro_vencimento,
            lambda i, n: (titulo or "Projeto") + (f" · parcela {i}/{n}" if n > 1 else ""),
        )  # fmt: skip
    if dados.mensal and dados.mensal.valor:
        m = dados.mensal
        lancs += _serie(
            {**base, "tipo": "mensal"}, [m.valor] * m.meses, m.primeira_mensalidade,
            lambda i, n: "Manutenção mensal" + (f" · {titulo}" if titulo else "") + f" · {i}/{n}",
        )  # fmt: skip
    sessao.add_all(lancs)
    await confirmar(sessao)
    return await _recarregar(sessao, [lanc.id for lanc in lancs])


async def atualizar(sessao: AsyncSession, id_: UUID, dados: LancamentoAtualizar) -> LancamentoReceita:
    lanc = await obter(sessao, LancamentoReceita, id_, "Lançamento")
    conferir_versao(lanc, dados.versao)
    if dados.cliente_id != lanc.cliente_id:
        await _validar_vinculos(sessao, dados.cliente_id, lanc.negocio_id, lanc.orcamento_id)
    aplicar(lanc, dados.model_dump(), ignorar=("versao", "status"))
    _definir_status(lanc, dados.status)
    await confirmar(sessao)
    return (await _recarregar(sessao, [id_]))[0]


async def receber(sessao: AsyncSession, id_: UUID) -> LancamentoReceita:
    lanc = await obter(sessao, LancamentoReceita, id_, "Lançamento")
    _definir_status(lanc, "recebido")
    await confirmar(sessao)
    return (await _recarregar(sessao, [id_]))[0]


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    lanc = await obter(sessao, LancamentoReceita, id_, "Lançamento")
    await sessao.delete(lanc)
    await confirmar(sessao)


async def anos_disponiveis(sessao: AsyncSession) -> list[int]:
    """Anos com movimento (receitas, despesas ou investimentos) mais o ano corrente."""
    consultas = [
        select(extract("year", col).label("ano"))
        for col in (LancamentoReceita.vencimento, Despesa.data, Investimento.data)
    ]
    anos = {int(a) for (a,) in (await sessao.execute(union(*consultas))).all()}
    return sorted(anos | {hoje().year})


async def resumo(sessao: AsyncSession, ano: int) -> dict:
    mes = extract("month", LancamentoReceita.vencimento)
    linhas = (
        await sessao.execute(
            select(
                mes.label("mes"),
                func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.status == "recebido"), 0),
                func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.status != "recebido"), 0),
                func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.tipo == "mensal"), 0),
                func.count(),
            )
            .where(LancamentoReceita.vencimento >= date(ano, 1, 1), LancamentoReceita.vencimento < date(ano + 1, 1, 1))
            .group_by(mes)
        )
    ).all()
    por_mes = {int(m): (r, p, rec, n) for m, r, p, rec, n in linhas}
    meses = [
        {"mes": m, "recebido": por_mes.get(m, (ZERO,) * 4)[0], "previsto": por_mes.get(m, (ZERO,) * 4)[1],
         "recorrente": por_mes.get(m, (ZERO,) * 4)[2], "quantidade": por_mes.get(m, (0, 0, 0, 0))[3]}
        for m in range(1, 13)
    ]  # fmt: skip
    return {
        "ano": ano,
        "anos_disponiveis": await anos_disponiveis(sessao),
        "meses": meses,
        "total_recebido": sum((m["recebido"] for m in meses), ZERO),
        "total_previsto": sum((m["previsto"] for m in meses), ZERO),
        "total_recorrente": sum((m["recorrente"] for m in meses), ZERO),
    }


async def exportar_csv(sessao: AsyncSession, ano: int) -> str:
    """Planilha do ano (separador ';', com BOM para o Excel abrir em UTF-8)."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    escritor.writerow(["Data", "Cliente", "Descrição", "Tipo", "Situação", "Valor", "Nota fiscal"])
    for lanc in await listar(sessao, ano):
        escritor.writerow([
            lanc.vencimento.strftime("%d/%m/%Y"), lanc.cliente_nome, lanc.descricao,
            ROTULO_TIPO.get(lanc.tipo, ""), "Recebido" if lanc.status == "recebido" else "Previsto",
            f"{lanc.valor:.2f}".replace(".", ","), lanc.nf or "",
        ])  # fmt: skip
    return "﻿" + saida.getvalue()
