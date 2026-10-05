from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors import NaoEncontrado
from app.models import Projeto, Tarefa, TarefaChecklist
from app.schemas.tarefa import ChecklistEntrada, MoverTarefa, TarefaAtualizar, TarefaEntrada
from app.services.base import aplicar, conferir_versao, confirmar, obter
from app.services.parceiros import exigir_cliente


def consulta():
    return select(Tarefa).options(selectinload(Tarefa.checklist))


async def listar(sessao: AsyncSession, busca: str | None = None) -> list[Tarefa]:
    q = consulta().order_by(Tarefa.coluna, Tarefa.prioridade_ordem, Tarefa.prazo.asc().nulls_last(), Tarefa.criado_em)
    if busca:
        q = q.where(Tarefa.busca.ilike(f"%{busca.strip().lower()}%"))
    return list((await sessao.scalars(q)).all())


async def obter_completo(sessao: AsyncSession, id_: UUID) -> Tarefa:
    tarefa = await sessao.scalar(consulta().where(Tarefa.id == id_).execution_options(populate_existing=True))
    if tarefa is None:
        raise NaoEncontrado("Tarefa")
    return tarefa


def _definir_coluna(tarefa: Tarefa, coluna: str) -> None:
    """Concluir carimba a data; reabrir a limpa (regra também garantida por CHECK no banco)."""
    tarefa.concluida_em = (tarefa.concluida_em or datetime.now(UTC)) if coluna == "concluido" else None
    tarefa.coluna = coluna


def _sincronizar_checklist(tarefa: Tarefa, itens: list[ChecklistEntrada]) -> None:
    atuais = {i.id: i for i in tarefa.checklist}
    novos: list[TarefaChecklist] = []
    for ordem, entrada in enumerate(itens, start=1):
        campos = entrada.model_dump(exclude={"id"})
        item = atuais.pop(entrada.id, None) if entrada.id else None
        if item:
            aplicar(item, campos)
            item.ordem = ordem
        else:
            item = TarefaChecklist(**campos, ordem=ordem)
        novos.append(item)
    tarefa.checklist[:] = novos


async def _validar_vinculos(sessao: AsyncSession, dados: TarefaEntrada) -> None:
    if dados.cliente_id:
        await exigir_cliente(sessao, dados.cliente_id)
    if dados.projeto_id:
        await obter(sessao, Projeto, dados.projeto_id, "Projeto")


async def criar(sessao: AsyncSession, dados: TarefaEntrada) -> Tarefa:
    await _validar_vinculos(sessao, dados)
    tarefa = Tarefa(**dados.model_dump(exclude={"checklist", "coluna"}), checklist=[])
    _definir_coluna(tarefa, dados.coluna)
    _sincronizar_checklist(tarefa, dados.checklist)
    sessao.add(tarefa)
    await confirmar(sessao)
    return await obter_completo(sessao, tarefa.id)


async def atualizar(sessao: AsyncSession, id_: UUID, dados: TarefaAtualizar) -> Tarefa:
    tarefa = await obter_completo(sessao, id_)
    conferir_versao(tarefa, dados.versao)
    await _validar_vinculos(sessao, dados)
    aplicar(tarefa, dados.model_dump(), ignorar=("versao", "checklist", "coluna"))
    _definir_coluna(tarefa, dados.coluna)
    _sincronizar_checklist(tarefa, dados.checklist)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def mover(sessao: AsyncSession, id_: UUID, dados: MoverTarefa) -> Tarefa:
    tarefa = await obter_completo(sessao, id_)
    conferir_versao(tarefa, dados.versao)
    _definir_coluna(tarefa, dados.coluna)
    await confirmar(sessao)
    return await obter_completo(sessao, id_)


async def excluir(sessao: AsyncSession, id_: UUID) -> None:
    await sessao.delete(await obter(sessao, Tarefa, id_, "Tarefa"))
    await confirmar(sessao)
