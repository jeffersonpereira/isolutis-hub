"""Rotas legadas de despesas e investimentos desativadas.

Esses movimentos são registrados em `titulo_financeiro`, classificados pela natureza
da conta do plano. O módulo permanece com um roteador vazio para manter a composição
da aplicação enquanto clientes antigos deixam de usar os endpoints legados.
"""

from fastapi import APIRouter

router = APIRouter()
