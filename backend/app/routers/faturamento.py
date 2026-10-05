from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.deps import Sessao
from app.schemas.faturamento import (
    FaturamentoEmLote,
    LancamentoAtualizar,
    LancamentoEntrada,
    LancamentoLeitura,
    ResumoFaturamento,
)
from app.services import faturamento as svc

router = APIRouter(prefix="/faturamento", tags=["Faturamento"])


@router.get("", response_model=list[LancamentoLeitura])
async def listar(
    sessao: Sessao, ano: int | None = Query(None, ge=2000, le=2100), mes: int | None = Query(None, ge=1, le=12)
):
    return await svc.listar(sessao, ano, mes)


@router.get("/resumo", response_model=ResumoFaturamento)
async def resumo(sessao: Sessao, ano: int = Query(..., ge=2000, le=2100)):
    return await svc.resumo(sessao, ano)


@router.get("/exportar", response_class=Response)
async def exportar(sessao: Sessao, ano: int = Query(..., ge=2000, le=2100)) -> Response:
    csv = await svc.exportar_csv(sessao, ano)
    return Response(
        csv,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''faturamento-isolutis-{ano}.csv"},
    )


@router.post("", response_model=list[LancamentoLeitura], status_code=201)
async def criar(dados: LancamentoEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.post("/lote", response_model=list[LancamentoLeitura], status_code=201)
async def criar_em_lote(dados: FaturamentoEmLote, sessao: Sessao):
    return await svc.criar_em_lote(sessao, dados)


@router.put("/{id_}", response_model=LancamentoLeitura)
async def atualizar(id_: UUID, dados: LancamentoAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.post("/{id_}/receber", response_model=LancamentoLeitura)
async def receber(id_: UUID, sessao: Sessao):
    return await svc.receber(sessao, id_)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)
