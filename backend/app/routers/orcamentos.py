from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.deps import Sessao
from app.documents.render import orcamento_pdf, slug
from app.errors import ErroApp
from app.schemas.orcamento import AprovacaoSaida, OrcamentoAtualizar, OrcamentoEntrada, OrcamentoLeitura, StatusExibido
from app.services import orcamentos as svc
from app.services.parceiros import exigir_cliente

router = APIRouter(prefix="/orcamentos", tags=["Orçamentos"])


@router.get("", response_model=list[OrcamentoLeitura])
async def listar(sessao: Sessao, status: StatusExibido | None = Query(None)):
    return await svc.listar(sessao, status)


@router.post("", response_model=OrcamentoLeitura, status_code=201)
async def criar(dados: OrcamentoEntrada, sessao: Sessao):
    return await svc.criar(sessao, dados)


@router.put("/{id_}", response_model=OrcamentoLeitura)
async def atualizar(id_: UUID, dados: OrcamentoAtualizar, sessao: Sessao):
    return await svc.atualizar(sessao, id_, dados)


@router.post("/{id_}/aprovar", response_model=AprovacaoSaida)
async def aprovar(id_: UUID, sessao: Sessao) -> AprovacaoSaida:
    orc = await svc.aprovar(sessao, id_)
    return AprovacaoSaida(orcamento=OrcamentoLeitura.model_validate(orc), negocio_id=orc.negocio_id)


@router.delete("/{id_}", status_code=204)
async def excluir(id_: UUID, sessao: Sessao) -> Response:
    await svc.excluir(sessao, id_)
    return Response(status_code=204)


@router.get("/{id_}/documento", response_class=Response)
async def documento(id_: UUID, sessao: Sessao) -> Response:
    orc = await svc.obter_completo(sessao, id_)
    cliente = await exigir_cliente(sessao, orc.cliente_id)
    try:
        pdf_bytes = orcamento_pdf(orc, cliente)
    except Exception as exc:
        raise ErroApp(
            "Não foi possível gerar o PDF. Tente novamente.",
            codigo="pdf_indisponivel",
            status=500,
        ) from exc
    nome = f"Orcamento-{orc.numero}-{slug(cliente.nome)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
    )
