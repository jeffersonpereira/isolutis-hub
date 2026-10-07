from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.deps import Administrador, EmpresaAtual, Sessao, UsuarioLogado, usuario_atual
from app.models import Empresa, UsuarioEmpresa
from sqlalchemy import select
from sqlalchemy import text
from pydantic import BaseModel, Field
from app.schemas.convite import ConviteEntrada, ConviteLeitura
from app.schemas.usuario import MembroEquipe, UsuarioAtualizar, UsuarioCriar, UsuarioLeitura
from app.services import convites as svc_convites
from app.services import usuarios as svc
from app.services.base import confirmar

router = APIRouter(tags=["Equipe"])


class EmpresaNova(BaseModel):
    nome: str = Field(min_length=1, max_length=150)


@router.get("/empresas", dependencies=[Depends(usuario_atual)])
async def empresas_do_usuario(sessao: Sessao, usuario: UsuarioLogado) -> list[dict[str, object]]:
    """Empresas acessíveis para a seleção do contexto ativo."""
    linhas = await sessao.execute(
        select(Empresa.id, Empresa.nome, UsuarioEmpresa.papel)
        .join(UsuarioEmpresa, UsuarioEmpresa.empresa_id == Empresa.id)
        .where(UsuarioEmpresa.usuario_id == usuario.id, UsuarioEmpresa.ativo)
        .order_by(Empresa.nome)
    )
    return [{"id": str(id_), "nome": nome, "papel": papel} for id_, nome, papel in linhas]


@router.post("/empresas", status_code=201, dependencies=[Depends(usuario_atual)])
async def criar_empresa(dados: EmpresaNova, sessao: Sessao, usuario: UsuarioLogado) -> dict[str, str]:
    """Cria uma empresa e associa o solicitante como administrador inicial."""
    empresa_id = await sessao.scalar(text("select criar_empresa(:nome)"), {"nome": dados.nome})
    await sessao.commit()
    return {"id": str(empresa_id), "nome": dados.nome.strip(), "papel": "admin"}


@router.get("/equipe", response_model=list[MembroEquipe], dependencies=[Depends(usuario_atual)])
async def equipe(sessao: Sessao, empresa: EmpresaAtual) -> list[MembroEquipe]:
    """Pessoas da equipe (qualquer usuário logado): usado em responsáveis e na autoria dos registros."""
    return [MembroEquipe.model_validate(u) for u in await svc.equipe(sessao, empresa.id)]


@router.get("/usuarios", response_model=list[UsuarioLeitura], tags=["Administração"])
async def listar_usuarios(empresa: EmpresaAtual, _: Administrador, sessao: Sessao) -> list[UsuarioLeitura]:
    return [UsuarioLeitura.model_validate(u) for u in await svc.equipe(sessao, empresa.id)]


@router.post("/usuarios", response_model=UsuarioLeitura, status_code=201, tags=["Administração"])
async def criar_usuario(dados: UsuarioCriar, empresa: EmpresaAtual, _: Administrador, sessao: Sessao) -> UsuarioLeitura:
    return UsuarioLeitura.model_validate(await svc.criar(sessao, empresa.id, dados))


@router.put("/usuarios/{id_}", response_model=UsuarioLeitura, tags=["Administração"])
async def atualizar_usuario(id_: UUID, dados: UsuarioAtualizar, empresa: EmpresaAtual, quem: Administrador, sessao: Sessao) -> UsuarioLeitura:
    return UsuarioLeitura.model_validate(await svc.atualizar(sessao, quem, empresa.id, id_, dados))


@router.delete("/usuarios/{id_}", status_code=204, tags=["Administração"])
async def remover_usuario(id_: UUID, empresa: EmpresaAtual, quem: Administrador, sessao: Sessao) -> Response:
    await svc.desativar(sessao, quem, empresa.id, id_)
    return Response(status_code=204)


@router.post("/convite", status_code=201, response_model=ConviteLeitura, tags=["Administração"])
async def criar_convite_route(dados: ConviteEntrada, empresa: EmpresaAtual, quem: Administrador, sessao: Sessao) -> ConviteLeitura:
    convite = await svc_convites.criar_convite(sessao, empresa.id, dados, quem.id)
    return ConviteLeitura.model_validate(convite)


@router.get("/convites", response_model=list[ConviteLeitura], tags=["Administração"])
async def listar_convites_route(empresa: EmpresaAtual, _: Administrador, sessao: Sessao) -> list[ConviteLeitura]:
    pendentes = await svc_convites.listar_pendentes(sessao, empresa.id)
    return [ConviteLeitura.model_validate(c) for c in pendentes]


@router.delete("/convite/{convite_id}", status_code=204, tags=["Administração"])
async def cancelar_convite_route(convite_id: int, empresa: EmpresaAtual, _: Administrador, sessao: Sessao) -> Response:
    await svc_convites.cancelar_convite(sessao, convite_id, empresa.id)
    return Response(status_code=204)


class EmpresaAtualizar(BaseModel):
    nome: str = Field(min_length=1, max_length=150)


@router.patch("/empresas/ativa", status_code=204)
async def atualizar_empresa_ativa(
    dados: EmpresaAtualizar,
    empresa: EmpresaAtual,
    _: Administrador,
    sessao: Sessao,
) -> None:
    empresa.nome = dados.nome.strip()
    await confirmar(sessao)

__all__ = ["router", "UsuarioLogado"]
