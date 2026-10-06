## 1. Menu Reorganization

- [x] 1.1 Update `ORDEM_MENU` in `src/state/nucleo.ts` with new order: painel, parceiro-negocio, comercial (negocios, orcamentos), projetos, tarefas, produtos, financeiro (plano, contas, bancarias, parceiros, titulos, fluxo, faturamento), equipe
- [x] 1.2 Rename "Clientes" to "Parceiro de Negócios" in `src/features/clientes.ts` (update `nome` in registrarVista, keep `id: "clientes"` for RLS)
- [x] 1.3 Rename "Negócios" to "Negócios e Funil" in `src/features/negocios.ts` and add `grupo: "Comercial"`
- [x] 1.4 Add `grupo: "Comercial"` to `src/features/orcamentos.ts`
- [x] 1.5 Add `grupo: "Financeiro"` to `src/features/faturamento.ts`
- [x] 1.6 Remove imports for "Despesas" and "Investimentos" from `src/main.ts` (remove `import "@/features/despesas"` and equivalent for investimentos if they exist)
- [ ] 1.7 Test menu renders correctly in browser with new names and groups
- [ ] 1.8 Verify "Comercial" group collapses/expands and Financeiro group contains Faturamento

## 2. Plano de Contas - Search Input

- [x] 2.1 Add search input field to plano-contas header in `src/features/financeiro/plano-contas.ts` (place in `<div class="tools">` area)
- [x] 2.2 Create data key `buscaPlano` in `src/state/estado.ts` (UI state for search input value)
- [x] 2.3 Wire search input to `data-busca="buscaPlano"` and ensure `input` event in `main.ts` updates `ui.buscaPlano` and calls `render()`
- [x] 2.4 Implement filter logic: check if account code or name contains search query (case-insensitive, substring match)
- [x] 2.5 Update `filhasDe()` function to filter by search query while preserving tree hierarchy
- [ ] 2.6 Test search input updates tree in real-time as user types
- [ ] 2.7 Test clearing search restores full tree
- [ ] 2.8 Test focus management: input stays focused during re-renders

## 3. Plano de Contas - Inline Actions (Remove Selection)

- [x] 3.1 Remove "Selecionada" state logic from plano-contas (remove `tela.selecionada` tracking, or keep it internally but remove UI dependence)
- [x] 3.2 Refactor `no()` function: remove `data-act="selecionarConta"` from tree-row div
- [x] 3.3 Update tree-row markup to no longer be clickable for selection; keep only caret, code, nome, pills
- [x] 3.4 Remove "Editar" and "Excluir" buttons from top toolbar (keep only "+ Nova Conta Raiz")
- [x] 3.5 Test that "+ Nova Conta Raiz" button is always visible and enabled (not grayed out)

## 4. Plano de Contas - Inline Action Buttons on Hover

- [x] 4.1 Add `<span class="tree-actions">` container to tree-row markup with three buttons: edit (✏️), delete (🗑️), add-child (+)
- [x] 4.2 Wire edit button to `data-act="editarConta"` with data-id for account
- [x] 4.3 Wire delete button to `data-act="excluirConta"` with data-id for account
- [x] 4.4 Wire add-child button to `data-act="novaContaFilha"` with data-id for parent account
- [x] 4.5 Add CSS to `src/styles/financeiro.css`: `.tree-actions { display: none; }` and `.tree-row:hover .tree-actions { display: flex; }`
- [x] 4.6 Add CSS for `.tree-row:focus .tree-actions { display: flex; }` (keyboard accessibility)
- [x] 4.7 Add CSS for high-contrast mode: `@media (prefers-forced-colors: active) { .tree-actions { display: flex !important; } }`
- [x] 4.8 Ensure add-child (+) button is disabled for analytic accounts (check `c.tipo_conta === "S"`)
- [x] 4.9 Update `formConta()` function to accept mode "nova" and optionally parent account (paiInicial)
- [x] 4.10 Wire form to open in appropriate mode: edit vs. new-child
- [ ] 4.11 Test edit button opens form with data pre-filled
- [ ] 4.12 Test delete button prompts for confirmation and deletes
- [ ] 4.13 Test add-child button opens form with parent pre-selected (disabled parent field for new child)
- [ ] 4.14 Test add-child button is disabled on analytic accounts

## 5. Chrome Color Fix

- [x] 5.1 Add `color-space: srgb;` to root CSS in `src/styles/tokens.css` (at the very top)
- [ ] 5.2 Review `prefers-color-scheme` media query blocks: ensure `:not([data-theme="light"])` is not conflicting in Chrome
- [ ] 5.3 Test colors in Chrome with page in light mode: verify background is white, text is dark, sidebar is navy
- [ ] 5.4 Test colors in Chrome with page in dark mode: verify background is dark, text is light
- [ ] 5.5 Compare colors in Chrome vs. Brave: should be visually identical
- [ ] 5.6 Compare colors in Chrome vs. Firefox: should be visually identical
- [ ] 5.7 If colors still appear too dark in Chrome after step 5.1, investigate browser-specific force-colors or high-contrast setting

## 6. Testing & Validation

- [ ] 6.1 E2E test: Menu reorganization - verify all modules appear in correct order and groups
- [ ] 6.2 E2E test: Menu names - verify "Parceiro de Negócios" is displayed, "Negócios e Funil" is displayed
- [ ] 6.3 E2E test: Comercial group - verify it's collapsible and contains Negócios and Orçamentos
- [ ] 6.4 E2E test: Financeiro group - verify Faturamento appears as a child
- [ ] 6.5 E2E test: Plano de Contas search - type in search, verify tree filters, clear search, verify tree restores
- [ ] 6.6 E2E test: Inline actions - hover over account, verify buttons appear, click edit, verify form opens
- [ ] 6.7 E2E test: Inline delete - click delete, verify confirmation, confirm deletion, verify tree updates
- [ ] 6.8 E2E test: Add child - click + on synthetic account, verify form opens in new mode with parent pre-selected
- [ ] 6.9 E2E test: Add child disabled - hover over analytic account, verify + button is disabled
- [ ] 6.10 Manual test: Colors on Chrome, Firefox, Brave, Safari - take screenshots, compare visually
- [ ] 6.11 Manual test: Plano de Contas on mobile - verify hover buttons don't break touch experience (long-press or tap to reveal)
- [ ] 6.12 Accessibility test: Tab through plano-contas tree, verify actions appear on focus, keyboard navigation works
- [ ] 6.13 Performance test: Large plano-contas (500+ accounts) - search and filter performance acceptable

## 7. Code Review & Cleanup

- [ ] 7.1 Remove unused variables or functions (e.g., `selecionarConta` action if fully replaced)
- [ ] 7.2 Review TypeScript types: ensure no lingering types reference removed "despesas" module
- [ ] 7.3 Check for any broken imports or references to removed modules
- [ ] 7.4 Update docs or comments if necessary (e.g., in nucleo.ts about menu structure)
- [ ] 7.5 Verify all tests pass (unit + E2E)
- [ ] 7.6 Create PR and request review
