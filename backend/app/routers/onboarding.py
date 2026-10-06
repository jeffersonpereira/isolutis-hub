"""Onboarding inicial da empresa: configuração guiada pós-cadastro."""

from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.deps import Administrador, EmpresaAtual, Sessao
from app.models import Produto
from app.services.base import confirmar

router = APIRouter(prefix="/onboarding")


class ProdutoInicial(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    preco: Decimal = Field(ge=0)


class ConcluirOnboardingEntrada(BaseModel):
    produtos: list[ProdutoInicial] = []


@router.get("/status")
async def status_onboarding(empresa: EmpresaAtual) -> dict[str, bool]:
    """Retorna se o onboarding da empresa já foi concluído."""
    return {"concluido": empresa.onboarding_concluido}


@router.post("/concluir", status_code=200)
async def concluir_onboarding(
    dados: ConcluirOnboardingEntrada,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> dict[str, bool]:
    """Cria produtos iniciais (se fornecidos) e marca o onboarding como concluído.

    Apenas administradores podem concluir o onboarding.
    Chamadas repetidas são idempotentes.
    """
    for produto_inicial in dados.produtos:
        produto = Produto(
            nome=produto_inicial.nome,
            tipo="outro",
            unidade="projeto",
            preco=produto_inicial.preco,
            ativo=True,
        )
        sessao.add(produto)

    empresa.onboarding_concluido = True
    await confirmar(sessao)

    return {"concluido": True}
