from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.domain.constantes import StatusEtapa
from app.domain.datas import adicionar_dias, hoje
from app.domain.projeto import ETAPAS_PADRAO, POS_ENTREGA_PADRAO
from app.errors import NaoEncontrado, RegraDeNegocio
from app.models import Negocio, Orcamento, Projeto, ProjetoEtapa
from app.schemas.projeto import EtapaEntrada, ProjetoAtualizar, ProjetoEntrada
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.parceiros import exigir_cliente


def consulta():
    return select(Projeto).options(joinedload(Projeto.cliente), selectinload(Projeto.etapas))


async def listar(sessao: AsyncSession) -> list[Projeto]:
    return list((await sessao.scalars(consulta().order_by(Projeto.entrega.asc().nulls_last()))).all())


async def obter_completo(sessao: AsyncSession, id_: UUID) -> Projeto:
    projeto = await sessao.scalar(consulta().where(Projeto.id == id_).execution_options(populate_existing=True))
    if projeto is None:
        raise NaoEncontrado("Projeto")
    return projeto


async def _validar_vinculos(sessao: AsyncSession, dados: ProjetoEntrada, id_atual: UUID | None = None) -> None:
    await exigir_cliente(sessao, dados.cliente_id)
    if dados.negocio_id:
        negocio = await obter(sessao, Negocio, dados.negocio_id, "Negócio")
        if negocio.cliente_id != dados.cliente_id:
            raise RegraDeNegocio("O negócio vendido pertence a outro cliente.")
        outro = await sessao.scalar(
            select(Projeto.id).where(Projeto.negocio_id == dados.negocio_id, Projeto.id != id_atual)
        )
        if outro:
            raise RegraDeNegocio("Já existe um projeto para este negócio.")
    if dados.orcamento_id:
        orc = await obter(sessao, Orcamento, dados.orcamento_id, "Orçamento")
        if orc.cliente_id != dados.cliente_id:
            raise RegraDeNegocio("O orçamento vinculado pertence a outro cliente.")


def _sincronizar_etapas(projeto: Projeto, etapas: list[EtapaEntrada]) -> None:
    atuais = {e.id: e for e in projeto.etapas}
    novas: list[ProjetoEtapa] = []
    for ordem, entrada in enumerate(etapas, start=1):
        campos = entrada.model_dump(exclude={"id"})
        etapa = atuais.pop(entrada.id, None) if entrada.id else None
        if etapa:
            aplicar(etapa, campos)
            etapa.ordem = ordem
        else:
            etapa = ProjetoEtapa(**campos, ordem=ordem)
        novas.append(etapa)
    projeto.etapas[:] = novas


async def criar(sessao: AsyncSession, dados: ProjetoEntrada) -> Projeto:
    await _validar_vinculos(sessao, dados)
    projeto = Projeto(**dados.model_dump(exclude={"etapas"}), etapas=[])
    _sincronizar_etapas(projeto, dados.etapas)
    sessao.add(projeto)
    await confirmar(sessao)
    return await obter_completo(sessao, projeto.id)


async def atualizar(sessao: AsyncSession, id_: UUID, dados: ProjetoAtualizar) -> Projeto:
    projeto = await obter_completo(sessao, id_)
    conferir_versao(projeto, dados.versao)
    await _validar_vinculos(sessao, dados, id_)
    aplicar(projeto, dados.model_dump(), ignorar=("versao", "etapas"))
    _sincronizar_etapas(projeto, dados.etapas)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    await sessao.delete(await obter(sessao, Projeto, id_, "Projeto"))
    await confirmar(sessao)


async def modelo_do_negocio(sessao: AsyncSession, negocio_id: UUID) -> dict:
    """Valores iniciais de um projeto aberto a partir de um negócio ganho (orçamento aprovado preferido)."""
    negocio = await obter(sessao, Negocio, negocio_id, "Negócio")
    orcs = (
        await sessao.scalars(
            select(Orcamento).options(selectinload(Orcamento.itens)).where(Orcamento.negocio_id == negocio_id)
        )
    ).all()
    orc = next((o for o in orcs if o.status == "aprovado"), orcs[0] if orcs else None)
    escopo = "\n".join(f"• {i.descricao}" for i in orc.itens if not i.mensal) if orc else None
    return {
        "titulo": negocio.titulo,
        "cliente_id": negocio.cliente_id,
        "negocio_id": negocio.id,
        "orcamento_id": orc.id if orc else None,
        "responsavel_id": negocio.responsavel_id,
        "inicio": hoje(),
        "escopo": escopo or None,
        "pos_entrega": POS_ENTREGA_PADRAO,
    }


def etapas_padrao(inicio: date | None, entrega: date | None) -> list[dict]:
    """Roteiro padrão da iSolutis distribuído entre o início e a entrega (7 dias por etapa se não houver entrega)."""
    inicio = inicio or hoje()
    total = max(len(ETAPAS_PADRAO), (entrega - inicio).days) if entrega else len(ETAPAS_PADRAO) * 7
    soma = sum(e.peso for e in ETAPAS_PADRAO)
    resultado, dia = [], 0
    for e in ETAPAS_PADRAO:
        duracao = max(1, round(total * e.peso / soma))
        resultado.append(
            {
                "titulo": e.titulo,
                "descricao": e.descricao,
                "entregaveis": e.entregaveis,
                "status": StatusEtapa.A_FAZER.value,
                "inicio": adicionar_dias(inicio, dia),
                "fim": adicionar_dias(inicio, dia + duracao - 1),
            }
        )
        dia += duracao
    return resultado
