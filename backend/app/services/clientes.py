"""Clientes = parceiros (hub) no papel de cliente. Este serviço é a fachada usada pela equipe comercial."""

from uuid import UUID

from sqlalchemy import Row, case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.constantes import ETAPAS_ABERTAS
from app.models import LancamentoReceita, Negocio, Orcamento, Parceiro, ParceiroPapel
from app.schemas.cliente import ClienteAtualizar, ClienteEntrada, ClienteRelacionados
from app.services import parceiros as svc
from app.services.orcamentos import consulta as consulta_orcamentos

PAPEL = svc.PAPEL_CLIENTE


def _campos(dados: ClienteEntrada) -> dict:
    campos = dados.model_dump()
    campos["tipo_pessoa"] = "PF" if campos.get("cpf_cnpj") and len(campos["cpf_cnpj"]) == 11 else "PJ"
    return campos


async def listar(sessao: AsyncSession) -> list[tuple[Parceiro, int, object]]:
    """Clientes com negócios abertos e total recebido (para a tabela da lista)."""
    empresa = await svc.empresa_atual(sessao)
    abertos = (
        select(Negocio.cliente_id, func.count().label("n"))
        .where(Negocio.etapa.in_([e.value for e in ETAPAS_ABERTAS]))
        .group_by(Negocio.cliente_id)
        .subquery()
    )
    recebido = (
        select(LancamentoReceita.cliente_id, func.sum(LancamentoReceita.valor).label("v"))
        .where(LancamentoReceita.status == "recebido")
        .group_by(LancamentoReceita.cliente_id)
        .subquery()
    )
    clientes = await svc.listar(sessao, empresa, PAPEL)
    n_por_cliente = dict((await sessao.execute(select(abertos.c.cliente_id, abertos.c.n))).all())
    v_por_cliente = dict((await sessao.execute(select(recebido.c.cliente_id, recebido.c.v))).all())
    return [(c, int(n_por_cliente.get(c.id, 0)), v_por_cliente.get(c.id, 0)) for c in clientes]


async def referencias(sessao: AsyncSession) -> list[Row]:
    """Só id e nome dos clientes da empresa ativa, sem contato, documento ou observações."""
    empresa = await svc.empresa_atual(sessao)
    consulta = (
        select(Parceiro.id, Parceiro.nome)
        .where(
            Parceiro.empresa_id == empresa.id,
            exists().where(
                ParceiroPapel.empresa_id == empresa.id,
                ParceiroPapel.parceiro_id == Parceiro.id,
                ParceiroPapel.papel == PAPEL,
            ),
        )
        .order_by(Parceiro.nome)
    )
    return list((await sessao.execute(consulta)).all())


async def criar(sessao: AsyncSession, dados: ClienteEntrada) -> Parceiro:
    return await svc.criar(sessao, await svc.empresa_atual(sessao), _campos(dados), [PAPEL])


async def atualizar(sessao: AsyncSession, id_: UUID, dados: ClienteAtualizar) -> Parceiro:
    await svc.exigir_cliente(sessao, id_)  # a equipe comercial só edita parceiros que são clientes
    campos = _campos(dados)
    campos.pop("versao", None)
    # os papéis do parceiro são preservados: a fachada de clientes não mexe neles
    return await svc.atualizar(sessao, await svc.empresa_atual(sessao), id_, campos, dados.versao)


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    await svc.excluir(sessao, await svc.empresa_atual(sessao), id_, PAPEL)


async def relacionados(sessao: AsyncSession, id_: UUID) -> ClienteRelacionados:
    await svc.exigir_cliente(sessao, id_)
    negocios = (
        await sessao.scalars(select(Negocio).where(Negocio.cliente_id == id_).order_by(Negocio.criado_em))
    ).all()
    orcs = (
        await sessao.scalars(consulta_orcamentos().where(Orcamento.cliente_id == id_).order_by(Orcamento.numero.desc()))
    ).all()
    lanc = (
        await sessao.execute(
            select(
                func.count(),
                func.coalesce(
                    func.sum(case((LancamentoReceita.status == "recebido", LancamentoReceita.valor), else_=0)), 0
                ),
            ).where(LancamentoReceita.cliente_id == id_)
        )
    ).one()
    return ClienteRelacionados(
        negocios=negocios,  # type: ignore[arg-type]
        orcamentos=[
            {"id": o.id, "numero": o.numero, "status": o.status_exibido, "total_projeto": o.total_projeto} for o in orcs
        ],  # type: ignore[arg-type]
        lancamentos=int(lanc[0]),
        recebido=lanc[1],
    )
