from decimal import Decimal as D

from app.financeiro import regras


def test_cpf_e_cnpj_com_digitos_verificadores():
    assert regras.cpf_valido("52998224725")
    assert not regras.cpf_valido("52998224724")  # dígito errado
    assert not regras.cpf_valido("11111111111")  # sequência repetida
    assert regras.cnpj_valido("11222333000181")
    assert not regras.cnpj_valido("11222333000180")
    assert not regras.cnpj_valido("00000000000000")
    assert regras.documento_valido("PF", "52998224725") and regras.documento_valido("PJ", "11222333000181")
    assert not regras.documento_valido("PJ", "52998224725")  # CPF onde se esperava CNPJ
    assert regras.so_digitos("11.222.333/0001-81") == "11222333000181"


def test_codigos_do_plano_de_contas_seguem_a_hierarquia():
    assert regras.codigo_valido("1", None) and regras.codigo_valido("12", None)
    assert not regras.codigo_valido("1.01", None)
    assert (
        regras.codigo_valido("1.01", "1")
        and not regras.codigo_valido("1.1", "1")
        and not regras.codigo_valido("2.01", "1")
    )
    assert regras.codigo_valido("1.01.001", "1.01") and not regras.codigo_valido("1.01.01", "1.01")
    assert not regras.codigo_valido("1.01.001.001", "1.01.001")  # quarto nível não existe
    assert regras.nivel_do_codigo("1.01.001") == 3


def test_proximo_codigo_e_ordenacao_numerica():
    assert regras.proximo_codigo([], None) == "1"
    assert regras.proximo_codigo(["1", "2"], None) == "3"
    assert regras.proximo_codigo([], "1") == "1.01"
    assert regras.proximo_codigo(["1.01", "1.09"], "1") == "1.10"
    assert regras.proximo_codigo(["1.01.001"], "1.01") == "1.01.002"
    codigos = ["10", "2", "1.02", "1", "1.01.001", "1.01"]
    assert sorted(codigos, key=regras.chave_de_ordenacao) == ["1", "1.01", "1.01.001", "1.02", "2", "10"]


def test_natureza_do_titulo_e_valor_devido():
    assert regras.natureza_do_titulo("P") == "D" and regras.natureza_do_titulo("R") == "R"
    assert regras.valor_devido(D("1000"), D("50"), D("10.50"), D("4.25")) == D("964.75")
