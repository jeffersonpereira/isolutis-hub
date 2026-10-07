"""Papéis por empresa e a matriz papel → permissões. Único ponto de verdade; o front consome a lista de permissões."""

from typing import Final, Literal, get_args

Papel = Literal["admin", "financeiro", "comercial", "membro"]
Permissao = Literal["base", "comercial", "financeiro", "administracao"]

PAPEIS: Final[tuple[str, ...]] = get_args(Papel)
PERMISSOES: Final[tuple[str, ...]] = get_args(Permissao)

PERMISSOES_POR_PAPEL: Final[dict[str, frozenset[str]]] = {
    "admin": frozenset({"base", "comercial", "financeiro", "administracao"}),
    "financeiro": frozenset({"base", "financeiro"}),
    "comercial": frozenset({"base", "comercial"}),
    "membro": frozenset({"base"}),
}

PADRAO_PAPEL: Final[str] = "^(" + "|".join(PAPEIS) + ")$"


def permissoes_do_papel(papel: str | None) -> frozenset[str]:
    """Permissões de um papel; papel desconhecido ou ausente não concede nada."""
    return PERMISSOES_POR_PAPEL.get(papel or "", frozenset())


def ordenadas(permissoes: frozenset[str]) -> list[str]:
    """Lista estável (ordem da matriz) para devolver à API."""
    return [p for p in PERMISSOES if p in permissoes]
