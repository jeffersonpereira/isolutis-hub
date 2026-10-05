# Hub Comercial iSolutis

Sistema comercial interno da iSolutis: clientes, negócios e funil, orçamentos, projetos com plano de entrega,
faturamento, despesas e investimentos, produtos, tarefas da equipe e gestão de usuários.

| Camada | Tecnologia | Pasta |
|---|---|---|
| Frontend | TypeScript + Vite (sem framework; mesmo visual do sistema anterior) | [`frontend/`](frontend) |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2 (async), Alembic | [`backend/`](backend) |
| Banco | PostgreSQL 16+, modelagem relacional ([docs](docs/banco-de-dados.md)) | [`backend/migrations/`](backend/migrations) |

> Módulo financeiro (plano de contas, contas bancárias, parceiros, títulos, fluxo de caixa): [`docs/modulo-financeiro.md`](docs/modulo-financeiro.md)
>
> Arquitetura, decisões e fluxos: [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) · Migração dos dados do sistema anterior:
> [`docs/MIGRACAO.md`](docs/MIGRACAO.md) · Modelo de dados: [`docs/banco-de-dados.md`](docs/banco-de-dados.md)

## Rodar localmente

Requisitos: Python 3.11+, Node 20+, PostgreSQL 16+ (ou Docker).

```bash
make instalar                       # dependências
make banco                          # PostgreSQL (docker compose) + migrações
cp backend/.env.example backend/.env
cd backend && python -m app.scripts.criar_admin --email voce@empresa.com.br --nome "Seu Nome"
make api                            # terminal 1: http://localhost:8000/api/docs
make web                            # terminal 2: http://localhost:5173
```

Sem Docker: crie o banco (`createdb hub_dev`), ajuste `HUB_DATABASE_URL` no `.env` e rode `alembic upgrade head` em `backend/`.

## Testes

```bash
cd backend  && pytest -q                      # API + regras de negócio + importador (PostgreSQL real, schema via Alembic)
psql -d hub_sql -v ON_ERROR_STOP=1 -f backend/tests_sql/test_schema.sql   # constraints e triggers do schema (base vazia)
cd frontend && npm test && npm run lint && npm run typecheck && npm run build
```

O teste de ponta a ponta no navegador está em [`e2e/`](e2e/README.md). A CI (`.github/workflows/ci.yml`) roda tudo isso.

## Produção

Uma imagem única (API + site): `docker compose build` (defina `HUB_SECRET_KEY`), aplique as migrações uma vez com
`docker compose --profile migrate run --rm migrate` e inicie a aplicação com `docker compose up -d app`.
Separar a migração permite executá-la como etapa única do release antes de iniciar ou atualizar as réplicas da API.
Em deploys com banco gerenciado, rode `alembic upgrade head` como job de release usando a mesma imagem e configuração.
Variáveis em
[`backend/.env.example`](backend/.env.example). Coloque atrás de HTTPS (o login usa token no cabeçalho `Authorization`).

## Acesso e equipe

- Cada pessoa entra com e-mail e senha. Quem administra cria usuários, define e troca senhas na aba **Equipe**.
  O primeiro administrador é criado por `python -m app.scripts.criar_admin`.
- "Remover da equipe" desativa a pessoa (o histórico de quem criou/alterou cada registro é preservado).
- Edição concorrente: se duas pessoas editam o mesmo registro, a segunda gravação é recusada com aviso (controle de versão
  no banco), em vez de sobrescrever em silêncio.
