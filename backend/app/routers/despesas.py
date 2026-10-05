from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.deps import Sessao
from app.schemas.despesa import (
    DespesaAtualizar,
    DespesaEntrada,
    DespesaLeitura,
    InvestimentoAtualizar,
    InvestimentoEntrada,
    InvestimentoLeitura,
    OpcoesDespesa,
    ResumoDespesas,
)
from app.services import despesas as svc

router = APIRouter(tags=["Despesas e investimentos"])
Ano = Query(None, ge=2000, le=2100)


@router.get("/despesas", response_model=list[DespesaLeitura])
async def listar(sessao: Sessao, ano: int | None = Ano, mes: int | None = Query(None, ge=1, le=12)):
    return await svc.listar(sessao, ano, mes)


@router.get("/despesas/opcoes", response_model=OpcoesDespesa)
async def opcoes(sessao: Sessao):
    return await svc.opcoes(sessao)


@router.get("/despesas/resumo", response_model=ResumoDespesas)
async def resumo(sessao: Sessao, ano: int = Query(..., ge=2000, le=2100)):
    return await svc.resumo(sessao, ano)


@router.post("/despesas", response_model=list[DespesaLeitura], status_code=201)
async def criar(dados: DespesaEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/despesas/{id_}", response_model=DespesaLeitura)
async def atualizar(id_: UUID, dados: DespesaAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.post("/despesas/{id_}/pagar", response_model=DespesaLeitura)
async def pagar(id_: UUID, sessao: Sessao):
    return await svc.pagar(sessao, id_)


@router.delete("/despesas/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)


@router.get("/investimentos", response_model=list[InvestimentoLeitura])
async def listar_investimentos(sessao: Sessao, ano: int | None = Ano):
    return await svc.listar_investimentos(sessao, ano)


@router.post("/investimentos", response_model=InvestimentoLeitura, status_code=201)
async def criar_investimento(dados: InvestimentoEntrada, sessao: Sessao):
    return await svc.criar_investimento(sessao, dados)


@router.put("/investimentos/{id_}", response_model=InvestimentoLeitura)
async def atualizar_investimento(id_: UUID, dados: InvestimentoAtualizar, sessao: Sessao):
    return await svc.atualizar_investimento(sessao, id_, dados)


@router.delete("/investimentos/{id_}", status_code=204)
async def excluir_investimento(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir_investimento(sessao, id_)
    return Response(status_code=204)
