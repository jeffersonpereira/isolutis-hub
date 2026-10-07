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


class EmpresaOnboardingEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    segmento: str | None = Field(default=None, max_length=100)


@router.patch("/empresa", status_code=204)
async def salvar_empresa_onboarding(
    dados: EmpresaOnboardingEntrada,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> None:
    """Atualiza nome e segmento da empresa (usado no wizard e na tela de configurações)."""
    empresa.nome = dados.nome.strip()
    if dados.segmento is not None:
        empresa.segmento = dados.segmento.strip() or None
    await confirmar(sessao)


class ProdutosIniciais(BaseModel):
    produtos: list[ProdutoInicial] = []


@router.post("/produtos", status_code=204)
async def salvar_produtos_onboarding(
    dados: ProdutosIniciais,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> None:
    """Cadastra produtos iniciais durante o onboarding (sem duplicar produtos já existentes)."""
    for p in dados.produtos:
        nome = p.nome.strip()
        if nome:
            sessao.add(Produto(
                nome=nome,
                tipo="outro",
                unidade="projeto",
                preco=p.preco or Decimal(0),
                ativo=True,
            ))
    await confirmar(sessao)
