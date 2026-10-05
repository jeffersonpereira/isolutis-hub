from datetime import date
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from app.deps import Sessao
from app.documents.render import projeto_html, slug
from app.models import Usuario
from app.schemas.projeto import EtapaSugerida, ModeloProjeto, ProjetoAtualizar, ProjetoEntrada, ProjetoLeitura
from app.schemas.usuario import MembroEquipe
from app.services import projetos as svc
from app.services.parceiros import exigir_cliente

router = APIRouter(prefix="/projetos", tags=["Projetos"])


@router.get("", response_model=list[ProjetoLeitura])
async def listar(sessao: Sessao):
    return await svc.listar(sessao)


@router.get("/modelo", response_model=ModeloProjeto)
async def modelo(sessao: Sessao, negocio_id: UUID = Query(...)):
    return await svc.modelo_do_negocio(sessao, negocio_id)


@router.get("/etapas-padrao", response_model=list[EtapaSugerida])
async def etapas_padrao(inicio: date | None = None, entrega: date | None = None):
    return svc.etapas_padrao(inicio, entrega)


@router.post("", response_model=ProjetoLeitura, status_code=201)
async def criar(dados: ProjetoEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/{id_}", response_model=ProjetoLeitura)
async def atualizar(id_: UUID, dados: ProjetoAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)


@router.get("/{id_}/relatorio", response_class=Response)
async def relatorio(id_: UUID, sessao: Sessao) -> Response:
    projeto = await svc.obter_completo(sessao, id_)
    cliente = await exigir_cliente(sessao, projeto.cliente_id)
    equipe = {u.id: MembroEquipe.model_validate(u) for u in (await sessao.scalars(select(Usuario))).all()}
    html = projeto_html(projeto, cliente, equipe.get(projeto.responsavel_id), equipe)
    nome = f"Plano-de-entrega-{slug(projeto.titulo)}-{slug(cliente.nome)}.html"
    return Response(
        html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
    )
