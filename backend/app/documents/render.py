"""Geração dos documentos HTML para o cliente (orçamento e plano de entrega do projeto).

São templates Jinja2 com autoescape: nenhum dado do usuário entra no HTML sem escape.
O arquivo baixado é autocontido (logo embutida) e vira PDF pelo "Imprimir → Salvar como PDF" do navegador.
"""

import base64
import re
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

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


def slug(texto: str) -> str:
    """Nome seguro para arquivo: tudo que não é letra/número vira hífen."""
    return "".join(c if c.isalnum() else "-" for c in texto)


def _brl(v: Decimal | float | None) -> str:
    texto = f"{Decimal(v or 0):,.2f}"  # 1,234.50
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _qtd(v: Decimal) -> str:
    return f"{v.normalize():f}".replace(".", ",")


def _cnpj(v: str) -> str:
    """Formata CNPJ (14 dígitos) ou CPF (11); outro tamanho volta como veio."""
    if len(v) == 14:
        return re.sub(r"(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})", r"\1.\2.\3/\4-\5", v)
    if len(v) == 11:
        return re.sub(r"(\d{3})(\d{3})(\d{3})(\d{2})", r"\1.\2.\3-\4", v)
    return v


@lru_cache
def _ambiente() -> Environment:
    env = Environment(loader=FileSystemLoader(PASTA / "templates"), autoescape=select_autoescape(["html"]))
    env.filters.update(brl=_brl, qtd=_qtd, cnpj=_cnpj, data_br=lambda d: d.strftime("%d/%m/%Y") if d else "—")
    return env


@lru_cache
def _imagem(nome: str) -> str:
    dados = (PASTA / "assets" / nome).read_bytes()
    return "data:image/png;base64," + base64.b64encode(dados).decode()


def _css(nome: str) -> str:
    return (PASTA / "templates" / nome).read_text(encoding="utf-8")


def orcamento_html(orc: Orcamento, cliente: Parceiro) -> str:
    return (
        _ambiente()
        .get_template("orcamento.html")
        .render(o=orc, c=cliente, css=_css("_orcamento.css"), logo=_imagem("logo.png"))
    )


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


def projeto_html(projeto: Projeto, cliente: Parceiro, responsavel: MembroEquipe | None, equipe: dict) -> str:
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
            p=projeto, contato=cliente.contato, css=_css("_relatorio.css"), logo=_imagem("logo-horizontal.png"),
            semanas=max(1, round(span / 7)) if span else 0, status_rotulo=STATUS_PROJETO.get(projeto.status, ""),
            responsavel=responsavel.nome if responsavel else None, escopo=_linhas(projeto.escopo),
            fora_escopo=_linhas(projeto.fora_escopo), gantt=gantt, passos=passos, emitido_em=hoje(),
        )
    )  # fmt: skip
