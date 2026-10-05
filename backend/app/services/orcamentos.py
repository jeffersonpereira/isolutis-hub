from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.domain.constantes import ETAPAS_ANTES_DA_PROPOSTA, StatusOrcamento
from app.domain.datas import hoje
from app.errors import NaoEncontrado, RegraDeNegocio
from app.models import Negocio, Orcamento, OrcamentoItem
from app.schemas.orcamento import ItemEntrada, OrcamentoAtualizar, OrcamentoEntrada
from app.services import negocios as svc_negocios
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.parceiros import exigir_cliente


def consulta():
    return select(Orcamento).options(joinedload(Orcamento.cliente), selectinload(Orcamento.itens))


async def listar(sessao: AsyncSession, status: str | None = None) -> list[Orcamento]:
    orcs = list((await sessao.scalars(consulta().order_by(Orcamento.numero.desc()))).all())
    if status:
        orcs = [o for o in orcs if o.status_exibido == status]
    return orcs


async def obter_completo(sessao: AsyncSession, id_: UUID) -> Orcamento:
    orc = await sessao.scalar(consulta().where(Orcamento.id == id_).execution_options(populate_existing=True))
    if orc is None:
        raise NaoEncontrado("Orçamento")
    return orc


async def _validar_vinculos(sessao: AsyncSession, dados: OrcamentoEntrada) -> Negocio | None:
    await exigir_cliente(sessao, dados.cliente_id)
    if not dados.negocio_id:
        return None
    negocio = await obter(sessao, Negocio, dados.negocio_id, "Negócio")
    if negocio.cliente_id != dados.cliente_id:
        raise RegraDeNegocio("O negócio escolhido pertence a outro cliente.")
    return negocio


def _sincronizar_itens(orc: Orcamento, itens: list[ItemEntrada]) -> None:
    """Atualiza itens existentes (por id), cria os novos e remove os que saíram, mantendo a ordem da tela."""
    atuais = {i.id: i for i in orc.itens}
    novos: list[OrcamentoItem] = []
    for ordem, entrada in enumerate(itens, start=1):
        campos = entrada.model_dump(exclude={"id"})
        item = atuais.pop(entrada.id, None) if entrada.id else None
        if item:
            aplicar(item, campos)
            item.ordem = ordem
        else:
            item = OrcamentoItem(**campos, ordem=ordem)
        novos.append(item)
    orc.itens[:] = novos  # orfãos são removidos (delete-orphan)


def _aplicar_status(orc: Orcamento, status: str) -> None:
    orc.status = status
    orc.aprovado_em = (orc.aprovado_em or hoje()) if status == StatusOrcamento.APROVADO else None


def _avancar_negocio(negocio: Negocio | None, status: str) -> None:
    """Enviar a proposta leva um negócio que ainda estava em lead/diagnóstico para "Proposta enviada"."""
    if negocio and status == StatusOrcamento.ENVIADO and negocio.etapa in ETAPAS_ANTES_DA_PROPOSTA:
        negocio.etapa = "proposta"


async def criar(sessao: AsyncSession, dados: OrcamentoEntrada) -> Orcamento:
    negocio = await _validar_vinculos(sessao, dados)
    orc = Orcamento(
        **dados.model_dump(exclude={"itens", "status"}),
        itens=[],
    )
    _aplicar_status(orc, dados.status)
    _sincronizar_itens(orc, dados.itens)
    _avancar_negocio(negocio, dados.status)
    sessao.add(orc)
    await confirmar(sessao)
    return await obter_completo(sessao, orc.id)


async def atualizar(sessao: AsyncSession, id_: UUID, dados: OrcamentoAtualizar) -> Orcamento:
    orc = await obter_completo(sessao, id_)
    conferir_versao(orc, dados.versao)
    negocio = await _validar_vinculos(sessao, dados)
    aplicar(orc, dados.model_dump(), ignorar=("versao", "itens", "status"))
    _aplicar_status(orc, dados.status)
    _sincronizar_itens(orc, dados.itens)
    _avancar_negocio(negocio, dados.status)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def aprovar(sessao: AsyncSession, id_: UUID) -> Orcamento:
    """Cliente aprovou: orçamento aprovado e, se houver negócio, ele vira Ganho com os valores do orçamento."""
    orc = await obter_completo(sessao, id_)
    _aplicar_status(orc, StatusOrcamento.APROVADO.value)
    if orc.negocio_id:
        negocio = await obter(sessao, Negocio, orc.negocio_id, "Negócio")
        t = orc.totais
        negocio.valor, negocio.mensal = t.projeto, t.mensal
        svc_negocios.definir_etapa(negocio, "ganho", None)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    orc = await obter(sessao, Orcamento, id_, "Orçamento")
    await sessao.delete(orc)
    await confirmar(sessao)
