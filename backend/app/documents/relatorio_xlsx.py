"""Geração de planilha Excel para relatórios financeiros (DRE e Fluxo de Caixa)."""

import io


def relatorio_xlsx(
    dre: list[dict],
    fluxo: list[dict],
    empresa_nome: str,
    ano: int,
) -> bytes:
    """Gera arquivo Excel com duas abas: DRE e Fluxo de Caixa.

    Args:
        dre: Dados do DRE (saída de ``calcular_dre``).
        fluxo: Dados do Fluxo de Caixa (saída de ``calcular_fluxo_caixa``).
        empresa_nome: Nome da empresa para o título.
        ano: Ano de referência.

    Returns:
        Conteúdo do arquivo .xlsx como bytes.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    NAVY = "1B2B4B"
    TEAL = "22C3CE"
    SOFT = "EEF1F6"
    WHITE = "FFFFFF"

    wb = Workbook(write_only=False)

    # --- Aba DRE ---
    ws_dre = wb.active
    ws_dre.title = "DRE"

    _escrever_titulo(ws_dre, f"{empresa_nome} — DRE {ano}", span=4)
    cabecalhos_dre = ["Mês", "Receitas (R$)", "Custos (R$)", "Resultado (R$)"]
    _escrever_cabecalho(ws_dre, cabecalhos_dre, cor_fundo=NAVY, cor_fonte=WHITE)

    for row in dre:
        resultado = row["resultado"]
        ws_dre.append([row["nome_mes"], row["receitas"], row["custos"], resultado])
        ultima = ws_dre.max_row
        for col in range(1, 5):
            cell = ws_dre.cell(row=ultima, column=col)
            cell.alignment = Alignment(horizontal="right" if col > 1 else "left")
            if col > 1:
                cell.number_format = '#,##0.00'
        # Colorir resultado positivo/negativo
        cel_resultado = ws_dre.cell(row=ultima, column=4)
        if isinstance(resultado, (int, float)):
            cel_resultado.font = Font(
                color="4A9D6F" if resultado >= 0 else "A85D52",
                bold=resultado == 0,
            )

    _ajustar_colunas(ws_dre, [20, 18, 18, 18])

    # Linha de totais
    total_receitas = sum(r["receitas"] for r in dre)
    total_custos = sum(r["custos"] for r in dre)
    total_resultado = total_receitas - total_custos
    ws_dre.append(["Total", total_receitas, total_custos, total_resultado])
    ultima = ws_dre.max_row
    for col in range(1, 5):
        cell = ws_dre.cell(row=ultima, column=col)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor=SOFT)
        cell.alignment = Alignment(horizontal="right" if col > 1 else "left")
        if col > 1:
            cell.number_format = '#,##0.00'

    # --- Aba Fluxo de Caixa ---
    ws_fc = wb.create_sheet("Fluxo de Caixa")

    _escrever_titulo(ws_fc, f"{empresa_nome} — Fluxo de Caixa {ano}", span=5)
    cabecalhos_fc = ["Mês", "Entradas (R$)", "Saídas (R$)", "Saldo do Mês (R$)", "Saldo Acumulado (R$)"]
    _escrever_cabecalho(ws_fc, cabecalhos_fc, cor_fundo=NAVY, cor_fonte=WHITE)

    for row in fluxo:
        ws_fc.append([
            row["nome_mes"],
            row["entradas"],
            row["saidas"],
            row["saldo_mes"],
            row["saldo_acumulado"],
        ])
        ultima = ws_fc.max_row
        for col in range(1, 6):
            cell = ws_fc.cell(row=ultima, column=col)
            cell.alignment = Alignment(horizontal="right" if col > 1 else "left")
            if col > 1:
                cell.number_format = '#,##0.00'
        # Colorir saldo do mês e saldo acumulado
        for col_idx, key in ((4, "saldo_mes"), (5, "saldo_acumulado")):
            val = row[key]
            if isinstance(val, (int, float)):
                ws_fc.cell(row=ultima, column=col_idx).font = Font(
                    color="4A9D6F" if val >= 0 else "A85D52"
                )

    _ajustar_colunas(ws_fc, [20, 18, 18, 20, 22])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _escrever_titulo(ws: object, texto: str, span: int) -> None:
    from openpyxl.styles import Alignment, Font

    ws.append([texto])
    cell = ws.cell(row=ws.max_row, column=1)
    cell.font = Font(bold=True, size=13)
    cell.alignment = Alignment(horizontal="left")
    ws.append([])  # linha em branco


def _escrever_cabecalho(ws: object, colunas: list[str], cor_fundo: str, cor_fonte: str) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    ws.append(colunas)
    linha = ws.max_row
    for col in range(1, len(colunas) + 1):
        cell = ws.cell(row=linha, column=col)
        cell.font = Font(bold=True, color=cor_fonte)
        cell.fill = PatternFill("solid", fgColor=cor_fundo)
        cell.alignment = Alignment(horizontal="right" if col > 1 else "left")


def _ajustar_colunas(ws: object, larguras: list[int]) -> None:
    from openpyxl.utils import get_column_letter

    for i, largura in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura
