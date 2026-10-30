# Tasks

> Estado: tudo foi implementado, mas o ambiente da sessão não tinha PostgreSQL nem Python 3.12, então **o backend não
> foi executado** (só compilação de sintaxe; o CSV foi validado por um script à parte). Item `[x]` está feito e
> verificado; item `[ ]` está implementado e **falta a verificação indicada**.

## 1. Backend

- [x] 1.1 `backend/app/financeiro/plano_padrao.py`: lê o CSV (cache), valida ids/códigos repetidos e pais ausentes, ordena por nível e expõe `CODIGO_APORTE_SOCIO`. O CSV real foi conferido: 149 contas (8/34/107 por nível), pais válidos, nível 3 analítico, natureza herdada e uma só conta `7.02.001` (de receita); o teste `test_csv_do_plano_padrao_e_consistente` repete isso no `pytest`
- [ ] 1.2 `servicos.importar_plano_padrao`: `pg_advisory_xact_lock` por empresa, `Conflito` se houver contas, `uuid4` por conta, inserção por nível com mapa de pais, `aporte_socio` em `7.02.001`, violação de unicidade vira `Conflito`. Falta: `pytest` (`tests/test_plano_padrao.py`)
- [ ] 1.3 `POST /financeiro/plano-contas/importar-padrao` (201 + `list[PlanoContaLeitura]`). Falta: `pytest` (201, 409, 403 para `membro`/`comercial`, 401, `financeiro` e `admin` aceitos)
- [ ] 1.4 Duas empresas importando (ids sem colisão, cada uma vê só o seu plano) e conta de aporte única, em `tests/test_plano_padrao.py`. Falta: `pytest`. A corrida real entre duas conexões não é coberta (os testes usam uma sessão só); o bloqueio e a unicidade são a garantia
- [ ] 1.5 Regenerar `backend/openapi.json` (`python -m app.scripts.exportar_openapi`). Falta: rodar; o frontend usa `http.post<PlanoConta[]>` à mão, sem depender disso

## 2. Frontend

- [x] 2.1 `apiFinanceiro.plano.importarPadrao()` em `features/financeiro/api.ts`; `npm run typecheck` sem erro
- [ ] 2.2 Botão "Importar plano padrão" no estado vazio de `plano-contas.ts`, com confirmação (`ui/confirmar`), aviso de sucesso e recarga também no erro (409). `typecheck` e `build` passam. Falta: teste manual numa empresa sem plano
- [x] 2.3 A opção só existe no estado vazio (some quando há contas) e `importando` impede clique duplo durante a requisição

## 3. Testes ponta a ponta e documentação

- [ ] 3.1 `e2e/tests/plano-contas-padrao.spec.ts` (API simulada): estado vazio, cancelar não grava, confirmar chama a rota e a árvore aparece; empresa com plano não vê a opção. Falta: rodar o Playwright
- [x] 3.2 `docs/modulo-financeiro.md` documenta as duas formas (aplicação: empresa sem plano; script do operador: substitui o plano)
- [ ] 3.3 Rodar `pytest -q`, `mypy app`, `ruff check .`, `npm test` e `npm run lint`. Falta: executar. No frontend, `npm run lint` e `validators.test.ts` já falhavam antes desta mudança

## Observação
`_confirmar_plano` em `servicos.py` compara o erro com o nome antigo `uq_plano_contas_company_codigo` (a migração 0005 o renomeou
para `uq_plano_contas_empresa_codigo`), então a mensagem "Já existe uma conta com este código" nunca aparece e cai na mensagem
genérica. Não é desta change e não foi alterado.
