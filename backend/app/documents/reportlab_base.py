"""Elementos de composição compartilhados entre os PDFs gerados em ReportLab
(relatórios financeiros e orçamento): cores, cabeçalho fiscal, cards de KPI,
gráfico de barras mensal e rodapé com paginação/timestamp.

Puro Python (ReportLab + Pillow) — sem dependência de bibliotecas nativas de
sistema, para funcionar no runtime de função Python da Vercel.
"""

import base64
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from xml.sax.saxutils import escape as _escape_xml

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#1B2B4B")
TEAL = colors.HexColor("#22C3CE")
SOFT = colors.HexColor("#EEF1F6")
WHITE = colors.white
TEXTO = colors.HexColor("#16223B")
TEXTO_SUAVE = colors.HexColor("#56647A")
OK = colors.HexColor("#4A9D6F")
BAD = colors.HexColor("#A85D52")

MARGEM = 15 * mm
LARGURA_UTIL = A4[0] - 2 * MARGEM

ESTILO_EMPRESA = ParagraphStyle("empresa", fontName="Helvetica-Bold", fontSize=8, textColor=TEXTO_SUAVE, leading=11)
ESTILO_TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, leading=20)
ESTILO_SUBTITULO = ParagraphStyle("subtitulo", fontName="Helvetica", fontSize=10, textColor=TEXTO_SUAVE, leading=13)
ESTILO_FISCAL = ParagraphStyle("fiscal", fontName="Helvetica", fontSize=9, textColor=TEXTO_SUAVE, leading=12)
ESTILO_KPI_ROTULO = ParagraphStyle(
    "kpi_rotulo", fontName="Helvetica-Bold", fontSize=8, textColor=TEXTO_SUAVE, leading=10
)
ESTILO_KPI_VALOR = ParagraphStyle("kpi_valor", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, leading=18)


def brl(valor: Decimal | float | None) -> str:
    """Formata número como Real Brasileiro: R$ 1.234,56"""
    texto = f"{Decimal(str(valor or 0)):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def esc(texto: str | None) -> str:
    """Escapa texto de origem externa (cadastro da empresa/cliente) antes de embutir em um
    ``Paragraph`` do ReportLab — que interpreta um subconjunto de XML (``<b>``, ``<br/>`` etc.) e
    lança erro ou corrompe o layout se o texto tiver `<`/`&`/`>` não escapados."""
    return _escape_xml(texto or "")


def _logo_reader(logo_data_url: str | None) -> io.BytesIO | None:
    """Decodifica um data URL (``data:image/...;base64,...``) em bytes legíveis pelo ReportLab."""
    if not logo_data_url or "base64," not in logo_data_url:
        return None
    _, b64 = logo_data_url.split("base64,", 1)
    return io.BytesIO(base64.b64decode(b64))


def _logo_imagem(logo_data_url: str | None) -> Image | None:
    """Decodifica a logomarca para uma `Image` do ReportLab, ou ``None`` se não houver logo ou se os
    bytes armazenados não formarem uma imagem válida (o cadastro só confere a assinatura do arquivo,
    não o conteúdo completo) — nesse caso o cabeçalho degrada para texto, em vez de falhar o PDF."""
    leitor = _logo_reader(logo_data_url)
    if not leitor:
        return None
    try:
        imagem = Image(leitor)
        imagem._restrictSize(40 * mm, 18 * mm)
        return imagem
    except Exception:
        return None


@dataclass(frozen=True)
class Identidade:
    """Quem emite o documento: dados do cadastro da empresa e a logomarca dela (data URL), se houver."""

    nome: str
    subtitulo: str | None = None
    documento: str | None = None
    contato: str | None = None
    endereco: str | None = None
    logo: str | None = None

    @property
    def rodape(self) -> str:
        return " · ".join(p for p in (self.nome, self.subtitulo, self.documento, self.contato) if p)


def cabecalho_fiscal(empresa: Identidade, titulo: str, subtitulo: str | None = None) -> Table:
    """Cabeçalho com logomarca (se houver) + identidade fiscal à esquerda e título do documento à direita."""
    linhas_fiscais = [p for p in (empresa.documento, empresa.endereco, empresa.contato) if p]
    bloco_empresa = [Paragraph(esc(empresa.nome.upper()), ESTILO_EMPRESA)]
    if empresa.subtitulo:
        bloco_empresa.append(Paragraph(esc(empresa.subtitulo), ESTILO_FISCAL))
    bloco_empresa.extend(Paragraph(esc(linha), ESTILO_FISCAL) for linha in linhas_fiscais)

    imagem = _logo_imagem(empresa.logo)
    coluna_esquerda: list = []
    if imagem:
        coluna_esquerda.append(imagem)
    coluna_esquerda.append(Spacer(1, 4) if imagem else Spacer(0, 0))
    coluna_esquerda.extend(bloco_empresa)

    bloco_titulo = [Paragraph(esc(titulo), ESTILO_TITULO)]
    if subtitulo:
        bloco_titulo.append(Paragraph(esc(subtitulo), ESTILO_SUBTITULO))

    tabela = Table(
        [[coluna_esquerda, bloco_titulo]],
        colWidths=[LARGURA_UTIL * 0.55, LARGURA_UTIL * 0.45],
    )
    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, 0), 2, NAVY),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )  # fmt: skip
    return tabela


def cards_kpi(itens: list[tuple[str, str, bool | None]]) -> Table:
    """Linha de cards de indicador: cada item é (rótulo, valor formatado, positivo?).

    ``positivo`` é ``None`` para indicadores neutros (sem cor semântica).
    """
    celulas = []
    for rotulo, valor, positivo in itens:
        cor = NAVY if positivo is None else (OK if positivo else BAD)
        estilo_valor = ParagraphStyle("kpi_valor_cor", parent=ESTILO_KPI_VALOR, textColor=cor)
        celulas.append([Paragraph(rotulo.upper(), ESTILO_KPI_ROTULO), Paragraph(valor, estilo_valor)])

    largura_card = LARGURA_UTIL / len(celulas)
    tabela = Table([celulas], colWidths=[largura_card] * len(celulas))
    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("BOX", (0, 0), (0, 0), 0, WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("INNERGRID", (0, 0), (-1, -1), 6, WHITE),
        ])
    )  # fmt: skip
    return tabela


def grafico_barras_mensal(
    categorias: list[str], series: list[tuple[str, list[float], colors.Color]], altura: float = 45 * mm
) -> Drawing:
    """Gráfico de barras com um mês por categoria e até duas séries (ex.: Receitas vs Custos)."""
    largura = LARGURA_UTIL
    desenho = Drawing(largura, altura + 12 * mm)
    grafico = VerticalBarChart()
    grafico.x = 10
    grafico.y = 10
    grafico.height = altura
    grafico.width = largura - 90
    grafico.data = [serie[1] for serie in series]
    grafico.categoryAxis.categoryNames = categorias
    grafico.categoryAxis.labels.fontSize = 6.5
    grafico.categoryAxis.labels.fontName = "Helvetica"
    grafico.valueAxis.labels.fontSize = 6.5
    grafico.valueAxis.labels.fontName = "Helvetica"
    grafico.valueAxis.valueMin = 0
    grafico.barSpacing = 2
    grafico.groupSpacing = 8
    for i, (_nome, _valores, cor) in enumerate(series):
        grafico.bars[i].fillColor = cor
        grafico.bars[i].strokeColor = None
    desenho.add(grafico)

    legenda = Legend()
    legenda.x = largura - 75
    legenda.y = altura / 2
    legenda.alignment = "right"
    legenda.fontName = "Helvetica"
    legenda.fontSize = 8
    legenda.colorNamePairs = [(cor, nome) for nome, _valores, cor in series]
    desenho.add(legenda)
    return desenho


class CanvasPaginado(Canvas):
    """Canvas que desenha, ao final, 'Página N de M' + timestamp de geração no rodapé de cada página."""

    def __init__(self, *args: object, rodape_esquerda: str = "", **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._paginas: list[bytes] = []
        self._rodape_esquerda = rodape_esquerda

    def showPage(self) -> None:
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._paginas)
        estado_atual = dict(self.__dict__)
        for i, estado in enumerate(self._paginas, start=1):
            self.__dict__.update(estado)
            self._desenhar_rodape(i, total)
            super().showPage()
        self.__dict__.update(estado_atual)
        super().save()

    def _desenhar_rodape(self, pagina: int, total: int) -> None:
        gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXTO_SUAVE)
        y = MARGEM - 8
        if self._rodape_esquerda:
            self.drawString(MARGEM, y, f"{self._rodape_esquerda} · Gerado em {gerado_em}")
        else:
            self.drawString(MARGEM, y, f"Gerado em {gerado_em}")
        self.drawRightString(A4[0] - MARGEM, y, f"Página {pagina} de {total}")
