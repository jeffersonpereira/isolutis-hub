from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.datas import adicionar_meses, hoje
from app.domain.dinheiro import ZERO
from app.models import CategoriaDespesa, Despesa, Investidor, Investimento, LancamentoReceita
from app.schemas.despesa import (
    DespesaAtualizar,
    DespesaEntrada,
    InvestimentoAtualizar,
    InvestimentoEntrada,
)
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.faturamento import anos_disponiveis


def _ano(coluna, ano: int | None):  # noqa: ANN001
    return (coluna >= date(ano, 1, 1)) & (coluna < date(ano + 1, 1, 1))


# ----------------------------------------------------------------------------- despesas
async def listar(sessao: AsyncSession, ano: int | None = None, mes: int | None = None) -> list[Despesa]:
    consulta = select(Despesa).options(joinedload(Despesa.categoria)).order_by(Despesa.data, Despesa.criado_em, Despesa.id)
    if ano:
        if mes:
            inicio = date(ano, mes, 1)
            fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
            consulta = consulta.where(Despesa.data >= inicio, Despesa.data < fim)
        else:
            consulta = consulta.where(_ano(Despesa.data, ano))
    if mes:
        if not ano:
            consulta = consulta.where(extract("month", Despesa.data) == mes)
    return list((await sessao.scalars(consulta)).all())


async def _recarregar(sessao: AsyncSession, ids: list[UUID]) -> list[Despesa]:
    consulta = select(Despesa).options(joinedload(Despesa.categoria)).where(Despesa.id.in_(ids)).order_by(Despesa.data)
    return list((await sessao.scalars(consulta.execution_options(populate_existing=True))).all())


def _definir_status(d: Despesa, status: str, pago_em: date) -> None:
    d.status = status
    d.pago_em = (d.pago_em or pago_em) if status == "pago" else None


async def criar(sessao: AsyncSession, dados: DespesaEntrada) -> list[Despesa]:
    await obter(sessao, CategoriaDespesa, dados.categoria_id, "Categoria")
    n = dados.repetir
    grupo = uuid4() if n > 1 else None
    campos = dados.model_dump(exclude={"repetir", "status", "data", "descricao"})
    despesas = []
    for i in range(n):
        data = adicionar_meses(dados.data, i)
        d = Despesa(
            **campos,
            data=data,
            descricao=dados.descricao + (f" · {i + 1}/{n}" if n > 1 else ""),
            grupo_id=grupo,
            parcela=i + 1 if grupo else None,
            total_parcelas=n if grupo else None,
        )
        _definir_status(d, dados.status if i == 0 else "a_pagar", data)
        despesas.append(d)
    sessao.add_all(despesas)
    await confirmar(sessao)
    return await _recarregar(sessao, [d.id for d in despesas])


async def atualizar(sessao: AsyncSession, id_: UUID, dados: DespesaAtualizar) -> Despesa:
    d = await obter(sessao, Despesa, id_, "Despesa")
    conferir_versao(d, dados.versao)
    await obter(sessao, CategoriaDespesa, dados.categoria_id, "Categoria")
    aplicar(d, dados.model_dump(), ignorar=("versao", "status"))
    _definir_status(d, dados.status, hoje())
    await confirmar(sessao)
    return (await _recarregar(sessao, [id_]))[0]


async def pagar(sessao: AsyncSession, id_: UUID) -> Despesa:
    d = await obter(sessao, Despesa, id_, "Despesa")
    _definir_status(d, "pago", hoje())
    await confirmar(sessao)
    return (await _recarregar(sessao, [id_]))[0]


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    await sessao.delete(await obter(sessao, Despesa, id_, "Despesa"))
    await confirmar(sessao)


# ----------------------------------------------------------------------------- investimentos
async def listar_investimentos(sessao: AsyncSession, ano: int | None = None) -> list[Investimento]:
    consulta = select(Investimento).options(joinedload(Investimento.investidor)).order_by(Investimento.data)
    if ano:
        consulta = consulta.where(_ano(Investimento.data, ano))
    return list((await sessao.scalars(consulta)).all())


async def _investidor_por_nome(sessao: AsyncSession, nome: str) -> Investidor:
    investidor = await sessao.scalar(select(Investidor).where(Investidor.nome == nome))
    if investidor is None:
        investidor = Investidor(nome=nome)
        sessao.add(investidor)
        await sessao.flush()
    return investidor


async def _investimento_completo(sessao: AsyncSession, id_: UUID) -> Investimento:
    consulta = select(Investimento).options(joinedload(Investimento.investidor)).where(Investimento.id == id_)
    return (await sessao.scalars(consulta.execution_options(populate_existing=True))).one()


async def criar_investimento(sessao: AsyncSession, dados: InvestimentoEntrada) -> Investimento:
    investidor = await _investidor_por_nome(sessao, dados.investidor)
    inv = Investimento(**dados.model_dump(exclude={"investidor"}), investidor_id=investidor.id)
    sessao.add(inv)
    await confirmar(sessao)
    return await _investimento_completo(sessao, inv.id)


async def atualizar_investimento(sessao: AsyncSession, id_: UUID, dados: InvestimentoAtualizar) -> Investimento:
    inv = await obter(sessao, Investimento, id_, "Investimento")
    conferir_versao(inv, dados.versao)
    investidor = await _investidor_por_nome(sessao, dados.investidor)
    aplicar(inv, dados.model_dump(), ignorar=("versao", "investidor"))
    inv.investidor_id = investidor.id
    await confirmar(sessao)
    return await _investimento_completo(sessao, id_)


async def excluir_investimento(sessao: AsyncSession, id_: UUID) -> None:
    await sessao.delete(await obter(sessao, Investimento, id_, "Investimento"))
    await confirmar(sessao)


# ----------------------------------------------------------------------------- opções e resumo
async def opcoes(sessao: AsyncSession) -> dict:
    categorias = (
        await sessao.scalars(select(CategoriaDespesa).where(CategoriaDespesa.ativo).order_by(CategoriaDespesa.ordem))
    ).all()
    investidores = (
        await sessao.scalars(select(Investidor.nome).where(Investidor.ativo).order_by(Investidor.nome))
    ).all()
    fornecedores = (
        await sessao.scalars(
            select(Despesa.fornecedor).where(Despesa.fornecedor.is_not(None)).distinct().order_by(Despesa.fornecedor)
        )
    ).all()
    return {
        "categorias": categorias,
        "investidores": [str(n) for n in investidores],
        "fornecedores": list(fornecedores),
    }


async def resumo(sessao: AsyncSession, ano: int) -> dict:
    """Recebido x despesas x investimentos do ano. Resultado = recebido menos despesas PAGAS."""

    async def por_mes(coluna_data, valor, *filtros) -> dict[int, object]:  # noqa: ANN001
        mes = extract("month", coluna_data)
        linhas = await sessao.execute(
            select(mes, func.coalesce(func.sum(valor), 0)).where(_ano(coluna_data, ano), *filtros).group_by(mes)
        )
        return {int(m): v for m, v in linhas.all()}

    recebido = await por_mes(
        LancamentoReceita.vencimento, LancamentoReceita.valor, LancamentoReceita.status == "recebido"
    )
    despesas = await por_mes(Despesa.data, Despesa.valor)
    investimentos = await por_mes(Investimento.data, Investimento.valor)
    pagas = await sessao.scalar(
        select(func.coalesce(func.sum(Despesa.valor), 0)).where(_ano(Despesa.data, ano), Despesa.status == "pago")
    )
    a_pagar = await sessao.scalar(
        select(func.coalesce(func.sum(Despesa.valor), 0)).where(_ano(Despesa.data, ano), Despesa.status == "a_pagar")
    )
    recebido_ano = sum(recebido.values(), ZERO)
    investido_ano = sum(investimentos.values(), ZERO)
    meses = []
    for m in range(1, 13):
        r, dp, iv = recebido.get(m, ZERO), despesas.get(m, ZERO), investimentos.get(m, ZERO)
        meses.append({"mes": m, "recebido": r, "despesas": dp, "resultado": r - dp, "investimentos": iv})

    linhas = await sessao.execute(
        select(
            Investidor.nome,
            func.coalesce(func.sum(Investimento.valor), 0),
            func.coalesce(func.sum(Investimento.valor).filter(_ano(Investimento.data, ano)), 0),
        )
        .join(Investimento, Investimento.investidor_id == Investidor.id)
        .group_by(Investidor.nome)
    )
    por_pessoa = sorted(linhas.all(), key=lambda x: x[1], reverse=True)
    investido_total = sum((t for _, t, _ in por_pessoa), ZERO)
    return {
        "ano": ano,
        "anos_disponiveis": await anos_disponiveis(sessao),
        "recebido_no_ano": recebido_ano,
        "despesas_pagas": pagas,
        "despesas_a_pagar": a_pagar,
        "resultado": recebido_ano - pagas,
        "investido_no_ano": investido_ano,
        "investido_total": investido_total,
        "meses": meses,
        "investidores": [
            {
                "nome": str(n),
                "no_ano": a,
                "total": t,
                "percentual": round(100 * t / investido_total) if investido_total else 0,
            }
            for n, t, a in por_pessoa
        ],
    }
