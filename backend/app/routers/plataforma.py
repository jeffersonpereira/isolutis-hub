"""Área da plataforma (operador): empresas e membros. Não expõe dados de negócio de nenhuma empresa."""

from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.deps import Sessao, SessaoOperador, UsuarioLogado
from app.schemas.convite import ConviteEntrada
from app.schemas.plataforma import (
    AcessoPlataforma,
    EmpresaDetalhe,
    EmpresaNova,
    EmpresaPlataforma,
    MembroAdicionado,
    MembroAtualizar,
    StatusEntrada,
)
from app.services import plataforma as svc

router = APIRouter(prefix="/plataforma", tags=["Plataforma"])


@router.get("/acesso", response_model=AcessoPlataforma)
async def acesso(sessao: Sessao, _: UsuarioLogado) -> AcessoPlataforma:
    """Diz ao front se mostra a área da plataforma. Qualquer usuário autenticado pode perguntar sobre si mesmo."""
    return AcessoPlataforma(operador=await svc.eh_operador(sessao))


@router.get("/empresas", response_model=list[EmpresaPlataforma])
async def listar(sessao: SessaoOperador, busca: str | None = Query(default=None, max_length=100)) -> list[EmpresaPlataforma]:
    return [EmpresaPlataforma.model_validate(e) for e in await svc.listar_empresas(sessao, busca)]


@router.post("/empresas", response_model=EmpresaPlataforma, status_code=201)
async def criar(dados: EmpresaNova, sessao: SessaoOperador) -> EmpresaPlataforma:
    return EmpresaPlataforma.model_validate(await svc.criar_empresa(sessao, dados))


@router.get("/empresas/{empresa_id}", response_model=EmpresaDetalhe)
async def detalhe(empresa_id: UUID, sessao: SessaoOperador) -> EmpresaDetalhe:
    return EmpresaDetalhe.model_validate(await svc.detalhe_empresa(sessao, empresa_id))


@router.patch("/empresas/{empresa_id}/status", response_model=EmpresaPlataforma)
async def definir_status(empresa_id: UUID, dados: StatusEntrada, sessao: SessaoOperador) -> EmpresaPlataforma:
    return EmpresaPlataforma.model_validate(await svc.definir_status(sessao, empresa_id, dados.status))


@router.post("/empresas/{empresa_id}/convites", response_model=MembroAdicionado)
async def convidar(empresa_id: UUID, dados: ConviteEntrada, sessao: SessaoOperador) -> MembroAdicionado:
    direto = await svc.convidar(sessao, empresa_id, dados)
    return MembroAdicionado(direto=direto)


@router.delete("/empresas/{empresa_id}/convites/{convite_id}", status_code=204)
async def cancelar_convite(empresa_id: UUID, convite_id: int, sessao: SessaoOperador) -> Response:
    await svc.cancelar_convite(sessao, empresa_id, convite_id)
    return Response(status_code=204)


@router.patch("/empresas/{empresa_id}/membros/{usuario_id}", status_code=204)
async def definir_membro(empresa_id: UUID, usuario_id: UUID, dados: MembroAtualizar, sessao: SessaoOperador) -> Response:
    await svc.definir_membro(sessao, empresa_id, usuario_id, dados.papel, dados.ativo)
    return Response(status_code=204)
