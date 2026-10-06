"""Geração de PDF para relatórios financeiros (DRE e Fluxo de Caixa)."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

PASTA = Path(__file__).parent


def _ambiente() -> Environment:
    env = Environment(
        loader=FileSystemLoader(PASTA / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["brl"] = _brl
    return env


def _brl(valor: float | None) -> str:
    """Formata número como Real Brasileiro: R$ 1.234,56"""
    from decimal import Decimal

    texto = f"{Decimal(str(valor or 0)):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _css(nome: str) -> str:
    return (PASTA / "templates" / nome).read_text(encoding="utf-8")


def relatorio_pdf(dados: list[dict], tipo: str, empresa_nome: str, ano: int) -> bytes:
    """Gera PDF do relatório financeiro.

    Args:
        dados: Lista de dicionários com os dados mensais.
        tipo: ``'dre'`` ou ``'fluxo_caixa'``.
        empresa_nome: Nome da empresa para o cabeçalho.
        ano: Ano de referência do relatório.

    Returns:
        Conteúdo do PDF como bytes.
    """
    from weasyprint import HTML

    titulo = "Demonstrativo de Resultado" if tipo == "dre" else "Fluxo de Caixa"
    html_content = (
        _ambiente()
        .get_template("_relatorio_financeiro.html")
        .render(
            dados=dados,
            tipo=tipo,
            empresa_nome=empresa_nome,
            titulo=titulo,
            ano=ano,
            css=_css("_relatorio_financeiro.css"),
        )
    )
    return HTML(string=html_content, base_url=str(PASTA / "templates")).write_pdf()  # type: ignore[no-any-return]
