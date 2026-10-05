"""Casos de uso do módulo financeiro. Cada operação confirma a transação uma única vez."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, extract, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.datas import hoje
from app.domain.dinheiro import ZERO
from app.errors import NaoEncontrado, RegraDeNegocio
from app.financeiro import regras
from app.financeiro.models import (
    ContaBancaria,
    InstituicaoFinanceira,
    PlanoConta,
    TituloFinanceiro,
)
from app.financeiro.schemas import (
    ContaBancariaEntrada,
    PlanoContaEntrada,
    TituloEntrada,
)
from app.models import Empresa, Municipio, Parceiro
from app.services.base import confirmar
from app.services.parceiros import empresa_atual  # noqa: F401  (reexportado para as rotas)


async def _obter(sessao: AsyncSession, modelo, id_: UUID, empresa: Empresa, nome: str):  # noqa: ANN001, ANN202
    obj = await sessao.get(modelo, id_)
    if obj is None or getattr(obj, "empresa_id", empresa.id) != empresa.id:
        raise NaoEncontrado(nome)
    return obj


# ============================================================================= referências
async def listar_municipios(sessao: AsyncSession, uf: str | None, busca: str | None, limite: int) -> list[Municipio]:
    consulta = select(Municipio).order_by(Municipio.nome).limit(limite)
    if uf:
        consulta = consulta.where(Municipio.uf == uf)
    if busca:
        consulta = consulta.where(Municipio.nome.ilike(f"%{busca.strip()}%"))
    return list((await sessao.scalars(consulta)).all())


async def listar_instituicoes(sessao: AsyncSession, busca: str | None) -> list[InstituicaoFinanceira]:
    consulta = select(InstituicaoFinanceira).order_by(InstituicaoFinanceira.codigo)
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(InstituicaoFinanceira.nome.ilike(termo) | InstituicaoFinanceira.codigo.ilike(termo))
    return list((await sessao.scalars(consulta)).all())


# ============================================================================= plano de contas
async def listar_plano(sessao: AsyncSession, empresa: Empresa) -> list[dict]:
    contas = list((await sessao.scalars(select(PlanoConta).where(PlanoConta.empresa_id == empresa.id))).all())
    com_filhas = {c.plano_pai_id for c in contas if c.plano_pai_id}
    com_titulos = set((await sessao.scalars(select(TituloFinanceiro.plano_conta_id).distinct())).all())
    contas.sort(key=lambda c: regras.chave_de_ordenacao(c.codigo))
    return [
        {
            "id": c.id, "plano_pai_id": c.plano_pai_id, "codigo": c.codigo, "nome": c.nome, "tipo_conta": c.tipo_conta,
            "natureza": c.natureza, "nivel": c.nivel, "possui_filhas": c.id in com_filhas, "possui_titulos": c.id in com_titulos,
        }
        for c in contas
    ]  # fmt: skip


async def proximo_codigo(sessao: AsyncSession, empresa: Empresa, pai_id: UUID | None) -> str:
    if pai_id is None:
        irmaos = (
            await sessao.scalars(
                select(PlanoConta.codigo).where(PlanoConta.empresa_id == empresa.id, PlanoConta.plano_pai_id.is_(None))
            )
        ).all()
        return regras.proximo_codigo(list(irmaos), None)
    pai = await _obter(sessao, PlanoConta, pai_id, empresa, "Conta pai")
    if pai.tipo_conta != "S" or pai.nivel >= regras.NIVEL_MAXIMO:
        raise RegraDeNegocio("Esta conta não aceita contas filhas.")
    irmaos = (await sessao.scalars(select(PlanoConta.codigo).where(PlanoConta.plano_pai_id == pai.id))).all()
    return regras.proximo_codigo(list(irmaos), pai.codigo)


async def _validar_conta(sessao: AsyncSession, empresa: Empresa, d: PlanoContaEntrada) -> tuple[int, str]:
    """Devolve (nível, natureza) válidos para a conta, aplicando RN01 com mensagens claras."""
    codigo = d.codigo.strip()
    if d.plano_pai_id is None:
        if not regras.codigo_valido(codigo, None):
            raise RegraDeNegocio(regras.mensagem_codigo_invalido(1, None))
        return 1, d.natureza or "R"
    pai = await _obter(sessao, PlanoConta, d.plano_pai_id, empresa, "Conta pai")
    if pai.tipo_conta != "S":
        raise RegraDeNegocio("Uma conta analítica não pode ter contas filhas: escolha uma conta sintética como pai.")
    nivel = pai.nivel + 1
    if nivel > regras.NIVEL_MAXIMO:
        raise RegraDeNegocio("O plano de contas tem no máximo três níveis.")
    if not regras.codigo_valido(codigo, pai.codigo):
        raise RegraDeNegocio(regras.mensagem_codigo_invalido(nivel, pai.codigo))
    if nivel == regras.NIVEL_MAXIMO and d.tipo_conta != "A":
        raise RegraDeNegocio("As contas do terceiro nível são sempre analíticas.")
    return nivel, pai.natureza


async def criar_conta(sessao: AsyncSession, empresa: Empresa, d: PlanoContaEntrada) -> PlanoConta:
    nivel, natureza = await _validar_conta(sessao, empresa, d)
    conta = PlanoConta(
        empresa_id=empresa.id, plano_pai_id=d.plano_pai_id, codigo=d.codigo.strip(), nome=d.nome.strip(),
        tipo_conta=d.tipo_conta, natureza=natureza, nivel=nivel,
    )  # fmt: skip
    sessao.add(conta)
    await _confirmar_plano(sessao)
    return conta


async def atualizar_conta(sessao: AsyncSession, empresa: Empresa, id_: UUID, d: PlanoContaEntrada) -> PlanoConta:
    conta = await _obter(sessao, PlanoConta, id_, empresa, "Conta")
    filhas = await sessao.scalar(select(func.count()).select_from(PlanoConta).where(PlanoConta.plano_pai_id == id_))
    titulos = await sessao.scalar(
        select(func.count()).select_from(TituloFinanceiro).where(TituloFinanceiro.plano_conta_id == id_)
    )
    if d.plano_pai_id == id_:
        raise RegraDeNegocio("Uma conta não pode ser pai dela mesma.")
    nivel, natureza = await _validar_conta(sessao, empresa, d)
    if filhas and (
        d.codigo.strip() != conta.codigo or d.plano_pai_id != conta.plano_pai_id or natureza != conta.natureza
    ):
        raise RegraDeNegocio("Esta conta tem contas filhas: não é possível mudar o código, a natureza ou o pai.")
    if filhas and d.tipo_conta == "A":
        raise RegraDeNegocio("Uma conta com filhas precisa continuar sintética.")
    if titulos and (d.tipo_conta == "S" or natureza != conta.natureza):
        raise RegraDeNegocio("Há títulos lançados nesta conta: ela precisa continuar analítica e com a mesma natureza.")
    conta.plano_pai_id, conta.codigo, conta.nome = d.plano_pai_id, d.codigo.strip(), d.nome.strip()
    conta.tipo_conta, conta.natureza, conta.nivel = d.tipo_conta, natureza, nivel
    await _confirmar_plano(sessao)
    return conta


async def excluir_conta(sessao: AsyncSession, empresa: Empresa, id_: UUID) -> None:
    conta = await _obter(sessao, PlanoConta, id_, empresa, "Conta")
    if await sessao.scalar(select(func.count()).select_from(PlanoConta).where(PlanoConta.plano_pai_id == id_)):
        raise RegraDeNegocio("Esta conta tem contas filhas. Exclua ou mova as filhas antes.")
    if await sessao.scalar(
        select(func.count()).select_from(TituloFinanceiro).where(TituloFinanceiro.plano_conta_id == id_)
    ):
        raise RegraDeNegocio("Há títulos lançados nesta conta. Exclua ou mude esses títulos antes.")
    await sessao.delete(conta)
    await confirmar(sessao)


async def _confirmar_plano(sessao: AsyncSession) -> None:
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        if "uq_plano_contas_company_codigo" in str(e.orig):
            raise RegraDeNegocio("Já existe uma conta com este código no plano de contas.") from e
        raise RegraDeNegocio("Os dados não respeitam as regras do plano de contas.") from e


# ============================================================================= contas bancárias
def _linha_conta(c: ContaBancaria) -> dict:
    return {
        "id": c.id, "instituicao_financeira_id": c.instituicao_financeira_id, "instituicao_codigo": c.instituicao.codigo,
        "instituicao_nome": c.instituicao.nome, "nome": c.nome, "saldo_inicial": c.saldo_inicial,
    }  # fmt: skip


async def listar_contas_bancarias(sessao: AsyncSession, empresa: Empresa) -> list[dict]:
    consulta = (
        select(ContaBancaria).options(joinedload(ContaBancaria.instituicao))
        .where(ContaBancaria.empresa_id == empresa.id).order_by(ContaBancaria.nome)
    )  # fmt: skip
    return [_linha_conta(c) for c in (await sessao.scalars(consulta)).all()]


async def _conta_completa(sessao: AsyncSession, id_: UUID) -> dict:
    consulta = select(ContaBancaria).options(joinedload(ContaBancaria.instituicao)).where(ContaBancaria.id == id_)
    return _linha_conta((await sessao.scalars(consulta.execution_options(populate_existing=True))).one())


async def criar_conta_bancaria(sessao: AsyncSession, empresa: Empresa, d: ContaBancariaEntrada) -> dict:
    await _exigir_instituicao(sessao, d.instituicao_financeira_id)
    conta = ContaBancaria(
        empresa_id=empresa.id,
        instituicao_financeira_id=d.instituicao_financeira_id,
        nome=d.nome.strip(),
        saldo_inicial=d.saldo_inicial,
    )
    sessao.add(conta)
    await _confirmar_conta(sessao)
    return await _conta_completa(sessao, conta.id)


async def atualizar_conta_bancaria(sessao: AsyncSession, empresa: Empresa, id_: UUID, d: ContaBancariaEntrada) -> dict:
    conta = await _obter(sessao, ContaBancaria, id_, empresa, "Conta bancária")
    await _exigir_instituicao(sessao, d.instituicao_financeira_id)
    conta.instituicao_financeira_id, conta.nome, conta.saldo_inicial = (
        d.instituicao_financeira_id,
        d.nome.strip(),
        d.saldo_inicial,
    )
    await _confirmar_conta(sessao)
    return await _conta_completa(sessao, id_)


async def excluir_conta_bancaria(sessao: AsyncSession, empresa: Empresa, id_: UUID) -> None:
    conta = await _obter(sessao, ContaBancaria, id_, empresa, "Conta bancária")
    if await sessao.scalar(
        select(func.count()).select_from(TituloFinanceiro).where(TituloFinanceiro.conta_bancaria_id == id_)
    ):
        raise RegraDeNegocio("Há títulos financeiros nesta conta bancária. Exclua ou mude esses títulos antes.")
    await sessao.delete(conta)
    await confirmar(sessao)


async def _exigir_instituicao(sessao: AsyncSession, id_: UUID) -> None:
    if await sessao.get(InstituicaoFinanceira, id_) is None:
        raise RegraDeNegocio("Escolha uma instituição financeira válida.")


async def _confirmar_conta(sessao: AsyncSession) -> None:
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        raise RegraDeNegocio("Já existe uma conta com este nome nesta instituição financeira.") from e


# ============================================================================= títulos
def _linha_titulo(t: TituloFinanceiro) -> dict:
    return {
        "id": t.id, "tipo_conta": t.tipo_conta, "conta_bancaria_id": t.conta_bancaria_id, "conta_bancaria_nome": t.conta_bancaria.nome,
        "plano_conta_id": t.plano_conta_id, "plano_conta_codigo": t.plano_conta.codigo, "plano_conta_nome": t.plano_conta.nome,
        "parceiro_id": t.parceiro_id, "parceiro_nome": t.parceiro.nome, "data_emissao": t.data_emissao,
        "data_vencimento": t.data_vencimento, "valor_titulo": t.valor_titulo, "valor_desconto": t.valor_desconto,
        "valor_multa": t.valor_multa, "valor_juros": t.valor_juros,
        "valor_devido": regras.valor_devido(t.valor_titulo, t.valor_desconto, t.valor_multa, t.valor_juros),
        "status": t.status, "data_pagamento": t.data_pagamento, "valor_quitacao": t.valor_quitacao, "anotacao": t.anotacao,
    }  # fmt: skip


def _consulta_titulos(empresa: Empresa) -> Select:
    return (
        select(TituloFinanceiro)
        .options(joinedload(TituloFinanceiro.conta_bancaria), joinedload(TituloFinanceiro.plano_conta), joinedload(TituloFinanceiro.parceiro))
        .where(TituloFinanceiro.empresa_id == empresa.id)
    )  # fmt: skip


async def listar_titulos(
    sessao: AsyncSession,
    empresa: Empresa,
    tipo: str | None,
    status: str | None,
    de: date | None,
    ate: date | None,
    busca: str | None,
) -> list[dict]:
    consulta = _consulta_titulos(empresa).order_by(TituloFinanceiro.data_vencimento, TituloFinanceiro.created_at, TituloFinanceiro.id)
    if tipo:
        consulta = consulta.where(TituloFinanceiro.tipo_conta == tipo)
    if status:
        consulta = consulta.where(TituloFinanceiro.status == status)
    if de:
        consulta = consulta.where(TituloFinanceiro.data_vencimento >= de)
    if ate:
        consulta = consulta.where(TituloFinanceiro.data_vencimento <= ate)
    if busca:
        consulta = consulta.join(Parceiro, Parceiro.id == TituloFinanceiro.parceiro_id).where(
            Parceiro.nome.ilike(f"%{busca.strip()}%")
        )
    return [_linha_titulo(t) for t in (await sessao.scalars(consulta)).unique().all()]


async def _titulo_completo(sessao: AsyncSession, empresa: Empresa, id_: UUID) -> dict:
    consulta = _consulta_titulos(empresa).where(TituloFinanceiro.id == id_).execution_options(populate_existing=True)
    return _linha_titulo((await sessao.scalars(consulta)).unique().one())


async def _campos_validados(sessao: AsyncSession, empresa: Empresa, d: TituloEntrada) -> dict:
    """RN03/RN04 e coerência da quitação, com mensagens claras (o banco repete as regras)."""
    await _obter(sessao, ContaBancaria, d.conta_bancaria_id, empresa, "Conta bancária")
    await _obter(sessao, Parceiro, d.parceiro_id, empresa, "Parceiro")
    conta = await _obter(sessao, PlanoConta, d.plano_conta_id, empresa, "Conta do plano de contas")
    if conta.tipo_conta != "A":
        raise RegraDeNegocio(
            "Títulos só podem ser lançados em conta analítica do plano de contas, nunca em conta sintética."
        )
    if conta.natureza != regras.natureza_do_titulo(d.tipo_conta):
        raise RegraDeNegocio("Conta a pagar exige uma conta de despesa; conta a receber exige uma conta de receita.")
    if d.data_emissao and d.data_emissao > d.data_vencimento:
        raise RegraDeNegocio("A data de emissão não pode ser depois do vencimento.")
    devido = regras.valor_devido(d.valor_titulo, d.valor_desconto, d.valor_multa, d.valor_juros)
    if devido <= 0:
        raise RegraDeNegocio("O desconto não pode zerar o valor do título.")
    campos = d.model_dump()
    if d.status == "Q":
        if d.data_pagamento is None:
            raise RegraDeNegocio("Informe a data de pagamento do título quitado.")
        campos["valor_quitacao"] = d.valor_quitacao or devido
        if campos["valor_quitacao"] <= 0:
            raise RegraDeNegocio("Informe o valor pago.")
    else:
        campos["data_pagamento"], campos["valor_quitacao"] = None, ZERO
    return campos


async def criar_titulo(sessao: AsyncSession, empresa: Empresa, d: TituloEntrada) -> dict:
    campos = await _campos_validados(sessao, empresa, d)
    titulo = TituloFinanceiro(empresa_id=empresa.id, **campos)
    sessao.add(titulo)
    await confirmar(sessao)
    return await _titulo_completo(sessao, empresa, titulo.id)


async def atualizar_titulo(sessao: AsyncSession, empresa: Empresa, id_: UUID, d: TituloEntrada) -> dict:
    titulo = await _obter(sessao, TituloFinanceiro, id_, empresa, "Título")
    for campo, valor in (await _campos_validados(sessao, empresa, d)).items():
        setattr(titulo, campo, valor)
    await confirmar(sessao)
    return await _titulo_completo(sessao, empresa, id_)


async def excluir_titulo(sessao: AsyncSession, empresa: Empresa, id_: UUID) -> None:
    await sessao.delete(await _obter(sessao, TituloFinanceiro, id_, empresa, "Título"))
    await confirmar(sessao)


# ============================================================================= fluxo de caixa (US05)
async def fluxo_de_caixa(sessao: AsyncSession, empresa: Empresa, ano: int) -> dict:
    """Mês a mês: realizado (quitados, por data de pagamento) e previsto (abertos, por vencimento).

    Títulos cancelados não entram. O saldo parte da soma dos saldos iniciais das contas bancárias mais o
    movimento realizado antes do ano.
    """
    t = TituloFinanceiro
    devido = t.valor_titulo - t.valor_desconto + t.valor_multa + t.valor_juros

    async def somar(coluna_data, valor, tipo: str, status: str) -> dict[int, Decimal]:  # noqa: ANN001
        mes = extract("month", coluna_data)
        inicio, fim = date(ano, 1, 1), date(ano + 1, 1, 1)
        linhas = await sessao.execute(
            select(mes, func.coalesce(func.sum(valor), 0))
            .where(t.empresa_id == empresa.id, t.tipo_conta == tipo, t.status == status, coluna_data >= inicio, coluna_data < fim)
            .group_by(mes)
        )  # fmt: skip
        return {int(m): v for m, v in linhas.all()}

    ent_real = await somar(t.data_pagamento, t.valor_quitacao, "R", "Q")
    sai_real = await somar(t.data_pagamento, t.valor_quitacao, "P", "Q")
    ent_prev = await somar(t.data_vencimento, devido, "R", "A")
    sai_prev = await somar(t.data_vencimento, devido, "P", "A")

    base = await sessao.scalar(
        select(func.coalesce(func.sum(ContaBancaria.saldo_inicial), 0)).where(ContaBancaria.empresa_id == empresa.id)
    )
    anterior = await sessao.execute(
        select(t.tipo_conta, func.coalesce(func.sum(t.valor_quitacao), 0))
        .where(t.empresa_id == empresa.id, t.status == "Q", t.data_pagamento < date(ano, 1, 1))
        .group_by(t.tipo_conta)
    )  # fmt: skip
    mov = dict(anterior.all())
    saldo_inicial = base + mov.get("R", ZERO) - mov.get("P", ZERO)

    meses, acumulado = [], saldo_inicial
    for m in range(1, 13):
        er, ep, sr, sp = ent_real.get(m, ZERO), ent_prev.get(m, ZERO), sai_real.get(m, ZERO), sai_prev.get(m, ZERO)
        saldo = er + ep - sr - sp
        acumulado += saldo
        meses.append({"mes": m, "entradas_realizadas": er, "entradas_previstas": ep, "saidas_realizadas": sr, "saidas_previstas": sp, "saldo_do_mes": saldo, "saldo_acumulado": acumulado})  # fmt: skip

    anos = {
        int(a)
        for coluna in (t.data_vencimento, t.data_pagamento)
        for (a,) in (
            await sessao.execute(
                select(extract("year", coluna)).where(t.empresa_id == empresa.id, coluna.is_not(None)).distinct()
            )
        ).all()
    }
    return {
        "ano": ano, "anos_disponiveis": sorted(anos | {hoje().year}), "saldo_inicial": saldo_inicial, "meses": meses,
        "total_entradas": sum((m["entradas_realizadas"] + m["entradas_previstas"] for m in meses), ZERO),
        "total_saidas": sum((m["saidas_realizadas"] + m["saidas_previstas"] for m in meses), ZERO),
    }  # fmt: skip
