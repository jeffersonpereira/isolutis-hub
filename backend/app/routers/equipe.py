"""Empresas, equipe e usuários da empresa ativa."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text

from app.deps import Administrador, EmpresaAtual, Sessao, UsuarioLogado
from app.models import Empresa, UsuarioEmpresa
from app.schemas.usuario import MembroEquipe, UsuarioAtualizar, UsuarioCriar, UsuarioLeitura
from app.services import usuarios as svc

router = APIRouter(tags=["Equipe"])


class EmpresaNova(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=150)


class EmpresaAtualizar(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=150)


@router.get("/empresas")
async def empresas_do_usuario(sessao: Sessao, usuario: UsuarioLogado) -> list[dict[str, str]]:
    linhas = await sessao.execute(
        select(Empresa.id, Empresa.nome, UsuarioEmpresa.papel)
        .join(UsuarioEmpresa, UsuarioEmpresa.empresa_id == Empresa.id)
        .where(UsuarioEmpresa.usuario_id == usuario.id, UsuarioEmpresa.ativo)
        .order_by(Empresa.nome)
    )
    return [{"id": str(id_), "nome": nome, "papel": papel} for id_, nome, papel in linhas]


@router.post("/empresas")
async def criar_empresa(dados: EmpresaNova, sessao: Sessao, usuario: UsuarioLogado) -> dict[str, str]:
    empresa_id = await sessao.scalar(text("select criar_empresa(:nome)"), {"nome": dados.nome})
    await sessao.commit()
    return {"id": str(empresa_id), "nome": dados.nome.strip(), "papel": "admin"}


@router.put("/empresas/{id_}")
async def atualizar_empresa(
    id_: UUID,
    dados: EmpresaAtualizar,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> dict[str, str]:
    if id_ != empresa.id:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    empresa.nome = dados.nome
    await sessao.commit()
    await sessao.refresh(empresa)
    return {"id": str(empresa.id), "nome": empresa.nome}


@router.get("/equipe", response_model=list[MembroEquipe], summary="Pessoas da equipe")
async def equipe(sessao: Sessao, empresa: EmpresaAtual) -> list[MembroEquipe]:
    return [MembroEquipe.model_validate(u) for u in await svc.equipe(sessao, empresa.id)]


@router.get("/usuarios", response_model=list[UsuarioLeitura], tags=["Administração"])
async def listar_usuarios(empresa: EmpresaAtual, _: Administrador, sessao: Sessao) -> list[UsuarioLeitura]:
    return [UsuarioLeitura.model_validate(u) for u in await svc.equipe(sessao, empresa.id)]


@router.post("/usuarios", response_model=UsuarioLeitura, status_code=201, tags=["Administração"])
async def criar_usuario(
    dados: UsuarioCriar,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> UsuarioLeitura:
    return UsuarioLeitura.model_validate(await svc.criar(sessao, empresa.id, dados))


@router.put("/usuarios/{id_}", response_model=UsuarioLeitura, tags=["Administração"])
async def atualizar_usuario(
    id_: UUID,
    dados: UsuarioAtualizar,
    empresa: EmpresaAtual,
    quem: UsuarioLogado,
    sessao: Sessao,
) -> UsuarioLeitura:
    return UsuarioLeitura.model_validate(await svc.atualizar(sessao, quem, empresa.id, id_, dados))


@router.delete("/usuarios/{id_}", status_code=204, tags=["Administração"])
async def remover_usuario(id_: UUID, empresa: EmpresaAtual, quem: UsuarioLogado, sessao: Sessao) -> Response:
    await svc.desativar(sessao, quem, empresa.id, id_)
    return Response(status_code=204)
