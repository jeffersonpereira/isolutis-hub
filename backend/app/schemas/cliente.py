"""Fachada de clientes: o parceiro (hub) visto apenas no papel de cliente. Os papéis não aparecem aqui."""

from uuid import UUID

from pydantic import Field

from app.schemas.comum import Dinheiro, Leitura
from app.schemas.parceiro import Origem, ParceiroLeitura, _CamposDoParceiro

__all__ = [
    "ClienteAtualizar", "ClienteEntrada", "ClienteLeitura", "ClienteRelacionados", "ClienteResumo", "Origem",
    "RelNegocio", "RelOrcamento",
]  # fmt: skip


class ClienteEntrada(_CamposDoParceiro):
    """Cliente: o tipo de pessoa é deduzido do documento (11 dígitos = PF; senão PJ)."""


class ClienteAtualizar(ClienteEntrada):
    versao: int = Field(ge=1)


class ClienteLeitura(ParceiroLeitura):
    pass


class ClienteResumo(ClienteLeitura):
    """Linha da lista de clientes, com os números que a tabela mostra."""

    negocios_abertos: int
    faturado: Dinheiro


class RelNegocio(Leitura):
    id: UUID
    titulo: str
    etapa: str
    valor: Dinheiro
    mensal: Dinheiro


class RelOrcamento(Leitura):
    id: UUID
    numero: str
    status: str
    total_projeto: Dinheiro


class ClienteRelacionados(Leitura):
    negocios: list[RelNegocio]
    orcamentos: list[RelOrcamento]
    lancamentos: int
    recebido: Dinheiro
