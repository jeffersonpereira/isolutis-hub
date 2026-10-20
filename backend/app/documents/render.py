"""Geração dos documentos para o cliente: orçamento (PDF, ReportLab) e plano de
entrega do projeto (HTML, Jinja2 — pensado para "Imprimir → Salvar como PDF" do navegador).
"""

import base64
import io
import re
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.documents.reportlab_base import MARGEM, NAVY, SOFT, TEXTO, TEXTO_SUAVE, Identidade, brl, cabecalho_fiscal, esc
from app.domain.datas import hoje
from app.models import Orcamento, Parceiro, Projeto
from app.schemas.usuario import MembroEquipe

PASTA = Path(__file__).parent
MES3 = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
STATUS_PROJETO = {
    "planejamento": "Planejamento", "construcao": "Em construção", "validacao": "Em validação",
    "entregue": "Entregue", "pausado": "Pausado",
}  # fmt: skip
STATUS_ETAPA = {"a_fazer": "A fazer", "andamento": "Em andamento", "concluida": "Concluída"}

PADRAO = Identidade(nome="iSolutis", subtitulo="Soluções e Inovações Tecnológicas")

_ESTILO_CLIENTE_NOME = ParagraphStyle(
    "cliente_nome", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, leading=16
)
_ESTILO_CLIENTE_INFO = ParagraphStyle(
    "cliente_info", fontName="Helvetica", fontSize=9.5, textColor=TEXTO_SUAVE, leading=13
)
_ESTILO_TOTAL = ParagraphStyle(
    "total", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, alignment=2, leading=17
)
_ESTILO_TOTAL_LINHA = ParagraphStyle(
    "total_linha", fontName="Helvetica", fontSize=10, textColor=TEXTO, alignment=2, leading=14
)
_ESTILO_OBS = ParagraphStyle("obs", fontName="Helvetica", fontSize=9.5, textColor=TEXTO, leading=14)


def slug(texto: str) -> str:
    """Nome seguro para arquivo: tudo que não é letra/número vira hífen."""
    return "".join(c if c.isalnum() else "-" for c in texto)


def _qtd(v: Decimal) -> str:
    return f"{v.normalize():f}".replace(".", ",")


def formatar_documento(v: str) -> str:
    """Formata CNPJ (14 dígitos) ou CPF (11); outro tamanho volta como veio."""
    if len(v) == 14:
        return re.sub(r"(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})", r"\1.\2.\3/\4-\5", v)
    if len(v) == 11:
        return re.sub(r"(\d{3})(\d{3})(\d{3})(\d{2})", r"\1.\2.\3-\4", v)
    return v


def _data_br(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else "—"


@lru_cache
def _ambiente() -> Environment:
    env = Environment(loader=FileSystemLoader(PASTA / "templates"), autoescape=select_autoescape(["html"]))
    env.filters.update(data_br=lambda d: d.strftime("%d/%m/%Y") if d else "—")
    return env


@lru_cache
def _imagem(nome: str) -> str:
    dados = (PASTA / "assets" / nome).read_bytes()
    return "data:image/png;base64," + base64.b64encode(dados).decode()


def _css(nome: str) -> str:
    return (PASTA / "templates" / nome).read_text(encoding="utf-8")


class _CanvasOrcamento(Canvas):
    """Rodapé discreto repetido em cada página, identificando o orçamento (número e cliente)."""

    def __init__(self, *args: object, identificacao: str, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._identificacao = identificacao

    def showPage(self) -> None:
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXTO_SUAVE)
        self.drawString(MARGEM, MARGEM - 8, self._identificacao)
        super().showPage()


def _tabela_itens(orc: Orcamento) -> Table:
    # Células de Table com string pura são desenhadas como texto literal (sem parser de XML
    # do Paragraph), então não precisam (e não devem) passar por `esc()` — ver cabecalho_fiscal
    # e os Paragraph de cliente/observações abaixo, onde o escape é obrigatório.
    linhas = [["Descrição", "Qtd", "Valor unitário", "Total"]]
    for item in orc.itens:
        descricao = f"{item.descricao} (mensal)" if item.mensal else item.descricao
        total = f"{brl(item.subtotal)}/mês" if item.mensal else brl(item.subtotal)
        linhas.append([descricao, _qtd(item.qtd), brl(item.preco_unitario), total])

    tabela = Table(linhas, repeatRows=1, colWidths=None)
    tabela.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("TEXTCOLOR", (0, 0), (-1, 0), TEXTO_SUAVE),
            ("BACKGROUND", (0, 0), (-1, 0), SOFT),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9.5),
            ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, SOFT),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )  # fmt: skip
    return tabela


def orcamento_pdf(orc: Orcamento, cliente: Parceiro, empresa: Identidade = PADRAO) -> bytes:
    """Gera o PDF do orçamento com ReportLab (sem dependência nativa de sistema)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=MARGEM + 4 * mm,
    )  # fmt: skip

    subtitulo = f"{_data_br(orc.data)} · Válido até {_data_br(orc.valido_ate)}"
    story: list = [cabecalho_fiscal(empresa, f"Orçamento Nº {orc.numero}", subtitulo), Spacer(1, 16)]

    story.append(Paragraph(esc(cliente.nome), _ESTILO_CLIENTE_NOME))
    if cliente.contato:
        linha = f"A/C {esc(cliente.contato)}" + (f" · {esc(cliente.cargo)}" if cliente.cargo else "")
        story.append(Paragraph(linha, _ESTILO_CLIENTE_INFO))
    if cliente.cpf_cnpj:
        rotulo = "CPF" if cliente.tipo_pessoa == "PF" else "CNPJ"
        story.append(Paragraph(f"{rotulo} {esc(formatar_documento(cliente.cpf_cnpj))}", _ESTILO_CLIENTE_INFO))
    story.append(Spacer(1, 12))

    story.append(_tabela_itens(orc))
    story.append(Spacer(1, 10))

    if orc.desconto:
        story.append(Paragraph(f"Desconto: −{brl(orc.desconto)}", _ESTILO_TOTAL_LINHA))
    story.append(Paragraph(f"Valor do projeto: {brl(orc.total_projeto)}", _ESTILO_TOTAL))
    if orc.total_mensal:
        story.append(Paragraph(f"Manutenção mensal: {brl(orc.total_mensal)}/mês", _ESTILO_TOTAL_LINHA))

    if orc.obs:
        story.append(Spacer(1, 16))
        tabela_obs = Table([[Paragraph(esc(orc.obs).replace("\n", "<br/>"), _ESTILO_OBS)]], colWidths=[None])
        tabela_obs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SOFT),
            ("LINEBEFORE", (0, 0), (0, 0), 3, NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ]))  # fmt: skip
        story.append(tabela_obs)

    identificacao = f"Orçamento Nº {orc.numero} · {cliente.nome}"
    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: _CanvasOrcamento(*args, identificacao=identificacao, **kwargs),
    )
    return buffer.getvalue()


def _linhas(texto: str | None) -> list[str]:
    """Texto de uma linha por item: remove marcadores (•, -, *) e linhas vazias."""
    return [s for s in (re.sub(r"^[•\-*]\s*", "", ln).strip() for ln in (texto or "").split("\n")) if s]


def _gantt(projeto: Projeto, inicio: date, fim: date) -> dict:
    span = (fim - inicio).days + 1
    marcas, (ano, mes) = [], (inicio.year, inicio.month)
    for k in range(24):
        primeiro = date(ano, mes, 1)
        if primeiro > fim:
            break
        x = max(0.0, (primeiro - inicio).days / span * 100)
        marcas.append({"x": round(x, 2), "rotulo": MES3[mes - 1] + (f" {str(ano)[2:]}" if mes == 1 or k == 0 else "")})
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1
    linhas = []
    for i, e in enumerate(projeto.etapas, start=1):
        barra = None
        if e.inicio and e.fim:
            barra = {
                "esquerda": round((e.inicio - inicio).days / span * 100, 2),
                "largura": round(max(1.5, ((e.fim - e.inicio).days + 1) / span * 100), 2),
            }
        linhas.append({"n": f"{i:02d}", "titulo": e.titulo, "status": e.status, "barra": barra})
    return {"marcas": marcas, "linhas": linhas}


def projeto_html(
    projeto: Projeto, cliente: Parceiro, responsavel: MembroEquipe | None, equipe: dict, empresa: Identidade = PADRAO
) -> str:
    etapas = projeto.etapas
    datas = sorted(
        [d for e in etapas for d in (e.inicio, e.fim) if d] + [d for d in (projeto.inicio, projeto.entrega) if d]
    )
    inicio, fim = (datas[0], datas[-1]) if datas else (None, None)
    span = (fim - inicio).days + 1 if inicio and fim else 0
    gantt = _gantt(projeto, inicio, fim) if span and any(e.inicio and e.fim for e in etapas) else None
    passos = []
    for i, e in enumerate(etapas, start=1):
        if e.inicio or e.fim:
            periodo = (
                f"{e.inicio.strftime('%d/%m/%Y') if e.inicio else '?'} a {e.fim.strftime('%d/%m/%Y') if e.fim else '?'}"
            )
        else:
            periodo = "Datas a definir"
        resp = equipe.get(e.responsavel_id)
        passos.append(
            {
                "n": f"{i:02d}", "titulo": e.titulo or f"Etapa {i}", "status": e.status,
                "status_rotulo": STATUS_ETAPA.get(e.status, "A fazer"), "periodo": periodo,
                "responsavel": resp.nome if resp else None, "descricao": e.descricao,
                "entregaveis": _linhas(e.entregaveis),
            }
        )  # fmt: skip
    return (
        _ambiente()
        .get_template("relatorio_projeto.html")
        .render(
            p=projeto, contato=cliente.contato, css=_css("_relatorio.css"), e=empresa,
            logo=empresa.logo or _imagem("logo-horizontal.png"), logo_propria=bool(empresa.logo),
            semanas=max(1, round(span / 7)) if span else 0, status_rotulo=STATUS_PROJETO.get(projeto.status, ""),
            responsavel=responsavel.nome if responsavel else None, escopo=_linhas(projeto.escopo),
            fora_escopo=_linhas(projeto.fora_escopo), gantt=gantt, passos=passos, emitido_em=hoje(),
        )
    )  # fmt: skip
