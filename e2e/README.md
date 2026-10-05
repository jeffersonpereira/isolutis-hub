# Teste de ponta a ponta

Percorre no navegador os fluxos principais: login, cliente, busca, arrastar cartões (negócios e tarefas), motivo de perda,
aprovação de orçamento com faturamento em lote, download de orçamento e relatório de projeto, equipe e tempo real
entre duas abas. Falha se houver erro de JavaScript no console.

```bash
# 1. banco novo + administrador + servidor (a API serve o build do frontend)
cd backend && alembic upgrade head
python -m app.scripts.criar_admin --email admin@isolutis.com.br --nome "Admin" --senha senha-segura-123
(cd ../frontend && npm run build)
HUB_FRONTEND_DIST=../frontend/dist uvicorn app.main:app --port 8000 &

# 2. dados de demonstração e teste
cd ../e2e && python seed.py && npm install && npx playwright install chromium && npm test
```

Variáveis: `HUB_URL`, `HUB_EMAIL`, `HUB_SENHA`, `CHROMIUM_PATH` (para usar um Chromium já instalado).
O teste cria registros; use uma base descartável.

## Módulo financeiro

`node financeiro.mjs` (mesmos pré-requisitos; exige o administrador e a carga de referências: `python -m app.financeiro.popular --fonte snapshot`). Gera um sufixo único por execução, então pode rodar várias vezes na mesma base.
