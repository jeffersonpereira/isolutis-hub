"""Regras de projeto: progresso e roteiro padrão de etapas da iSolutis."""

from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.constantes import StatusEtapa

POS_ENTREGA_PADRAO = (
    "Depois da entrega, seguimos responsáveis pela operação: hospedagem, monitoramento, correções, "
    "atualizações de segurança e pequenas evoluções, com mensalidade previsível."
)


def progresso(status_das_etapas: Iterable[StatusEtapa]) -> int:
    """Percentual (0-100) de etapas concluídas."""
    etapas = list(status_das_etapas)
    if not etapas:
        return 0
    concluidas = sum(1 for s in etapas if s is StatusEtapa.CONCLUIDA)
    return round(100 * concluidas / len(etapas))


@dataclass(frozen=True)
class EtapaPadrao:
    titulo: str
    descricao: str
    entregaveis: str
    peso: float


ETAPAS_PADRAO: tuple[EtapaPadrao, ...] = (
    EtapaPadrao(
        "Diagnóstico e levantamento",
        "Conversas com a equipe do cliente para entender o processo atual, os gargalos e quem vai usar o sistema.",
        "Mapa do processo atual\nLista de necessidades priorizadas",
        1,
    ),
    EtapaPadrao(
        "Especificação aprovada",
        "Escopo, telas e regras de negócio descritos e validados com o cliente antes de qualquer código.",
        "Documento de especificação\nProtótipo das telas principais\nAprovação formal do escopo",
        1.5,
    ),
    EtapaPadrao(
        "Desenvolvimento",
        "Construção do sistema conforme a especificação aprovada, com entregas parciais para acompanhamento.",
        "Versões parciais para acompanhamento\nAmbiente de testes acessível ao cliente",
        4,
    ),
    EtapaPadrao(
        "Revisão de engenharia e segurança",
        "Revisão do código, testes de segurança e de desempenho antes de ir ao ar.",
        "Relatório de revisão de segurança\nCorreções aplicadas",
        1,
    ),
    EtapaPadrao(
        "Validação com o cliente",
        "O cliente usa o sistema com casos reais e aponta ajustes finais.",
        "Lista de ajustes validada\nAceite da versão final",
        1,
    ),
    EtapaPadrao(
        "Implantação e treinamento",
        "Sistema no ar no ambiente definitivo, dados iniciais carregados e equipe do cliente treinada.",
        "Sistema em produção\nTreinamento da equipe\nManual de uso",
        1,
    ),
    EtapaPadrao(
        "Acompanhamento pós-entrega",
        "Primeiras semanas de uso acompanhadas de perto, com suporte prioritário.",
        "Relatório do primeiro mês de uso",
        1.5,
    ),
)
