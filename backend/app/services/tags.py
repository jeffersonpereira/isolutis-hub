"""Classificações personalizadas de parceiros, isoladas por empresa."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import NaoEncontrado, RegraDeNegocio
from app.models import Empresa, Parceiro, ParceiroTag, TagParceiro
from app.services.base import confirmar


async def listar(sessao: AsyncSession, empresa: Empresa) -> list[TagParceiro]:
    return list((await sessao.scalars(
        select(TagParceiro).where(TagParceiro.empresa_id == empresa.id).order_by(TagParceiro.nome)
    )).all())


async def criar(sessao: AsyncSession, empresa: Empresa, nome: str) -> TagParceiro:
    tag = TagParceiro(empresa_id=empresa.id, nome=nome.strip())
    sessao.add(tag)
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        raise RegraDeNegocio("Já existe uma tag com esse nome nesta empresa.") from e
    return tag


async def arquivar(sessao: AsyncSession, empresa: Empresa, tag_id: UUID) -> TagParceiro:
    tag = await sessao.scalar(select(TagParceiro).where(TagParceiro.id == tag_id, TagParceiro.empresa_id == empresa.id))
    if tag is None:
        raise NaoEncontrado("Tag")
    tag.ativo = False
    await confirmar(sessao)
    return tag


async def atualizar(sessao: AsyncSession, empresa: Empresa, tag_id: UUID, nome: str) -> TagParceiro:
    tag = await sessao.scalar(select(TagParceiro).where(TagParceiro.id == tag_id, TagParceiro.empresa_id == empresa.id))
    if tag is None:
        raise NaoEncontrado("Tag")
    tag.nome = nome.strip()
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        raise RegraDeNegocio("Já existe uma tag com esse nome nesta empresa.") from e
    return tag


async def atribuir(sessao: AsyncSession, empresa: Empresa, parceiro_id: UUID, tag_ids: list[UUID]) -> None:
    parceiro = await sessao.scalar(select(Parceiro.id).where(
        Parceiro.id == parceiro_id, Parceiro.empresa_id == empresa.id
    ))
    if parceiro is None:
        raise NaoEncontrado("Parceiro")
    ids = set(tag_ids)
    tags = set((await sessao.scalars(select(TagParceiro.id).where(
        TagParceiro.empresa_id == empresa.id, TagParceiro.ativo, TagParceiro.id.in_(ids)
    ))).all()) if ids else set()
    if tags != ids:
        raise RegraDeNegocio("Uma ou mais tags estão indisponíveis nesta empresa.")
    await sessao.execute(ParceiroTag.__table__.delete().where(
        ParceiroTag.empresa_id == empresa.id, ParceiroTag.parceiro_id == parceiro_id
    ))
    sessao.add_all(ParceiroTag(empresa_id=empresa.id, parceiro_id=parceiro_id, tag_id=tag_id) for tag_id in sorted(ids, key=str))
    await confirmar(sessao)
