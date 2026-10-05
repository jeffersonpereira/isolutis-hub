from uuid import UUID

from fastapi import APIRouter, Response

from app.deps import Sessao
from app.schemas.negocio import MoverEtapa, NegocioAtualizar, NegocioEntrada, NegocioLeitura
from app.services import negocios as svc

router = APIRouter(prefix="/negocios", tags=["Negócios"])


@router.get("", response_model=list[NegocioLeitura])
async def listar(sessao: Sessao):
    return await svc.listar(sessao)


@router.post("", response_model=NegocioLeitura, status_code=201)
async def criar(dados: NegocioEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/{id_}", response_model=NegocioLeitura)
async def atualizar(id_: UUID, dados: NegocioAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.patch("/{id_}/etapa", response_model=NegocioLeitura)
async def mover(id_: UUID, dados: MoverEtapa, sessao: Sessao):
    return await svc.mover(sessao, id_, dados)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)
