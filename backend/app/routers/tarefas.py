from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.deps import Sessao
from app.schemas.tarefa import MoverTarefa, TarefaAtualizar, TarefaEntrada, TarefaLeitura
from app.services import tarefas as svc

router = APIRouter(prefix="/tarefas", tags=["Tarefas"])


@router.get("", response_model=list[TarefaLeitura])
async def listar(sessao: Sessao, busca: str | None = Query(None, max_length=100)):
    return await svc.listar(sessao, busca)


@router.post("", response_model=TarefaLeitura, status_code=201)
async def criar(dados: TarefaEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/{id_}", response_model=TarefaLeitura)
async def atualizar(id_: UUID, dados: TarefaAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.patch("/{id_}/coluna", response_model=TarefaLeitura)
async def mover(id_: UUID, dados: MoverTarefa, sessao: Sessao):
    return await svc.mover(sessao, id_, dados)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)
