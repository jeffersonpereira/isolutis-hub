# Tasks

> Estado: tudo foi implementado, mas o ambiente da sessão não tinha PostgreSQL nem Python 3.12, então **nada do
> backend foi executado** (só compilação de sintaxe). Item marcado `[x]` está feito e verificado; item `[ ]` está
> implementado e **falta a verificação indicada**.

## 1. Banco de dados

- [ ] 1.1 `backend/migrations/sql/0017_area_plataforma.sql`: tabela `operador_plataforma`, `empresa.status` (CHECK `ativa|suspensa`) com gatilho que só deixa as funções do operador mudá-lo, `auditoria_plataforma` somente inserção, papel `hub_plataforma` sem privilégio em tabelas. Falta: `alembic upgrade head` numa base limpa
- [ ] 1.2 Funções `SECURITY DEFINER` `plataforma_*` (listar empresas, criar empresa + convite admin, definir status, listar membros e convites, convidar, cancelar convite, definir membro com regra do último admin), `eh_operador_plataforma()`, e `REVOKE EXECUTE` de `criar_empresa` ao `hub_runtime`. Falta: executar cada função (coberta por `tests/test_plataforma.py`)
- [x] 1.3 Autoria do convite: `convites.criado_por` referencia `usuarios` e o operador é um usuário, então não precisou mudar constraint; `convites` não tem RLS
- [ ] 1.4 `0017_area_plataforma_down.sql` e `migrations/versions/0017_area_plataforma.py`. Falta: `alembic downgrade -1 && alembic upgrade head`
- [ ] 1.5 Testes do banco em `backend/tests/test_plataforma.py` (não em `tests_sql/test_schema.sql`, que só cobre o schema 0001): `hub_plataforma` não lê tabelas de negócio, `hub_runtime` não executa `criar_empresa` nem toca a auditoria, não operador é recusado, último admin protegido, auditoria imutável, admin da empresa não reativa a empresa. Falta: `pytest -q`

## 2. Backend

- [ ] 2.1 `HUB_PLATAFORMA_DATABASE_URL` em `config.py` e `db.get_session_plataforma` (pool próprio; sem a variável devolve `None` e a rota responde 503 `plataforma_indisponivel`; aviso na inicialização em vez de falha, para não quebrar implantações existentes). Falta: `pytest`/`mypy`
- [ ] 2.2 `deps.sessao_operador` (confere `eh_operador_plataforma()` com `hub_runtime`, depois abre a sessão `hub_plataforma`; marcada com `permissao_exigida = "plataforma"` para o teste estrutural de rotas) e `Empresa.status`. Não há model `OperadorPlataforma`: o acesso é só por função. Falta: 403 para não operador, inclusive `admin` de empresa
- [ ] 2.3 `services/plataforma.py` e `routers/plataforma.py` (`GET /plataforma/acesso`, `GET/POST /plataforma/empresas`, `GET /plataforma/empresas/{id}`, `PATCH .../status`, `POST/DELETE .../convites`, `PATCH .../membros/{usuario_id}`), e-mail enviado depois do commit, registrado em `main.py`. Falta: `tests/test_plataforma.py`
- [ ] 2.4 `deps.empresa_atual`, `GET /empresas` e o WebSocket recusam empresa suspensa (`empresa_inacessivel`); a leitura de vínculo e empresa ignora o cache da sessão (`populate_existing`). Falta: testes de suspensão e reativação
- [x] 2.5 O front sabe se o usuário é operador por `GET /plataforma/acesso` (qualquer usuário autenticado), em vez de um campo novo em `/auth/eu`; `/plataforma/acesso` entrou na lista de rotas sem permissão de empresa em `test_permissoes_rotas.py`
- [x] 2.6 O runtime não usa `criar_empresa` em nenhuma rota (confirmado por busca no código); a recusa no banco está em 1.2 e 1.5
- [ ] 2.7 `scripts/criar_admin.py --operador` (empresa opcional quando só operador). Falta: executar contra uma base de teste
- [ ] 2.8 Regenerar `backend/openapi.json` com `python -m app.scripts.exportar_openapi`. Falta: rodar (exige o ambiente Python do projeto); o frontend usa tipos escritos à mão em `api/tipos.ts` para `/plataforma/*`, então não depende disso

## 3. Frontend

- [x] 3.1 Tipos e `api.plataforma.*` em `api/tipos.ts` e `api/endpoints.ts`; `npm run typecheck` sem erro
- [ ] 3.2 `ui/plataforma.ts` + `styles/plataforma.css`: lista com busca, nova empresa, detalhe (suspender/reativar, membros com troca de papel e desativar, convites com reenviar/cancelar, convidar). `typecheck`, `build` e o teste de `formatarCnpj` passam. Falta: teste manual no navegador
- [ ] 3.3 Entrada: `/plataforma` abre a área só para operador (reservada em `state/caminhos.ts`); operador sem empresa vai direto para ela; "Área da plataforma" na escolha de empresa e no menu do usuário. Falta: verificar com usuário comum e com operador
- [ ] 3.4 Suspensão com a aba aberta reabre a escolha de empresa (comportamento já existente para `empresa_inacessivel`). Falta: verificar suspendendo uma empresa com a aba aberta

## 4. Testes ponta a ponta e documentação

- [ ] 4.1 `e2e/tests/plataforma.spec.ts` (API simulada): operador cria empresa e suspende; não operador em `/plataforma` cai no Hub. Falta: rodar o Playwright. O fluxo completo com banco real (administrador aceita o convite e vê o onboarding) está em `tests/test_plataforma.py::test_administrador_aceita_o_convite_e_entra`, sem a parte do onboarding
- [x] 4.2 Documentado em `README.md`, `docs/MULTI_TENANCY.md`, `backend/.env.example`, `docker-compose.yml` e `backend/docker/init-runtime-role.sh` (variável, papel, primeiro operador, política de uso)
- [ ] 4.3 Rodar `pytest -q`, `mypy app`, `ruff check .` e o lint do frontend. Falta: executar. No frontend, `npm run lint` já falha em 6 pontos de `ui/formulario-helper.ts` e `ui/salvar-helper.ts` e `npm test` em `ui/validators.test.ts` (NaN/Infinity), todos anteriores a esta change
