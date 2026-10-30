"""Rotas do módulo financeiro. Exigem a permissão `financeiro` (papéis admin e financeiro)."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.deps import Sessao, requer_base, requer_financeiro
from app.errors import RegraDeNegocio
from app.financeiro import recorrencias as rec
from app.financeiro import servicos as svc
from app.financeiro.schemas import (
    ContaBancariaEntrada,
    ContaBancariaLeitura,
    FluxoDeCaixa,
    InstituicaoLeitura,
    MunicipioLeitura,
    PaginaTitulos,
    PlanoContaEntrada,
    PlanoContaLeitura,
    ProximoCodigo,
    RecorrenciaAtualizar,
    RecorrenciaEntrada,
    RecorrenciaLeitura,
    TituloEntrada,
    TituloLeitura,
)

router = APIRouter(prefix="/financeiro", tags=["Financeiro"], dependencies=[Depends(requer_financeiro)])
# Referências (municípios e instituições) são dados públicos de apoio a formulários: qualquer papel lê.
router_referencias = APIRouter(prefix="/financeiro", tags=["Financeiro"], dependencies=[Depends(requer_base)])

Ano = Annotated[int, Query(ge=2000, le=2100)]


async def _empresa(sessao: Sessao):  # noqa: ANN202
    return await svc.empresa_atual(sessao)


# --------------------------------------------------------------------------- referências
@router_referencias.get("/municipios", response_model=list[MunicipioLeitura])
async def municipios(
    sessao: Sessao,
    uf: str | None = Query(None, min_length=2, max_length=2),
    busca: str | None = Query(None, max_length=100),
    limite: int = Query(1000, ge=1, le=6000),
):
    return await svc.listar_municipios(sessao, uf.upper() if uf else None, busca, limite)


@router_referencias.get("/instituicoes", response_model=list[InstituicaoLeitura])
async def instituicoes(sessao: Sessao, busca: str | None = Query(None, max_length=100)):
    return await svc.listar_instituicoes(sessao, busca)


# --------------------------------------------------------------------------- plano de contas
@router.get("/plano-contas", response_model=list[PlanoContaLeitura])
async def listar_plano(sessao: Sessao):
    return await svc.listar_plano(sessao, await _empresa(sessao))


@router.get("/plano-contas/proximo-codigo", response_model=ProximoCodigo)
async def proximo_codigo(sessao: Sessao, pai_id: UUID | None = None):
    return {"codigo": await svc.proximo_codigo(sessao, await _empresa(sessao), pai_id)}


@router.post("/plano-contas", response_model=PlanoContaLeitura, status_code=201)
async def criar_conta(dados: PlanoContaEntrada, sessao: Sessao):
    empresa = await _empresa(sessao)
    conta = await svc.criar_conta(sessao, empresa, dados)
    return next(c for c in await svc.listar_plano(sessao, empresa) if c["id"] == conta.id)


@router.put("/plano-contas/{id_}", response_model=PlanoContaLeitura)
async def atualizar_conta(id_: UUID, dados: PlanoContaEntrada, sessao: Sessao):
    empresa = await _empresa(sessao)
    conta = await svc.atualizar_conta(sessao, empresa, id_, dados)
    return next(c for c in await svc.listar_plano(sessao, empresa) if c["id"] == conta.id)


@router.delete("/plano-contas/{id_}", status_code=204)
async def excluir_conta(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir_conta(sessao, await _empresa(sessao), id_)
    return Response(status_code=204)


# --------------------------------------------------------------------------- contas bancárias
@router.get("/contas-bancarias", response_model=list[ContaBancariaLeitura])
async def listar_contas_bancarias(sessao: Sessao):
    return await svc.listar_contas_bancarias(sessao, await _empresa(sessao))


@router.post("/contas-bancarias", response_model=ContaBancariaLeitura, status_code=201)
async def criar_conta_bancaria(dados: ContaBancariaEntrada, sessao: Sessao):
    return await svc.criar_conta_bancaria(sessao, await _empresa(sessao), dados)


@router.put("/contas-bancarias/{id_}", response_model=ContaBancariaLeitura)
async def atualizar_conta_bancaria(id_: UUID, dados: ContaBancariaEntrada, sessao: Sessao):
    return await svc.atualizar_conta_bancaria(sessao, await _empresa(sessao), id_, dados)


@router.delete("/contas-bancarias/{id_}", status_code=204)
async def excluir_conta_bancaria(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir_conta_bancaria(sessao, await _empresa(sessao), id_)
    return Response(status_code=204)


# --------------------------------------------------------------------------- títulos
def _filtros_titulos(
    tipo: Literal["P", "R"] | None = None,
    status: Literal["A", "Q", "C"] | None = None,
    busca: str | None = Query(None, max_length=100),
    parceiro_id: UUID | None = None,
    plano_conta_id: UUID | None = None,
    conta_bancaria_id: UUID | None = None,
    de: date | None = Query(None, description="Vencimento a partir de"),
    ate: date | None = Query(None, description="Vencimento até"),
    pago_de: date | None = Query(None, description="Pagamento a partir de"),
    pago_ate: date | None = Query(None, description="Pagamento até"),
    valor_min: Decimal | None = Query(None, ge=0, description="Valor devido mínimo"),
    valor_max: Decimal | None = Query(None, ge=0, description="Valor devido máximo"),
    recorrente: bool | None = None,
) -> svc.FiltroTitulos:
    for inicio, fim, nome in ((de, ate, "vencimento"), (pago_de, pago_ate, "pagamento"), (valor_min, valor_max, "valor")):
        if inicio is not None and fim is not None and inicio > fim:
            raise RegraDeNegocio(f"O início do filtro de {nome} não pode ser depois do fim.")
    return svc.FiltroTitulos(tipo, status, busca, parceiro_id, plano_conta_id, conta_bancaria_id, de, ate, pago_de, pago_ate, valor_min, valor_max, recorrente)


FiltroTitulos = Annotated[svc.FiltroTitulos, Depends(_filtros_titulos)]
Ordem = Literal["vencimento", "valor", "parceiro"]
Sentido = Literal["asc", "desc"]


@router.get("/titulos", response_model=PaginaTitulos)
async def listar_titulos(
    sessao: Sessao,
    filtro: FiltroTitulos,
    ordem: Ordem = "vencimento",
    sentido: Sentido = "asc",
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(25),
):
    if tamanho not in svc.TAMANHOS_DE_PAGINA:
        raise RegraDeNegocio(f"O tamanho da página deve ser um destes: {', '.join(map(str, svc.TAMANHOS_DE_PAGINA))}.")
    return await svc.listar_titulos(sessao, await _empresa(sessao), filtro, ordem, sentido, pagina, tamanho)


@router.get("/titulos/exportar", response_class=Response)
async def exportar_titulos(sessao: Sessao, filtro: FiltroTitulos, ordem: Ordem = "vencimento", sentido: Sentido = "asc"):
    """CSV de todos os títulos do filtro (sem paginação), pronto para planilhas em português."""
    conteudo, truncado = await svc.exportar_titulos_csv(sessao, await _empresa(sessao), filtro, ordem, sentido)
    cabecalhos = {"Content-Disposition": 'attachment; filename="titulos.csv"'}
    if truncado:
        cabecalhos["X-Exportacao-Truncada"] = "1"
    return Response(conteudo, media_type="text/csv; charset=utf-8", headers=cabecalhos)


@router.post("/titulos", response_model=TituloLeitura, status_code=201)
async def criar_titulo(dados: TituloEntrada, sessao: Sessao):
    return await svc.criar_titulo(sessao, await _empresa(sessao), dados)


@router.put("/titulos/{id_}", response_model=TituloLeitura)
async def atualizar_titulo(id_: UUID, dados: TituloEntrada, sessao: Sessao):
    return await svc.atualizar_titulo(sessao, await _empresa(sessao), id_, dados)


@router.delete("/titulos/{id_}", status_code=204)
async def excluir_titulo(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir_titulo(sessao, await _empresa(sessao), id_)
    return Response(status_code=204)


# --------------------------------------------------------------------------- fluxo de caixa (US05)
@router.get("/fluxo-de-caixa", response_model=FluxoDeCaixa)
async def fluxo_de_caixa(sessao: Sessao, ano: Ano):
    return await svc.fluxo_de_caixa(sessao, await _empresa(sessao), ano)


# --------------------------------------------------------------------------- recorrências
@router.get("/recorrencias", response_model=list[RecorrenciaLeitura])
async def listar_recorrencias(sessao: Sessao):
    return await rec.listar(sessao, await _empresa(sessao))


@router.post("/recorrencias", response_model=RecorrenciaLeitura, status_code=201)
async def criar_recorrencia(dados: RecorrenciaEntrada, sessao: Sessao):
    return await rec.criar(sessao, await _empresa(sessao), dados)


@router.put("/recorrencias/{id_}", response_model=RecorrenciaLeitura)
async def atualizar_recorrencia(id_: UUID, dados: RecorrenciaAtualizar, sessao: Sessao):
    return await rec.atualizar(sessao, await _empresa(sessao), id_, dados)


@router.post("/recorrencias/{id_}/pausar", response_model=RecorrenciaLeitura)
async def pausar_recorrencia(id_: UUID, sessao: Sessao):
    return await rec.pausar(sessao, await _empresa(sessao), id_)


@router.post("/recorrencias/{id_}/retomar", response_model=RecorrenciaLeitura)
async def retomar_recorrencia(id_: UUID, sessao: Sessao):
    return await rec.retomar(sessao, await _empresa(sessao), id_)


@router.post("/recorrencias/{id_}/encerrar", response_model=RecorrenciaLeitura)
async def encerrar_recorrencia(id_: UUID, sessao: Sessao):
    return await rec.encerrar(sessao, await _empresa(sessao), id_)
