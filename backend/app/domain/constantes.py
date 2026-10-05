"""Vocabulário do domínio. Os valores são os mesmos gravados no banco (CHECKs) e expostos na API."""

from enum import StrEnum


class EtapaNegocio(StrEnum):
    LEAD = "lead"
    DIAG_AGENDADO = "diag_agendado"
    DIAG_FEITO = "diag_feito"
    PROPOSTA = "proposta"
    NEGOCIACAO = "negociacao"
    GANHO = "ganho"
    PERDIDO = "perdido"

    @property
    def aberta(self) -> bool:
        return self not in (EtapaNegocio.GANHO, EtapaNegocio.PERDIDO)


ETAPAS_ABERTAS = tuple(e for e in EtapaNegocio if e.aberta)
ETAPAS_ANTES_DA_PROPOSTA = (EtapaNegocio.LEAD, EtapaNegocio.DIAG_AGENDADO, EtapaNegocio.DIAG_FEITO)


class TipoReceita(StrEnum):
    PROJETO = "projeto"
    MENSAL = "mensal"
    CONSULTORIA = "consultoria"
    OUTRO = "outro"


class StatusOrcamento(StrEnum):
    RASCUNHO = "rascunho"
    ENVIADO = "enviado"
    APROVADO = "aprovado"
    RECUSADO = "recusado"
    # Derivado (nunca gravado): enviado cuja validade já passou.
    VENCIDO = "vencido"


class StatusReceita(StrEnum):
    PREVISTO = "previsto"
    RECEBIDO = "recebido"


class StatusProjeto(StrEnum):
    PLANEJAMENTO = "planejamento"
    CONSTRUCAO = "construcao"
    VALIDACAO = "validacao"
    ENTREGUE = "entregue"
    PAUSADO = "pausado"


class StatusEtapa(StrEnum):
    A_FAZER = "a_fazer"
    ANDAMENTO = "andamento"
    CONCLUIDA = "concluida"


class ColunaTarefa(StrEnum):
    A_FAZER = "a_fazer"
    FAZENDO = "fazendo"
    REVISAO = "revisao"
    CONCLUIDO = "concluido"


class Prioridade(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class StatusDespesa(StrEnum):
    PAGO = "pago"
    A_PAGAR = "a_pagar"


class TipoDespesa(StrEnum):
    DESPESA = "despesa"
    INVESTIMENTO = "investimento"
