"""Grava o contrato OpenAPI em backend/openapi.json (o frontend gera os tipos TypeScript a partir dele)."""

import json
from pathlib import Path

from app.main import app

DESTINO = Path(__file__).resolve().parents[2] / "openapi.json"

if __name__ == "__main__":
    DESTINO.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Contrato gravado em {DESTINO}")
