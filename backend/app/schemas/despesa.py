from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.comum import Auditoria, Dinheiro, DinheiroPositivo, Entrada, Leitura, Texto, TextoLongo, TextoOpcional

StatusDespesa = Literal["pago", "a_pagar"]
FormaInvestimento = Literal["Dinheiro (aporte)", "Equipamento", "Pagamento de despesa da empresa", "Outro"]


class DespesaEntrada(Entrada):
    data: date
    descricao: Texto
    valor: DinheiroPositivo
    categoria_id: UUID
    status: StatusDespesa = "pago"
    fornecedor: TextoOpcional = None
    obs: TextoLongo = None
    # Só na criação: repete todo mês por N meses (a primeira mantém o status; as demais ficam "a pagar").
    repetir: int = Field(default=1, ge=1, le=36)


class DespesaAtualizar(Entrada):
    data: date
    descricao: Texto
    valor: DinheiroPositivo
    categoria_id: UUID
    status: StatusDespesa
    fornecedor: TextoOpcional = None
    obs: TextoLongo = None
    versao: int = Field(ge=1)


class DespesaLeitura(Auditoria):
    data: date
    descricao: str
    valor: Dinheiro
    categoria_id: UUID
    categoria_nome: str
    status: str
    pago_em: date | None
    fornecedor: str | None
    obs: str | None
    grupo_id: UUID | None
    parcela: int | None
    total_parcelas: int | None


class InvestimentoEntrada(Entrada):
    data: date
    descricao: Texto
    valor: DinheiroPositivo
    investidor: Texto  # nome; o servidor localiza ou cria o investidor
    forma: FormaInvestimento = "Dinheiro (aporte)"
    obs: TextoLongo = None


class InvestimentoAtualizar(InvestimentoEntrada):
    versao: int = Field(ge=1)


class InvestimentoLeitura(Auditoria):
    data: date
    descricao: str
    valor: Dinheiro
    investidor_id: UUID
    investidor_nome: str
    forma: str
    obs: str | None


class CategoriaLeitura(Leitura):
    id: UUID
    nome: str


class OpcoesDespesa(Leitura):
    categorias: list[CategoriaLeitura]
    investidores: list[str]
    fornecedores: list[str]


class MesResultado(Leitura):
    mes: int
    recebido: Dinheiro
    despesas: Dinheiro
    resultado: Dinheiro
    investimentos: Dinheiro


class InvestidorResumo(Leitura):
    nome: str
    no_ano: Dinheiro
    total: Dinheiro
    percentual: int


class ResumoDespesas(Leitura):
    ano: int
    anos_disponiveis: list[int]
    recebido_no_ano: Dinheiro
    despesas_pagas: Dinheiro
    despesas_a_pagar: Dinheiro
    resultado: Dinheiro
    investido_no_ano: Dinheiro
    investido_total: Dinheiro
    meses: list[MesResultado]
    investidores: list[InvestidorResumo]
