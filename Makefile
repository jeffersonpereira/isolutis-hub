.PHONY: instalar banco api web testes lint tipos openapi
SHELL := /bin/bash

instalar:            ## dependências do backend e do frontend
	cd backend && pip install -e ".[dev]"
	cd frontend && npm ci

banco:               ## sobe o PostgreSQL local e aplica as migrações
	docker compose up -d db
	cd backend && alembic upgrade head

api:                 ## API em modo desenvolvimento (http://localhost:8000/api/docs)
	cd backend && uvicorn app.main:app --reload

web:                 ## frontend em modo desenvolvimento (http://localhost:5173, com proxy para a API)
	cd frontend && npm run dev

testes:              ## todos os testes (backend, SQL e frontend)
	cd backend && pytest -q
	cd frontend && npm test

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint && npm run typecheck

openapi:             ## regenera o contrato da API e os tipos do frontend
	cd backend && python -m app.scripts.exportar_openapi
	cd frontend && npm run gen:api
