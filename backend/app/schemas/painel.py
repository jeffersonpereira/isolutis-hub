from datetime import date
from uuid import UUID

from app.schemas.comum import Dinheiro, Leitura


class PontoSerie(Leitura):
    ano: int
    mes: int
    recebido: Dinheiro
    previsto: Dinheiro


class EtapaFunil(Leitura):
    etapa: str
    quantidade: int
    valor: Dinheiro


class ProximoFechamento(Leitura):
    id: UUID
    titulo: str
    cliente_nome: str
    etapa: str
    valor: Dinheiro
    mensal: Dinheiro
    previsao: date


class OrcamentoAguardando(Leitura):
    id: UUID
    numero: str
    cliente_nome: str
    data: date
    total_projeto: Dinheiro


class AlertaItem(Leitura):
    quantidade: int
    ids: list[UUID]


class AlertasInfo(Leitura):
    lancamentos_vencidos: AlertaItem | None = None  # `financeiro`
    orcamentos_parados: AlertaItem | None = None  # `comercial`
    projetos_atrasados: AlertaItem  # `base`


class Painel(Leitura):
    """Campos de `financeiro` e `comercial` só vêm quando o papel tem a permissão; o front omite o que não vier."""

    ano: int
    mes: int
    banco_vazio: bool
    alertas: AlertasInfo
    # financeiro
    recebido_no_mes: Dinheiro | None = None
    previsto_no_mes: Dinheiro | None = None
    recorrente_no_mes: Dinheiro | None = None
    serie: list[PontoSerie] | None = None
    # comercial
    funil_abertos: int | None = None
    funil_valor: Dinheiro | None = None
    funil_mensal: Dinheiro | None = None
    ganhos: int | None = None
    perdidos: int | None = None
    conversao_pct: int | None = None
    orcamentos_aguardando_qtd: int | None = None
    orcamentos_aguardando_valor: Dinheiro | None = None
    por_etapa: list[EtapaFunil] | None = None
    proximos_fechamentos: list[ProximoFechamento] | None = None
    orcamentos_aguardando: list[OrcamentoAguardando] | None = None
