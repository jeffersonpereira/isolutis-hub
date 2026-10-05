from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.cliente import Origem
from app.schemas.comum import Auditoria, Dinheiro, DinheiroPositivo, Entrada, Texto, TextoLongo

Etapa = Literal["lead", "diag_agendado", "diag_feito", "proposta", "negociacao", "ganho", "perdido"]
MotivoPerda = Literal["Preço", "Prazo", "Escolheu concorrente", "Adiou o projeto", "Sem resposta", "Fora do perfil"]


class NegocioEntrada(Entrada):
    titulo: Texto
    cliente_id: UUID
    etapa: Etapa = "lead"
    valor: DinheiroPositivo = Decimal("0")  # type: ignore[assignment]
    mensal: DinheiroPositivo = Decimal("0")  # type: ignore[assignment]
    previsao: date | None = None
    responsavel_id: UUID | None = None
    origem: Origem | None = None
    motivo_perda: MotivoPerda | None = None
    obs: TextoLongo = None

    @model_validator(mode="after")
    def _motivo_so_quando_perdido(self) -> "NegocioEntrada":
        if self.etapa == "perdido" and not self.motivo_perda:
            raise ValueError("Informe o motivo da perda.")
        if self.etapa != "perdido":
            self.motivo_perda = None
        return self


class NegocioAtualizar(NegocioEntrada):
    versao: int = Field(ge=1)


class MoverEtapa(Entrada):
    etapa: Etapa
    motivo_perda: MotivoPerda | None = None
    versao: int = Field(ge=1)


class NegocioLeitura(Auditoria):
    titulo: str
    cliente_id: UUID
    cliente_nome: str
    etapa: str
    valor: Dinheiro
    mensal: Dinheiro
    previsao: date | None
    responsavel_id: UUID | None
    origem: str | None
    motivo_perda: str | None
    obs: str | None
    fechado_em: date | None
    # Derivado: já existem lançamentos de receita gerados a partir deste negócio.
    faturado: bool
