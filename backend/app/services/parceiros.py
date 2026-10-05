"""Cadastro único de parceiros (hub de papéis): regras compartilhadas por clientes e pelo módulo financeiro."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.errors import NaoEncontrado, RegraDeNegocio
from app.financeiro import regras
from app.models import (
    Empresa,
    LancamentoReceita,
    Municipio,
    Negocio,
    Orcamento,
    PapelParceiro,
    Parceiro,
    ParceiroPapel,
    ParceiroTag,
    Projeto,
    Tarefa,
)
from app.services.base import conferir_versao, confirmar

PAPEL_CLIENTE = "cliente"


async def empresa_atual(sessao: AsyncSession) -> Empresa:
    """Resolve a empresa validada na dependência da requisição; scripts devem defini-la explicitamente."""
    empresa_id = sessao.info.get("empresa_id")
    empresa = await sessao.get(Empresa, empresa_id) if isinstance(empresa_id, UUID) else None
    if empresa is None:
        raise RegraDeNegocio("Defina uma empresa ativa antes de acessar os dados operacionais.")
    return empresa


def consulta() -> object:
    return select(Parceiro).options(selectinload(Parceiro.papeis), joinedload(Parceiro.municipio))


async def listar(
    sessao: AsyncSession, empresa: Empresa, papel: str | None = None, busca: str | None = None,
    tag_ids: Iterable[UUID] | None = None,
) -> list[Parceiro]:
    q = consulta().where(Parceiro.empresa_id == empresa.id).order_by(Parceiro.nome)  # type: ignore[attr-defined]
    if papel:
        q = q.where(exists().where(
            ParceiroPapel.empresa_id == empresa.id,
            ParceiroPapel.parceiro_id == Parceiro.id,
            ParceiroPapel.papel == papel,
        ))
    tags = set(tag_ids or ())
    if tags:
        q = q.where(exists().where(
            ParceiroTag.empresa_id == empresa.id,
            ParceiroTag.parceiro_id == Parceiro.id,
            ParceiroTag.tag_id.in_(tags),
        ))
    if busca:
        digitos = regras.so_digitos(busca)
        criterio = Parceiro.nome.ilike(f"%{busca.strip()}%")
        if digitos:
            criterio = criterio | Parceiro.cpf_cnpj.ilike(f"%{digitos}%")
        q = q.where(criterio)
    return list((await sessao.scalars(q)).unique().all())


async def obter_completo(sessao: AsyncSession, empresa: Empresa, id_: UUID, papel: str | None = None) -> Parceiro:
    q = consulta().where(Parceiro.id == id_, Parceiro.empresa_id == empresa.id)  # type: ignore[attr-defined]
    if papel:
        q = q.where(exists().where(
            ParceiroPapel.empresa_id == empresa.id,
            ParceiroPapel.parceiro_id == Parceiro.id,
            ParceiroPapel.papel == papel,
        ))
    parceiro = (await sessao.scalars(q.execution_options(populate_existing=True))).unique().first()
    if parceiro is None:
        raise NaoEncontrado("Cliente" if papel == PAPEL_CLIENTE else "Parceiro")
    return parceiro


async def exigir_cliente(sessao: AsyncSession, id_: UUID) -> Parceiro:
    """Garante que o id é de um parceiro com o papel de cliente (negócios, orçamentos etc. exigem isso)."""
    return await obter_completo(sessao, await empresa_atual(sessao), id_, PAPEL_CLIENTE)


async def listar_papeis(sessao: AsyncSession) -> list[PapelParceiro]:
    return list(
        (await sessao.scalars(select(PapelParceiro).where(PapelParceiro.ativo).order_by(PapelParceiro.nome))).all()
    )


async def _validar(sessao: AsyncSession, campos: dict) -> None:
    doc = campos.get("cpf_cnpj")
    if doc and not regras.documento_valido(campos["tipo_pessoa"], doc):
        raise RegraDeNegocio(
            f"{'CPF' if campos['tipo_pessoa'] == 'PF' else 'CNPJ'} inválido. Confira os números digitados."
        )
    if campos.get("cep") and len(campos["cep"]) != 8:
        raise RegraDeNegocio("O CEP deve ter 8 dígitos.")
    if campos.get("municipio_id") and await sessao.get(Municipio, campos["municipio_id"]) is None:
        raise RegraDeNegocio("Escolha um município válido.")


async def _papeis_validos(sessao: AsyncSession, codigos: Iterable[str]) -> set[str]:
    codigos = set(codigos)
    if not codigos:
        raise RegraDeNegocio("Escolha pelo menos um papel (cliente, fornecedor, funcionário…).")
    ativos = {p.codigo for p in await listar_papeis(sessao)}
    desconhecidos = codigos - ativos
    if desconhecidos:
        raise RegraDeNegocio(f"Papel inválido: {', '.join(sorted(desconhecidos))}.")
    return codigos


async def _vinculos_como_cliente(sessao: AsyncSession, id_: UUID) -> int:
    total = 0
    for modelo in (Negocio, Orcamento, LancamentoReceita, Projeto, Tarefa):
        total += await sessao.scalar(select(func.count()).select_from(modelo).where(modelo.cliente_id == id_)) or 0
    return total


async def criar(sessao: AsyncSession, empresa: Empresa, campos: dict, papeis: Iterable[str]) -> Parceiro:
    await _validar(sessao, campos)
    codigos = await _papeis_validos(sessao, papeis)
    parceiro = Parceiro(empresa_id=empresa.id, **campos, papeis=[ParceiroPapel(papel=c) for c in sorted(codigos)])
    sessao.add(parceiro)
    await _confirmar(sessao)
    return await obter_completo(sessao, empresa, parceiro.id)


async def atualizar(
    sessao: AsyncSession, empresa: Empresa, id_: UUID, campos: dict, versao: int, papeis: Iterable[str] | None = None
) -> Parceiro:
    parceiro = await obter_completo(sessao, empresa, id_)
    conferir_versao(parceiro, versao)
    await _validar(sessao, campos)
    for nome, valor in campos.items():
        setattr(parceiro, nome, valor)
    if papeis is not None:
        novos = await _papeis_validos(sessao, papeis)
        atuais = set(parceiro.codigos_de_papel)
        if PAPEL_CLIENTE in atuais - novos and await _vinculos_como_cliente(sessao, id_):
            raise RegraDeNegocio(
                "Este parceiro tem negócios, orçamentos, projetos, tarefas ou lançamentos como cliente e não pode deixar de ser cliente."
            )
        parceiro.papeis[:] = [p for p in parceiro.papeis if p.papel in novos] + [
            ParceiroPapel(papel=c) for c in sorted(novos - atuais)
        ]
    await _confirmar(sessao)
    return await obter_completo(sessao, empresa, id_)


async def excluir(sessao: AsyncSession, empresa: Empresa, id_: UUID, papel: str | None = None) -> None:
    """Exclui o parceiro. Com `papel` (fachada de clientes): se ele tem outros papéis, só retira esse papel."""
    parceiro = await obter_completo(sessao, empresa, id_, papel)
    if papel == PAPEL_CLIENTE and await _vinculos_como_cliente(sessao, id_):
        raise RegraDeNegocio(
            "Este cliente tem negócios, orçamentos, projetos, tarefas ou faturamento. Exclua esses registros antes."
        )
    outros = [p for p in parceiro.papeis if p.papel != papel] if papel else []
    if papel and outros:
        parceiro.papeis[:] = outros
        await confirmar(sessao)
        return
    from app.financeiro.models import TituloFinanceiro  # evita ciclo: o módulo financeiro importa este serviço

    if await sessao.scalar(
        select(func.count()).select_from(TituloFinanceiro).where(TituloFinanceiro.parceiro_id == id_)
    ):
        raise RegraDeNegocio("Há títulos financeiros deste parceiro. Exclua ou mude esses títulos antes.")
    if await _vinculos_como_cliente(sessao, id_):
        raise RegraDeNegocio(
            "Este parceiro tem negócios, orçamentos, projetos, tarefas ou lançamentos como cliente. Exclua esses registros antes."
        )
    await sessao.delete(parceiro)
    await confirmar(sessao)


async def _confirmar(sessao: AsyncSession) -> None:
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        raise RegraDeNegocio("Já existe um parceiro com este CPF/CNPJ.") from e
