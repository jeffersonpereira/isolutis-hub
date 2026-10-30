"""Casos de uso do módulo financeiro. Cada operação confirma a transação uma única vez."""

import csv
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Select, extract, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.datas import hoje
from app.domain.dinheiro import ZERO
from app.errors import Conflito, NaoEncontrado, RegraDeNegocio
from app.financeiro import regras
from app.financeiro.models import (
    ContaBancaria,
    InstituicaoFinanceira,
    PlanoConta,
    TituloFinanceiro,
)
from app.financeiro.plano_padrao import CODIGO_APORTE_SOCIO, ler_plano_padrao
from app.financeiro.schemas import (
    ContaBancariaEntrada,
    PlanoContaEntrada,
    TituloEntrada,
)
from app.models import Empresa, Municipio, Parceiro, ParceiroPapel
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
            "natureza": c.natureza, "nivel": c.nivel, "aporte_socio": c.aporte_socio,
            "possui_filhas": c.id in com_filhas, "possui_titulos": c.id in com_titulos,
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


def _exigir_aporte_valido(d: PlanoContaEntrada, natureza: str) -> None:
    if d.aporte_socio and (d.tipo_conta != "A" or natureza != "R"):
        raise RegraDeNegocio("Só uma conta analítica de receita pode ser marcada como aporte de sócio.")


async def criar_conta(sessao: AsyncSession, empresa: Empresa, d: PlanoContaEntrada) -> PlanoConta:
    nivel, natureza = await _validar_conta(sessao, empresa, d)
    _exigir_aporte_valido(d, natureza)
    conta = PlanoConta(
        empresa_id=empresa.id, plano_pai_id=d.plano_pai_id, codigo=d.codigo.strip(), nome=d.nome.strip(),
        tipo_conta=d.tipo_conta, natureza=natureza, nivel=nivel, aporte_socio=d.aporte_socio,
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
    _exigir_aporte_valido(d, natureza)
    if conta.aporte_socio and not d.aporte_socio and titulos:
        raise RegraDeNegocio("Há aportes lançados nesta conta: ela precisa continuar marcada como aporte de sócio.")
    if filhas and (
        d.codigo.strip() != conta.codigo or d.plano_pai_id != conta.plano_pai_id or natureza != conta.natureza
    ):
        raise RegraDeNegocio("Esta conta tem contas filhas: não é possível mudar o código, a natureza ou o pai.")
    if filhas and d.tipo_conta == "A":
        raise RegraDeNegocio("Uma conta com filhas precisa continuar sintética.")
    if titulos and (d.tipo_conta == "S" or natureza != conta.natureza):
        raise RegraDeNegocio("Há títulos lançados nesta conta: ela precisa continuar analítica e com a mesma natureza.")
    conta.plano_pai_id, conta.codigo, conta.nome = d.plano_pai_id, d.codigo.strip(), d.nome.strip()
    conta.tipo_conta, conta.natureza, conta.nivel, conta.aporte_socio = d.tipo_conta, natureza, nivel, d.aporte_socio
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


async def importar_plano_padrao(sessao: AsyncSession, empresa: Empresa) -> list[dict]:
    """Cria o plano de contas padrão numa empresa que ainda não tem nenhuma conta; nunca apaga nem mescla.

    Ids novos a cada importação. O bloqueio por empresa serializa importações simultâneas: a segunda enxerga o plano
    criado pela primeira e recebe conflito (a unicidade de código é a rede de segurança).
    """
    await sessao.execute(text("select pg_advisory_xact_lock(hashtextextended(:chave, 0))"), {"chave": f"plano-contas:{empresa.id}"})
    existentes = await sessao.scalar(select(func.count()).select_from(PlanoConta).where(PlanoConta.empresa_id == empresa.id))
    if existentes:
        raise Conflito("Esta empresa já tem plano de contas. O plano padrão só pode ser importado quando não há nenhuma conta.")
    ids: dict[str, UUID] = {}
    try:
        contas = ler_plano_padrao()
        for nivel in sorted({c.nivel for c in contas}):  # pais antes das filhas; nível e natureza também vêm do gatilho
            for c in (c for c in contas if c.nivel == nivel):
                ids[c.chave] = uuid4()
                sessao.add(PlanoConta(
                    id=ids[c.chave], empresa_id=empresa.id, plano_pai_id=ids[c.pai] if c.pai else None, codigo=c.codigo,
                    nome=c.nome, tipo_conta=c.tipo_conta, natureza=c.natureza, nivel=c.nivel,
                    aporte_socio=c.codigo == CODIGO_APORTE_SOCIO,
                ))  # fmt: skip
            await sessao.flush()
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        if "uq_plano_contas" in str(e.orig):
            raise Conflito("Esta empresa já tem plano de contas. O plano padrão só pode ser importado quando não há nenhuma conta.") from e
        raise
    return await listar_plano(sessao, empresa)


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
        "recorrencia_id": t.recorrencia_id,
    }  # fmt: skip


def _consulta_titulos(empresa: Empresa) -> Select:
    return (
        select(TituloFinanceiro)
        .options(joinedload(TituloFinanceiro.conta_bancaria), joinedload(TituloFinanceiro.plano_conta), joinedload(TituloFinanceiro.parceiro))
        .where(TituloFinanceiro.empresa_id == empresa.id)
    )  # fmt: skip


# Valor devido em SQL: espelha `regras.valor_devido` (um teste compara as duas).
_VALOR_DEVIDO = (
    TituloFinanceiro.valor_titulo - TituloFinanceiro.valor_desconto + TituloFinanceiro.valor_multa + TituloFinanceiro.valor_juros
)
_NOME_DO_PARCEIRO = select(func.lower(Parceiro.nome)).where(Parceiro.id == TituloFinanceiro.parceiro_id).scalar_subquery()
TAMANHOS_DE_PAGINA = (25, 50, 100)
LIMITE_DA_EXPORTACAO = 10_000


@dataclass(frozen=True)
class FiltroTitulos:
    """Filtros da lista de títulos; `de`/`ate` valem para o vencimento. Campos vazios não filtram."""

    tipo: str | None = None
    status: str | None = None
    busca: str | None = None
    parceiro_id: UUID | None = None
    plano_conta_id: UUID | None = None
    conta_bancaria_id: UUID | None = None
    de: date | None = None
    ate: date | None = None
    pago_de: date | None = None
    pago_ate: date | None = None
    valor_min: Decimal | None = None
    valor_max: Decimal | None = None
    recorrente: bool | None = None


def _filtrar_titulos(consulta: Select, empresa: Empresa, f: FiltroTitulos) -> Select:
    """Aplica empresa e filtros a qualquer consulta sobre `TituloFinanceiro` (listagem, contagem, totais e CSV)."""
    T = TituloFinanceiro
    consulta = consulta.where(T.empresa_id == empresa.id)
    if f.tipo:
        consulta = consulta.where(T.tipo_conta == f.tipo)
    if f.status:
        consulta = consulta.where(T.status == f.status)
    if f.parceiro_id:
        consulta = consulta.where(T.parceiro_id == f.parceiro_id)
    if f.plano_conta_id:
        consulta = consulta.where(T.plano_conta_id == f.plano_conta_id)
    if f.conta_bancaria_id:
        consulta = consulta.where(T.conta_bancaria_id == f.conta_bancaria_id)
    if f.de:
        consulta = consulta.where(T.data_vencimento >= f.de)
    if f.ate:
        consulta = consulta.where(T.data_vencimento <= f.ate)
    if f.pago_de:
        consulta = consulta.where(T.data_pagamento >= f.pago_de)
    if f.pago_ate:
        consulta = consulta.where(T.data_pagamento <= f.pago_ate)
    if f.valor_min is not None:
        consulta = consulta.where(f.valor_min <= _VALOR_DEVIDO)
    if f.valor_max is not None:
        consulta = consulta.where(f.valor_max >= _VALOR_DEVIDO)
    if f.recorrente is not None:
        consulta = consulta.where(T.recorrencia_id.is_not(None) if f.recorrente else T.recorrencia_id.is_(None))
    if f.busca and f.busca.strip():
        consulta = consulta.where(T.parceiro_id.in_(select(Parceiro.id).where(Parceiro.nome.ilike(f"%{f.busca.strip()}%"))))
    return consulta


def _ordenar_titulos(consulta: Select, ordem: str, sentido: str) -> Select:
    chave = {"vencimento": TituloFinanceiro.data_vencimento, "valor": _VALOR_DEVIDO, "parceiro": _NOME_DO_PARCEIRO}[ordem]
    chave = chave.desc() if sentido == "desc" else chave.asc()
    # o desempate mantém a ordem estável entre páginas
    return consulta.order_by(chave, TituloFinanceiro.data_vencimento, TituloFinanceiro.created_at, TituloFinanceiro.id)


async def listar_titulos(
    sessao: AsyncSession, empresa: Empresa, f: FiltroTitulos, ordem: str, sentido: str, pagina: int, tamanho: int
) -> dict:
    """Uma página de títulos, o total do filtro e os totais em aberto a receber e a pagar do filtro inteiro."""
    consulta = _ordenar_titulos(_filtrar_titulos(_consulta_titulos(empresa), empresa, f), ordem, sentido)
    consulta = consulta.limit(tamanho).offset((pagina - 1) * tamanho)
    itens = [_linha_titulo(t) for t in (await sessao.scalars(consulta)).unique().all()]
    total = await sessao.scalar(_filtrar_titulos(select(func.count()).select_from(TituloFinanceiro), empresa, f))
    somas = await sessao.execute(
        _filtrar_titulos(
            select(TituloFinanceiro.tipo_conta, func.coalesce(func.sum(_VALOR_DEVIDO), ZERO)).where(TituloFinanceiro.status == "A"),
            empresa,
            f,
        ).group_by(TituloFinanceiro.tipo_conta)
    )
    por_tipo = {tipo: valor for tipo, valor in somas.all()}
    return {"itens": itens, "total": total or 0, "totais": {"a_receber": por_tipo.get("R", ZERO), "a_pagar": por_tipo.get("P", ZERO)}}


_SITUACAO = {"A": "Aberto", "Q": "Quitado", "C": "Cancelado"}
_TIPO = {"P": "A pagar", "R": "A receber"}
CABECALHO_CSV = (
    "Vencimento", "Tipo", "Parceiro", "Conta do plano", "Conta bancária", "Valor do título", "Desconto", "Multa", "Juros",
    "Valor devido", "Situação", "Data de pagamento", "Valor pago", "Anotação",
)  # fmt: skip


def _texto_csv(valor: str | None) -> str:
    """Neutraliza campo que uma planilha interpretaria como fórmula."""
    valor = valor or ""
    return "'" + valor if valor[:1] in ("=", "+", "-", "@", "\t", "\r") else valor


def _numero_csv(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")


def _data_csv(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


async def exportar_titulos_csv(sessao: AsyncSession, empresa: Empresa, f: FiltroTitulos, ordem: str, sentido: str) -> tuple[bytes, bool]:
    """CSV do filtro inteiro, sem paginação, para planilhas em português (UTF-8 com BOM, `;`, vírgula decimal).

    Devolve também se o limite de linhas cortou o resultado."""
    consulta = _ordenar_titulos(_filtrar_titulos(_consulta_titulos(empresa), empresa, f), ordem, sentido).limit(LIMITE_DA_EXPORTACAO + 1)
    titulos = [_linha_titulo(t) for t in (await sessao.scalars(consulta)).unique().all()]
    truncado = len(titulos) > LIMITE_DA_EXPORTACAO
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(CABECALHO_CSV)
    for t in titulos[:LIMITE_DA_EXPORTACAO]:
        escritor.writerow([
            _data_csv(t["data_vencimento"]), _TIPO[t["tipo_conta"]], _texto_csv(t["parceiro_nome"]),
            _texto_csv(f"{t['plano_conta_codigo']} {t['plano_conta_nome']}"), _texto_csv(t["conta_bancaria_nome"]),
            _numero_csv(t["valor_titulo"]), _numero_csv(t["valor_desconto"]), _numero_csv(t["valor_multa"]),
            _numero_csv(t["valor_juros"]), _numero_csv(t["valor_devido"]), _SITUACAO[t["status"]],
            _data_csv(t["data_pagamento"]), _numero_csv(t["valor_quitacao"]), _texto_csv(t["anotacao"]),
        ])  # fmt: skip
    return ("\ufeff" + saida.getvalue()).encode("utf-8"), truncado


async def _titulo_completo(sessao: AsyncSession, empresa: Empresa, id_: UUID) -> dict:
    consulta = _consulta_titulos(empresa).where(TituloFinanceiro.id == id_).execution_options(populate_existing=True)
    return _linha_titulo((await sessao.scalars(consulta)).unique().one())


async def _campos_validados(sessao: AsyncSession, empresa: Empresa, d: TituloEntrada) -> dict:
    """RN03/RN04 e coerência da quitação, com mensagens claras (o banco repete as regras)."""
    await _obter(sessao, ContaBancaria, d.conta_bancaria_id, empresa, "Conta bancária")
    await _obter(sessao, Parceiro, d.parceiro_id, empresa, "Parceiro")
    conta = await _obter(sessao, PlanoConta, d.plano_conta_id, empresa, "Conta do plano de contas")
    papeis = set((await sessao.scalars(select(ParceiroPapel.papel).where(ParceiroPapel.parceiro_id == d.parceiro_id))).all())
    if d.tipo_conta == "P" and not regras.parceiro_pode_receber_pagamento(papeis):
        raise RegraDeNegocio("Conta a pagar exige um parceiro fornecedor, funcionário ou sócio. Ajuste os papéis do parceiro.")
    if conta.aporte_socio and not regras.parceiro_pode_aportar(papeis):
        raise RegraDeNegocio("Aporte de sócio exige um parceiro com o papel de sócio.")
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

    async def somar(coluna_data, valor, tipo: str, status: str, aporte: bool = False) -> dict[int, Decimal]:  # noqa: ANN001
        mes = extract("month", coluna_data)
        inicio, fim = date(ano, 1, 1), date(ano + 1, 1, 1)
        linhas = await sessao.execute(
            select(mes, func.coalesce(func.sum(valor), 0))
            .join(PlanoConta, PlanoConta.id == t.plano_conta_id)
            .where(t.empresa_id == empresa.id, t.tipo_conta == tipo, t.status == status, coluna_data >= inicio, coluna_data < fim, PlanoConta.aporte_socio == aporte)
            .group_by(mes)
        )  # fmt: skip
        return {int(m): v for m, v in linhas.all()}

    # Aportes de sócio entram no caixa (e no saldo), mas ficam fora das entradas operacionais.
    ent_real = await somar(t.data_pagamento, t.valor_quitacao, "R", "Q")
    sai_real = await somar(t.data_pagamento, t.valor_quitacao, "P", "Q")
    ent_prev = await somar(t.data_vencimento, devido, "R", "A")
    sai_prev = await somar(t.data_vencimento, devido, "P", "A")
    apo_real = await somar(t.data_pagamento, t.valor_quitacao, "R", "Q", aporte=True)
    apo_prev = await somar(t.data_vencimento, devido, "R", "A", aporte=True)

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
        ar, ap = apo_real.get(m, ZERO), apo_prev.get(m, ZERO)
        saldo = er + ep + ar + ap - sr - sp
        acumulado += saldo
        meses.append({"mes": m, "entradas_realizadas": er, "entradas_previstas": ep, "aportes_realizados": ar, "aportes_previstos": ap, "saidas_realizadas": sr, "saidas_previstas": sp, "saldo_do_mes": saldo, "saldo_acumulado": acumulado})  # fmt: skip

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
        "total_aportes": sum((m["aportes_realizados"] + m["aportes_previstos"] for m in meses), ZERO),
        "total_saidas": sum((m["saidas_realizadas"] + m["saidas_previstas"] for m in meses), ZERO),
    }  # fmt: skip
