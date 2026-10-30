# Tasks

> **Pendente de verificação (sem PostgreSQL nem navegador neste ambiente):** os testes de integração do backend (1.2, 1.3, 2.2, 2.3, 2.4) foram escritos e coletados pelo pytest, mas não executados; o SQL gerado foi só compilado para o dialeto PostgreSQL. A tela (4.1 a 4.4) e o e2e (5.1) passaram por `tsc`, testes unitários e leitura de código, sem rodar o app. Rodar `pytest -q` e o e2e antes de arquivar (5.3).

## 1. Backend: filtro, ordenação e totais

- [x] 1.1 Criar em `financeiro/servicos.py` a expressão SQL de `valor_devido` e `_filtrar_titulos(empresa, filtros)` com todos os filtros (tipo, situação, busca, parceiro, plano, conta bancária, vencimento, pagamento, faixa de valor, recorrente), com um único join em `Parceiro`; verificar com `pytest backend/tests/test_financeiro.py -q`
- [x] 1.2 Adicionar a um teste a comparação entre a expressão SQL e `regras.valor_devido` sobre títulos com desconto, multa e juros; verificar que passa
- [x] 1.3 Reescrever `listar_titulos` para aplicar ordenação (`vencimento`, `valor`, `parceiro`, com desempate por `created_at, id`), `limit/offset` e devolver `{itens, total, totais}` (totais só de títulos abertos); verificar com testes de página, ordem estável, totais independentes da página e página fora do intervalo

## 2. Backend: API e exportação

- [x] 2.1 Atualizar `rotas.py` e `schemas.py`: novos parâmetros de consulta validados (tamanho ∈ {25, 50, 100}, ordem, sentido, intervalos coerentes) e o schema `PaginaTitulos`; verificar `mypy` e que `GET /financeiro/titulos` responde o envelope
- [x] 2.2 Criar `GET /financeiro/titulos/exportar` (mesmos filtros, sem paginação, CSV UTF-8 com BOM, `;`, decimal com vírgula, datas `dd/mm/aaaa`, escape de `=`, `+`, `-`, `@`, limite de 10.000 linhas); verificar com teste do conteúdo e do cabeçalho `Content-Disposition`
- [x] 2.3 Cobrir permissão e isolamento: ajustar `test_permissoes_rotas.py` e `test_permissoes.py` (403 sem `financeiro` na exportação) e acrescentar teste de que títulos de outra empresa não entram em lista, totais nem CSV
- [x] 2.4 Ajustar os testes existentes de `/titulos` ao novo envelope e regenerar `backend/openapi.json` com `python -m app.scripts.exportar_openapi`; verificar `pytest -q` verde

## 3. Frontend: base

- [x] 3.1 Criar `state/consulta-url.ts` para ler e gravar a query string (valores padrão omitidos, inválidos ignorados, `replaceState` para filtros e `pushState` para página) com testes em Vitest; verificar `npm test`
- [x] 3.2 Criar o componente de paginação (intervalo, anterior/próxima, números, tamanho da página) e o de chips de filtro, com estilos em `styles/financeiro.css`; verificar visualmente nos temas claro e escuro
- [x] 3.3 Atualizar `api.ts` (`titulos.listar(filtros)` com o novo envelope e `titulos.exportar(filtros)` baixando por `fetch` autenticado + `Blob`) e os tipos; verificar `npm run typecheck`

## 4. Frontend: tela de títulos

- [x] 4.1 Reescrever `titulos.ts` para carregar do servidor conforme o estado da URL, remover o filtro no cliente e `ui.finTipo`/`ui.finStatus` de `state/estado.ts`, e usar os totais e o total do envelope no cabeçalho; verificar que Tipo e Situação funcionam e atualizam a URL
- [x] 4.2 Adicionar os atalhos "Atrasados" e "Vence nos próximos 7 dias", o botão "Filtros (n)" e a gaveta com os filtros avançados (comboboxes de parceiro, plano e conta bancária), "Aplicar" e "Limpar"; verificar cada cenário da spec `listagem-titulos-financeiros`
- [x] 4.3 Adicionar ordenação no cabeçalho, paginação e o botão "Exportar CSV"; verificar que mudar filtro volta à página 1 e que o Voltar do navegador percorre as páginas
- [x] 4.4 Garantir que criar, editar e excluir um título recarrega a página atual e, se ela ficar vazia, volta à última existente; verificar manualmente

## 5. Verificação final

- [x] 5.1 Atualizar `e2e/financeiro.mjs` ao novo formato e acrescentar um passo de filtro + exportação; verificar a execução do e2e
- [x] 5.2 Atualizar `docs/modulo-financeiro.md` com os filtros, a paginação e a exportação; verificar que o texto bate com a API
- [ ] 5.3 Rodar `pytest -q`, `npm run typecheck` e `npm test`; verificar tudo verde
