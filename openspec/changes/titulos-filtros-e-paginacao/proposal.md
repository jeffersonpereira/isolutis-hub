# Proposal

## Why

A tela de Títulos financeiros baixa todos os títulos da empresa e filtra só por tipo e situação, no navegador. Para a
triagem semanal ("o que está atrasado?", "o que vence nos próximos dias?") faltam atalhos e filtros por período,
parceiro, conta e valor. Sem paginação, a lista e o resumo do topo ficam cada vez mais pesados à medida que os títulos
recorrentes se acumulam. Também não há como levar o resultado para uma planilha.

## What Changes

- `GET /financeiro/titulos` passa a **filtrar, ordenar e paginar no servidor**. **BREAKING**: a resposta deixa de ser uma
  lista e vira `{itens, total, totais}`. Os totais "a receber" e "a pagar" em aberto são calculados sobre o filtro
  completo, não sobre a página.
- Novos filtros no servidor: vencimento (de/até), pagamento (de/até), parceiro, conta do plano, conta bancária, faixa de
  valor devido, recorrente ou avulso e "atrasados" (aberto e vencido). Os já existentes (`tipo`, `status`, `busca`)
  continuam.
- Ordenação por vencimento, valor devido ou parceiro, nos dois sentidos, escolhida no cabeçalho da tabela.
- Nova rota `GET /financeiro/titulos/exportar` devolve o resultado do filtro completo, sem paginação, em CSV.
- Na tela: atalhos "Atrasados" e "Vence nos próximos 7 dias" ao lado dos botões de tipo e situação; botão **Filtros (n)**
  que abre uma gaveta com os filtros avançados; chips removíveis dos filtros ativos; paginação (25, 50 ou 100 por
  página, padrão 25) e botão **Exportar CSV**.
- Filtros, ordenação e página ficam na **query string** da URL (`/fin-titulos?status=A&pag=2`), para recarregar, voltar
  e salvar nos favoritos.

## Capabilities

### New Capabilities
- `listagem-titulos-financeiros`: filtros, ordenação, paginação, totais e exportação CSV da lista de títulos.

### Modified Capabilities
- `navegacao-por-url`: telas passam a poder guardar seu estado de listagem na query string.

## Impact

- **API**: `GET /financeiro/titulos` muda de contrato (envelope); nova rota `/financeiro/titulos/exportar`. Os dois
  seguem sob a permissão `financeiro`. `backend/openapi.json` é regenerado.
- **Backend**: `financeiro/rotas.py`, `schemas.py` e `servicos.py` (`listar_titulos`); testes em `test_financeiro.py`.
- **Frontend**: `features/financeiro/titulos.ts`, `api.ts`, `state/estado.ts`; novos componentes de paginação e de chips
  de filtro; ajuste do roteamento para ler e gravar a query string; `styles/financeiro.css`.
- **E2E**: `e2e/financeiro.mjs` (abre a lista de títulos) precisa do novo formato.
- **Sem migração**: não há mudança de tabela. Índice em `titulo_financeiro (empresa_id, data_vencimento)` fica avaliado
  no design.
