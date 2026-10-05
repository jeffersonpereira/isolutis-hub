from datetime import date
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.constantes import EtapaNegocio
from app.domain.datas import hoje
from app.errors import RegraDeNegocio
from app.models import LancamentoReceita, Negocio
from app.schemas.negocio import MoverEtapa, NegocioAtualizar, NegocioEntrada
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.parceiros import exigir_cliente


def _consulta():
    faturado = exists().where(LancamentoReceita.negocio_id == Negocio.id).label("faturado")
    return select(Negocio, faturado).options(joinedload(Negocio.cliente))


def _com_faturado(linhas: list) -> list[Negocio]:
    resultado = []
    for negocio, faturado in linhas:
        negocio.faturado = bool(faturado)
        resultado.append(negocio)
    return resultado


async def listar(sessao: AsyncSession) -> list[Negocio]:
    linhas = (await sessao.execute(_consulta().order_by(Negocio.previsao.asc().nulls_last()))).all()
    return _com_faturado(linhas)


async def obter_completo(sessao: AsyncSession, id_: UUID) -> Negocio:
    linhas = (await sessao.execute(_consulta().where(Negocio.id == id_))).all()
    if not linhas:
        raise RegraDeNegocio("Negócio não encontrado.", status=404, codigo="nao_encontrado")
    return _com_faturado(linhas)[0]


def definir_etapa(negocio: Negocio, etapa: str, motivo_perda: str | None, hoje_: date | None = None) -> None:
    """Regras da mudança de etapa: ganho carimba o fechamento; perdido exige motivo; sair desfaz o que não vale mais."""
    hoje_ = hoje_ or hoje()
    if etapa == EtapaNegocio.PERDIDO:
        if not motivo_perda:
            raise RegraDeNegocio("Informe o motivo da perda.")
        negocio.motivo_perda = motivo_perda
    else:
        negocio.motivo_perda = None
    if etapa == EtapaNegocio.GANHO:
        if negocio.etapa != EtapaNegocio.GANHO:
            negocio.fechado_em = hoje_
    else:
        negocio.fechado_em = None
    negocio.etapa = etapa


async def criar(sessao: AsyncSession, dados: NegocioEntrada) -> Negocio:
    await exigir_cliente(sessao, dados.cliente_id)
    campos = dados.model_dump(exclude={"etapa", "motivo_perda"})
    negocio = Negocio(**campos, etapa="lead")
    definir_etapa(negocio, dados.etapa, dados.motivo_perda)
    sessao.add(negocio)
    await confirmar(sessao)
    return await obter_completo(sessao, negocio.id)


async def atualizar(sessao: AsyncSession, id_: UUID, dados: NegocioAtualizar) -> Negocio:
    negocio = await obter(sessao, Negocio, id_, "Negócio")
    conferir_versao(negocio, dados.versao)
    if dados.cliente_id != negocio.cliente_id:
        raise RegraDeNegocio("Não é possível trocar o cliente de um negócio já aberto. Crie um novo negócio.")
    aplicar(negocio, dados.model_dump(), ignorar=("versao", "etapa", "motivo_perda", "cliente_id"))
    definir_etapa(negocio, dados.etapa, dados.motivo_perda)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def mover(sessao: AsyncSession, id_: UUID, dados: MoverEtapa) -> Negocio:
    negocio = await obter(sessao, Negocio, id_, "Negócio")
    conferir_versao(negocio, dados.versao)
    definir_etapa(negocio, dados.etapa, dados.motivo_perda)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    negocio = await obter(sessao, Negocio, id_, "Negócio")
    await sessao.delete(negocio)
    await confirmar(sessao)
