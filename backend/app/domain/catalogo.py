"""Catálogo inicial do site: faixas de sistema sob medida, manutenções mensais e consultoria (preço a definir)."""

_MANUTENCAO = "Operação, correções e ajustes do sistema entregue."


def _item(nome: str, tipo: str, descricao: str) -> dict[str, object]:
    unidade = {"projeto": "projeto", "mensal": "mês", "consultoria": "hora"}[tipo]
    return {"nome": nome, "tipo": tipo, "unidade": unidade, "descricao": descricao, "preco": 0, "ativo": True}


CATALOGO = [
    _item("Sistema sob medida · Simples", "projeto", "Um processo, um tipo de usuário. Construção em 2 a 4 semanas."),
    _item(
        "Sistema sob medida · Média", "projeto", "Vários perfis, integrações e relatórios. Construção em 4 a 8 semanas."
    ),
    _item("Sistema sob medida · Complexa", "projeto", "Multiempresa, integrações críticas e exigência regulatória."),
    _item("Manutenção mensal · Simples", "mensal", _MANUTENCAO),
    _item("Manutenção mensal · Média", "mensal", _MANUTENCAO),
    _item("Manutenção mensal · Complexa", "mensal", _MANUTENCAO),
    _item("Consultoria · Diagnóstico", "consultoria", "Diagnóstico de processos e tecnologia."),
    _item(
        "Consultoria · Mentoria e formação",
        "consultoria",
        "Mentoria e formação para times de tecnologia, operação comercial e produto.",
    ),
]
