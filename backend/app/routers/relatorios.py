"""Endpoints de relatórios financeiros: DRE e Fluxo de Caixa."""

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.deps import EmpresaAtual, Sessao, UsuarioLogado
from app.documents.relatorio_pdf import relatorio_pdf
from app.documents.relatorio_xlsx import relatorio_xlsx
from app.errors import ErroApp
from app.services.relatorios import calcular_dre, calcular_fluxo_caixa

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

_ANO_ATUAL = datetime.now().year


@router.get("/dre", response_model=None)
async def dre(
    sessao: Sessao,
    _usuario: UsuarioLogado,
    empresa: EmpresaAtual,
    ano: int = Query(default=_ANO_ATUAL, ge=2000, le=2100),
    formato: str = Query(default="json", pattern="^(json|pdf|xlsx)$"),
) -> Response | list[dict]:
    """DRE mensal do ano. Formato: json (padrão), pdf ou xlsx."""
    dados = await calcular_dre(sessao, empresa.id, ano)

    if formato == "pdf":
        try:
            pdf_bytes = relatorio_pdf(dados, "dre", empresa.nome, ano)
        except Exception as exc:
            raise ErroApp(
                "Não foi possível gerar o PDF. Tente novamente.",
                codigo="pdf_indisponivel",
                status=500,
            ) from exc
        nome = f"DRE-{empresa.nome}-{ano}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
        )

    if formato == "xlsx":
        fluxo = await calcular_fluxo_caixa(sessao, empresa.id, ano)
        try:
            xlsx_bytes = relatorio_xlsx(dados, fluxo, empresa.nome, ano)
        except Exception as exc:
            raise ErroApp(
                "Não foi possível gerar a planilha. Tente novamente.",
                codigo="xlsx_indisponivel",
                status=500,
            ) from exc
        nome = f"Relatorios-{empresa.nome}-{ano}.xlsx"
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
        )

    return dados


@router.get("/fluxo-caixa", response_model=None)
async def fluxo_caixa(
    sessao: Sessao,
    _usuario: UsuarioLogado,
    empresa: EmpresaAtual,
    ano: int = Query(default=_ANO_ATUAL, ge=2000, le=2100),
    formato: str = Query(default="json", pattern="^(json|pdf|xlsx)$"),
) -> Response | list[dict]:
    """Fluxo de Caixa mensal do ano. Formato: json (padrão), pdf ou xlsx."""
    dados = await calcular_fluxo_caixa(sessao, empresa.id, ano)

    if formato == "pdf":
        try:
            pdf_bytes = relatorio_pdf(dados, "fluxo_caixa", empresa.nome, ano)
        except Exception as exc:
            raise ErroApp(
                "Não foi possível gerar o PDF. Tente novamente.",
                codigo="pdf_indisponivel",
                status=500,
            ) from exc
        nome = f"FluxoCaixa-{empresa.nome}-{ano}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
        )

    if formato == "xlsx":
        dre_dados = await calcular_dre(sessao, empresa.id, ano)
        try:
            xlsx_bytes = relatorio_xlsx(dre_dados, dados, empresa.nome, ano)
        except Exception as exc:
            raise ErroApp(
                "Não foi possível gerar a planilha. Tente novamente.",
                codigo="xlsx_indisponivel",
                status=500,
            ) from exc
        nome = f"Relatorios-{empresa.nome}-{ano}.xlsx"
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome)}"},
        )

    return dados
