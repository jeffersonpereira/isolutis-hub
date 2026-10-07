from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.deps import Sessao, requer_base
from app.schemas.cliente import (
    ClienteReferencia,
    ClienteAtualizar,
    ClienteEntrada,
    ClienteLeitura,
    ClienteRelacionados,
    ClienteResumo,
)
from app.services import clientes as svc

router = APIRouter(prefix="/clientes", tags=["Clientes"])
# Lista mínima (id e nome) para qualquer papel identificar o cliente em projetos, tarefas e faturamento.
router_referencias = APIRouter(prefix="/clientes", tags=["Clientes"], dependencies=[Depends(requer_base)])


@router_referencias.get("/referencias", response_model=list[ClienteReferencia])
async def referencias(sessao: Sessao) -> list[ClienteReferencia]:
    return [ClienteReferencia(id=c.id, nome=c.nome) for c in await svc.referencias(sessao)]


@router.get("", response_model=list[ClienteResumo])
async def listar(sessao: Sessao) -> list[ClienteResumo]:
    return [
        ClienteResumo(**ClienteLeitura.model_validate(c).model_dump(), negocios_abertos=abertos, faturado=faturado)
        for c, abertos, faturado in await svc.listar(sessao)
    ]


@router.post("", response_model=ClienteLeitura, status_code=201)
async def criar(dados: ClienteEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/{id_}", response_model=ClienteLeitura)
async def atualizar(id_: UUID, dados: ClienteAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)


@router.get("/{id_}/relacionados", response_model=ClienteRelacionados)
async def relacionados(id_: UUID, sessao: Sessao) -> ClienteRelacionados:
    return await svc.relacionados(sessao, id_)
