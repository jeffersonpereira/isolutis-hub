"""Geração de PDF para relatórios financeiros (DRE e Fluxo de Caixa) com ReportLab.

Puro Python — sem dependência de bibliotecas nativas de sistema (ao contrário do
WeasyPrint, que exigia Pango/Cairo e nunca funcionou no runtime de função da Vercel).
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

from app.documents.reportlab_base import (
    BAD,
    MARGEM,
    NAVY,
    OK,
    SOFT,
    TEXTO,
    WHITE,
    CanvasPaginado,
    Identidade,
    brl,
    cabecalho_fiscal,
    cards_kpi,
    grafico_barras_mensal,
)

_COLUNAS_DRE = ["Mês", "Receitas", "Custos", "Resultado"]
_COLUNAS_FLUXO = ["Mês", "Entradas", "Saídas", "Saldo do Mês", "Saldo Acumulado"]


def _tabela_dre(dados: list[dict]) -> Table:
    linhas = [_COLUNAS_DRE]
    for row in dados:
        linhas.append([row["nome_mes"], brl(row["receitas"]), brl(row["custos"]), brl(row["resultado"])])
    total_receitas = sum(r["receitas"] for r in dados)
    total_custos = sum(r["custos"] for r in dados)
    linhas.append(["Total", brl(total_receitas), brl(total_custos), brl(total_receitas - total_custos)])
    return _montar_tabela(linhas, [coluna_resultado_cor(r["resultado"]) for r in dados] + [True])


def _tabela_fluxo(dados: list[dict]) -> Table:
    linhas = [_COLUNAS_FLUXO]
    for row in dados:
        linhas.append([
            row["nome_mes"], brl(row["entradas"]), brl(row["saidas"]),
            brl(row["saldo_mes"]), brl(row["saldo_acumulado"]),
        ])  # fmt: skip
    return _montar_tabela(linhas, [coluna_resultado_cor(r["saldo_mes"]) for r in dados])


def coluna_resultado_cor(valor: float) -> bool:
    return valor >= 0


def _montar_tabela(linhas: list[list[str]], cores_ultima_coluna: list[bool]) -> Table:
    n_colunas = len(linhas[0])
    tabela = Table(linhas, colWidths=None, repeatRows=1)
    estilo = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#D3DBE6")),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, NAVY),
        ("BACKGROUND", (0, -1), (-1, -1), SOFT),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]  # fmt: skip
    for i, positivo in enumerate(cores_ultima_coluna, start=1):
        estilo.append(("TEXTCOLOR", (n_colunas - 1, i), (n_colunas - 1, i), OK if positivo else BAD))
    tabela.setStyle(TableStyle(estilo))
    return tabela


def relatorio_pdf(dados: list[dict], tipo: str, empresa: Identidade, ano: int) -> bytes:
    """Gera PDF do relatório financeiro (DRE ou Fluxo de Caixa) com ReportLab.

    Args:
        dados: Lista de dicionários com os dados mensais (saída de ``calcular_dre``/``calcular_fluxo_caixa``).
        tipo: ``'dre'`` ou ``'fluxo_caixa'``.
        empresa: Identidade de quem emite o relatório (nome, logo, dados fiscais).
        ano: Ano de referência do relatório.

    Returns:
        Conteúdo do PDF como bytes.
    """
    titulo = "Demonstrativo de Resultado" if tipo == "dre" else "Fluxo de Caixa"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=MARGEM + 6 * mm,
    )  # fmt: skip

    story = [cabecalho_fiscal(empresa, titulo, f"Ano {ano}"), Spacer(1, 14)]

    if tipo == "dre":
        total_receitas = sum(r["receitas"] for r in dados)
        total_custos = sum(r["custos"] for r in dados)
        total_resultado = total_receitas - total_custos
        story.append(cards_kpi([
            ("Receita Total", brl(total_receitas), None),
            ("Custo Total", brl(total_custos), None),
            ("Resultado", brl(total_resultado), total_resultado >= 0),
        ]))  # fmt: skip
        if dados:
            story.append(Spacer(1, 14))
            story.append(grafico_barras_mensal(
                [r["nome_mes"] for r in dados],
                [("Receitas", [float(r["receitas"]) for r in dados], NAVY),
                 ("Custos", [float(r["custos"]) for r in dados], BAD)],
            ))  # fmt: skip
        story.append(Spacer(1, 14))
        story.append(_tabela_dre(dados))
    else:
        total_entradas = sum(r["entradas"] for r in dados)
        total_saidas = sum(r["saidas"] for r in dados)
        saldo_final = dados[-1]["saldo_acumulado"] if dados else 0
        story.append(cards_kpi([
            ("Entradas Totais", brl(total_entradas), None),
            ("Saídas Totais", brl(total_saidas), None),
            ("Saldo Acumulado", brl(saldo_final), saldo_final >= 0),
        ]))  # fmt: skip
        if dados:
            story.append(Spacer(1, 14))
            story.append(grafico_barras_mensal(
                [r["nome_mes"] for r in dados],
                [("Entradas", [float(r["entradas"]) for r in dados], NAVY),
                 ("Saídas", [float(r["saidas"]) for r in dados], BAD)],
            ))  # fmt: skip
        story.append(Spacer(1, 14))
        story.append(_tabela_fluxo(dados))

    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: CanvasPaginado(*args, rodape_esquerda=empresa.nome, **kwargs),
    )
    return buffer.getvalue()
