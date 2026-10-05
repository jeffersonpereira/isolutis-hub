from datetime import date
from decimal import Decimal as D

import pytest

from app.domain.constantes import StatusEtapa, StatusOrcamento
from app.domain.datas import adicionar_meses
from app.domain.dinheiro import centavos, dividir_em_parcelas
from app.domain.orcamento import ItemCalculavel, status_efetivo, totais, valido_ate
from app.domain.projeto import progresso


def test_adicionar_meses_limita_ao_ultimo_dia():
    assert adicionar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert adicionar_meses(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert adicionar_meses(date(2026, 11, 15), 3) == date(2027, 2, 15)
    assert adicionar_meses(date(2026, 3, 10), -3) == date(2025, 12, 10)


def test_parcelas_somam_o_total_e_a_ultima_absorve_o_arredondamento():
    partes = dividir_em_parcelas(D("100.00"), 3)
    assert partes == [D("33.33"), D("33.33"), D("33.34")]
    assert sum(partes) == D("100.00")
    assert dividir_em_parcelas(D("10"), 1) == [D("10.00")]
    with pytest.raises(ValueError):
        dividir_em_parcelas(D("10"), 0)


def test_centavos_arredonda_meio_para_cima():
    assert centavos("1.005") == D("1.01")
    assert centavos(2) == D("2.00")


def test_totais_separam_projeto_e_mensal_e_aplicam_desconto():
    itens = [
        ItemCalculavel(D("1"), D("10000"), False),
        ItemCalculavel(D("2"), D("500.50"), False),
        ItemCalculavel(D("1"), D("800"), True),
    ]
    t = totais(itens, D("1000"))
    assert t.projeto == D("10001.00")
    assert t.mensal == D("800.00")


def test_desconto_maior_que_o_projeto_nao_fica_negativo():
    assert totais([ItemCalculavel(D("1"), D("100"), False)], D("500")).projeto == D("0.00")


def test_status_vencido_e_derivado():
    enviado = StatusOrcamento.ENVIADO
    assert status_efetivo(enviado, date(2026, 1, 1), 15, date(2026, 1, 16)) is StatusOrcamento.ENVIADO
    assert status_efetivo(enviado, date(2026, 1, 1), 15, date(2026, 1, 17)) is StatusOrcamento.VENCIDO
    # só orçamentos enviados vencem
    assert status_efetivo(StatusOrcamento.APROVADO, date(2020, 1, 1), 15, date(2026, 1, 1)) is StatusOrcamento.APROVADO
    assert valido_ate(date(2026, 1, 1), 0) == date(2026, 1, 16)  # validade 0 cai no padrão de 15 dias


def test_progresso():
    assert progresso([]) == 0
    assert progresso([StatusEtapa.CONCLUIDA, StatusEtapa.ANDAMENTO, StatusEtapa.A_FAZER]) == 33
    assert progresso([StatusEtapa.CONCLUIDA] * 2) == 100
