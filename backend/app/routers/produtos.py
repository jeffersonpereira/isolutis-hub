from uuid import UUID

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.deps import Sessao
from app.domain.catalogo import CATALOGO
from app.models import Produto
from app.schemas.produto import ProdutoAtualizar, ProdutoEntrada, ProdutoLeitura
from app.services.base import aplicar, conferir_versao, confirmar, obter

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("", response_model=list[ProdutoLeitura])
async def listar(sessao: Sessao) -> list[Produto]:
    return list((await sessao.scalars(select(Produto).order_by(Produto.tipo, Produto.nome))).all())


@router.post("", response_model=ProdutoLeitura, status_code=201)
async def criar(dados: ProdutoEntrada, sessao: Sessao) -> Produto:
    produto = Produto(**dados.model_dump())
    sessao.add(produto)
    await confirmar(sessao)
    return produto


@router.post("/catalogo", response_model=list[ProdutoLeitura], status_code=201)
async def criar_catalogo(sessao: Sessao) -> list[Produto]:
    """Cria os produtos do catálogo do site (preços em branco, para a equipe definir)."""

    produtos = [Produto(**item) for item in CATALOGO]
    sessao.add_all(produtos)
    await confirmar(sessao)
    return produtos


@router.put("/{id_}", response_model=ProdutoLeitura)
async def atualizar(id_: UUID, dados: ProdutoAtualizar, sessao: Sessao) -> Produto:
    produto = await obter(sessao, Produto, id_, "Produto")
    conferir_versao(produto, dados.versao)
    aplicar(produto, dados.model_dump(), ignorar=("versao",))
    await confirmar(sessao)
    return produto


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await sessao.delete(await obter(sessao, Produto, id_, "Produto"))
    await confirmar(sessao)
    return Response(status_code=204)
