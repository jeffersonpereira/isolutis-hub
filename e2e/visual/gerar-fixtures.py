"""Gera `fixtures.json` (respostas simuladas de todos os GET sem parâmetro de caminho) a partir do contrato OpenAPI do backend.

Uso (na pasta backend): python ../e2e/visual/gerar-fixtures.py
Usado pela varredura de capturas (`varredura.mjs`) para que todas as telas apareçam com dados.
"""

import json
import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault("HUB_DATABASE_URL", "postgresql+psycopg://x:x@localhost:5432/x")
os.environ.setdefault("HUB_SECRET_KEY", "chave-so-para-gerar-fixtures-0123456789")
sys.path.insert(0, str(Path.cwd()))

from app.main import app  # noqa: E402

ESQ = app.openapi()
COMP = ESQ["components"]["schemas"]
NOMES = ["Distribuidora Alfa", "Clínica Horizonte", "Mercado Bela Vista"]
cont = {"n": 0}


def uid() -> str:
    cont["n"] += 1
    return str(uuid.UUID(int=cont["n"]))


def amostra(s: dict, nome: str = "", prof: int = 0):  # noqa: ANN201
    if prof > 5:
        return None
    if "$ref" in s:
        return amostra(COMP[s["$ref"].split("/")[-1]], nome, prof + 1)
    for chave in ("anyOf", "oneOf"):
        if chave in s:
            opcoes = [o for o in s[chave] if o.get("type") != "null"]
            return amostra(opcoes[0], nome, prof + 1) if opcoes else None
    if "allOf" in s:
        return amostra(s["allOf"][0], nome, prof + 1)
    if "enum" in s:
        return s["enum"][0]
    t = s.get("type")
    f = s.get("format")
    if t == "object" or "properties" in s:
        return {k: amostra(v, k, prof + 1) for k, v in s.get("properties", {}).items()}
    if t == "array":
        return [amostra(s.get("items", {}), nome, prof + 1) for _ in range(3)]
    if t == "boolean":
        return True
    if t == "integer":
        return {"ano": 2026, "mes": 10}.get(nome, 3)
    if t == "number":
        return 12500.5
    if f == "uuid":
        return uid()
    if f == "date-time":
        return "2026-10-01T12:00:00"
    if f == "date":
        return "2026-10-15"
    if f == "email":
        return "contato@exemplo.com.br"
    if t == "string":
        if nome in ("nome", "titulo", "razao_social"):
            cont["n"] += 1
            return NOMES[cont["n"] % len(NOMES)]
        if nome == "municipio_nome":
            return "Salvador"
        if nome in ("uf",):
            return "BA"
        if nome in ("telefone",):
            return "(71) 98888-0000"
        return "Exemplo"
    return None


saida = {}
for caminho, ops in ESQ["paths"].items():
    get = ops.get("get")
    if not get or "{" in caminho:
        continue
    resp = get.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema")
    if resp:
        saida[caminho.replace("/api/v1", "")] = amostra(resp)

destino = Path(__file__).parent / "fixtures.json" if "__file__" in globals() else Path("fixtures.json")
destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(saida)} respostas simuladas gravadas em {destino}")
