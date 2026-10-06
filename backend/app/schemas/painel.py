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
    lancamentos_vencidos: AlertaItem
    orcamentos_parados: AlertaItem
    projetos_atrasados: AlertaItem


class Painel(Leitura):
    ano: int
    mes: int
    recebido_no_mes: Dinheiro
    previsto_no_mes: Dinheiro
    recorrente_no_mes: Dinheiro
    funil_abertos: int
    funil_valor: Dinheiro
    funil_mensal: Dinheiro
    ganhos: int
    perdidos: int
    conversao_pct: int | None
    orcamentos_aguardando_qtd: int
    orcamentos_aguardando_valor: Dinheiro
    banco_vazio: bool
    serie: list[PontoSerie]
    por_etapa: list[EtapaFunil]
    proximos_fechamentos: list[ProximoFechamento]
    orcamentos_aguardando: list[OrcamentoAguardando]
    alertas: AlertasInfo
