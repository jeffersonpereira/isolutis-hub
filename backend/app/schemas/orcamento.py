from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.comum import Auditoria, Dinheiro, DinheiroPositivo, Entrada, Leitura, Quantidade, Texto, TextoLongo

StatusGravavel = Literal["rascunho", "enviado", "aprovado", "recusado"]
StatusExibido = Literal["rascunho", "enviado", "aprovado", "recusado", "vencido"]


class ItemEntrada(Entrada):
    id: UUID | None = None
    produto_id: UUID | None = None
    descricao: Texto
    qtd: Quantidade = Decimal("1")
    preco_unitario: DinheiroPositivo = Decimal("0")  # type: ignore[assignment]
    mensal: bool = False


class OrcamentoEntrada(Entrada):
    cliente_id: UUID
    negocio_id: UUID | None = None
    data: date
    validade_dias: int = Field(default=15, ge=1, le=3650)
    status: StatusGravavel = "rascunho"
    desconto: DinheiroPositivo = Decimal("0")  # type: ignore[assignment]
    obs: TextoLongo = None
    itens: list[ItemEntrada] = Field(min_length=1)

    @model_validator(mode="after")
    def _desconto_nao_excede_o_projeto(self) -> "OrcamentoEntrada":
        projeto = sum((i.qtd * i.preco_unitario for i in self.itens if not i.mensal), Decimal("0"))
        if self.desconto > projeto:
            raise ValueError("O desconto não pode ser maior que o valor do projeto.")
        return self


class OrcamentoAtualizar(OrcamentoEntrada):
    versao: int = Field(ge=1)


class ItemLeitura(Leitura):
    id: UUID
    produto_id: UUID | None
    descricao: str
    qtd: Quantidade
    preco_unitario: Dinheiro
    mensal: bool
    subtotal: Dinheiro


class OrcamentoLeitura(Auditoria):
    numero: str
    cliente_id: UUID
    cliente_nome: str
    negocio_id: UUID | None
    data: date
    validade_dias: int
    valido_ate: date
    status: str
    status_exibido: StatusExibido
    desconto: Dinheiro
    obs: str | None
    aprovado_em: date | None
    total_projeto: Dinheiro
    total_mensal: Dinheiro
    itens: list[ItemLeitura]


class AprovacaoSaida(Leitura):
    orcamento: OrcamentoLeitura
    negocio_id: UUID | None
