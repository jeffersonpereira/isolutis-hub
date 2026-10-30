# Tasks

## 1. Banco de dados

- [ ] 1.1 Criar `backend/migrations/sql/0012_atividades_proxima_acao.sql` com a tabela `atividades` (auditoria, `empresa_id`, RLS e policies como `tarefas`, CHECK de `tipo`, FKs, índices compostos, trigger `tg_exige_papel_cliente` e trigger de coerência cliente × negócio) e as colunas `proxima_acao`/`proxima_acao_em` + CHECK em `negocios`; verificar com `alembic upgrade head` numa base limpa
- [ ] 1.2 Criar `0012_atividades_proxima_acao_down.sql` e o wrapper `migrations/versions/0012_atividades_proxima_acao.py`; verificar `alembic downgrade -1 && alembic upgrade head` sem erro
- [ ] 1.3 Adicionar casos em `backend/tests_sql/test_schema.sql` para: tipo inválido, negócio de outro cliente, ação parcial (só texto ou só data) e ação em negócio fechado recusados; verificar com `psql -v ON_ERROR_STOP=1 -f backend/tests_sql/test_schema.sql`
- [ ] 1.4 Documentar a tabela e as colunas novas em `docs/banco-de-dados.md` e verificar que o diagrama/lista de tabelas cita `atividades`

## 2. Backend: próxima ação do negócio

- [ ] 2.1 Adicionar `proxima_acao` e `proxima_acao_em` ao model `Negocio` e aos schemas `NegocioEntrada`, `MoverEtapa` (opcionais) e `NegocioLeitura`; verificar `mypy`/`pytest -q` sem regressão
- [ ] 2.2 Estender `definir_etapa` em `services/negocios.py` para exigir a ação em etapa aberta (mantendo a gravada no mover), limpar em ganho/perdido e aceitar negócios antigos na leitura; verificar com testes novos em `tests/test_comercial.py` cobrindo cada cenário da spec `proxima-acao-negocio`
- [ ] 2.3 Ajustar fixtures e testes existentes que criam negócios abertos sem ação (`test_comercial.py`, `test_permissoes*.py`, `test_multi_tenant.py`); verificar `pytest -q` verde

## 3. Backend: atividades

- [ ] 3.1 Criar model `Atividade` em `models/comercial.py` e schemas em `schemas/atividade.py` (entrada, atualizar com `versao`, leitura com `responsavel_nome` e `negocio_titulo`, página com cursor); verificar import e `mypy`
- [ ] 3.2 Criar `services/atividades.py` (listar por cliente ou negócio com cursor `(ocorrida_em, id)`, criar com responsável padrão e cliente inferido do negócio, rejeitar data futura além de 5 min, editar/excluir só autor ou admin); verificar com `tests/test_atividades.py` cobrindo os cenários da spec `atividades-comerciais`
- [ ] 3.3 Criar `routers/atividades.py` e registrar em `main.py` sob `requer_comercial`, publicando o recurso realtime `atividades`; verificar em `tests/test_permissoes_rotas.py` que `membro` e `financeiro` recebem 403 e em `test_multi_tenant.py` que atividade de outra empresa dá 404
- [ ] 3.4 Implementar `POST /negocios/{id}/concluir-acao` (transação única: versão, atividade, nova ação ou fechamento) publicando `negocios` e `atividades`; verificar com testes de sucesso, fechamento como perdido, ação inválida sem gravação parcial e conflito de versão
- [ ] 3.5 Regenerar `backend/openapi.json` com `python -m app.scripts.exportar_openapi` e verificar que as rotas novas e os campos de próxima ação aparecem

## 4. Backend: alertas do painel

- [ ] 4.1 Adicionar `negocios_sem_acao` e `acoes_vencidas` ao bloco `comercial` de `services/painel.py` (uma consulta com `FILTER`) e ao schema `AlertasInfo`; verificar com testes em `test_comercial.py` (contagem, ação de hoje não alerta, ausência para papel sem `comercial`)

## 5. Frontend

- [ ] 5.1 Atualizar tipos/schemas e cliente da API (`src/api`, `src/schemas`) para atividades, próxima ação e `concluir-acao`; verificar `npm run typecheck`
- [ ] 5.2 Criar `src/ui/linha-do-tempo.ts` (lista agrupada por dia, ícone por tipo, estado vazio, "Carregar anteriores", formulário com data/hora padrão "agora", editar/excluir só para autor ou admin) com teste `linha-do-tempo.test.ts`; verificar `npm test`
- [ ] 5.3 Incluir a linha do tempo no cliente (`features/clientes.ts`) e no negócio (`features/negocios.ts`), atualizando ao receber o evento realtime `atividades`; verificar manualmente registrando uma atividade em duas abas
- [ ] 5.4 Adicionar os campos de próxima ação ao formulário do negócio (obrigatórios em etapa aberta, ocultos em fechada, sugestões rápidas e data padrão +2 dias úteis); verificar que salvar sem ação mostra o erro da API no campo
- [ ] 5.5 Mostrar a próxima ação no cartão do funil com data relativa e cores `--bad`/`--warn`, tratar o 422 do arraste abrindo o diálogo de próxima ação e reenviando o movimento; verificar com teste de unidade da data relativa e teste manual de arraste
- [ ] 5.6 Criar o diálogo "Concluir ação" (o que foi feito + nova ação ou fechar como ganho/perdido) usando `concluir-acao` e o tratamento de conflito de `ui/conflito.ts`; verificar manualmente os três caminhos
- [ ] 5.7 Exibir os dois alertas novos em `features/painel.ts` com navegação para o funil; verificar `npm test && npm run lint && npm run build`

## 6. Integração

- [ ] 6.1 Adicionar ao teste de ponta a ponta em `e2e/` o fluxo: criar negócio com próxima ação, concluir com nova ação, ver a atividade no cliente e no negócio, ver o alerta de ação vencida; verificar que a CI passa
- [ ] 6.2 Registrar a mudança incompatível (próxima ação obrigatória) no `README.md` ou changelog do projeto e verificar o texto na revisão do PR

## Workflow follow-up

- Arquivar a mudança com `/opsx:archive` depois do merge.
