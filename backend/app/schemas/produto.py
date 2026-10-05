from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.comum import Auditoria, Dinheiro, DinheiroPositivo, Entrada, Texto, TextoLongo

TipoProduto = Literal["projeto", "mensal", "consultoria", "outro"]


class ProdutoEntrada(Entrada):
    nome: Texto
    tipo: TipoProduto
    unidade: Texto = "projeto"
    preco: DinheiroPositivo = Decimal("0")  # type: ignore[assignment]
    ativo: bool = True
    descricao: TextoLongo = None


class ProdutoAtualizar(ProdutoEntrada):
    versao: int = Field(ge=1)


class ProdutoLeitura(Auditoria):
    nome: str
    tipo: str
    unidade: str
    preco: Dinheiro
    ativo: bool
    descricao: str | None
