## MODIFIED Requirements

### Requirement: Plano de Contas screen layout
The Plano de Contas screen SHALL display a hierarchical tree of accounts with integrated search and action buttons.

#### Scenario: Screen header with search and new button
- **WHEN** user navigates to Plano de Contas
- **THEN** the screen header contains:
  - Page title "Plano de Contas"
  - Descriptive subtitle about three hierarchy levels
  - A search input field for filtering accounts
  - A "+ Nova Conta Raiz" button for creating root accounts

#### Scenario: Tree displays accounts in hierarchy
- **WHEN** page loads
- **THEN** accounts are displayed as a tree structure
- **AND** expandable folders (📁) indicate synthetic accounts
- **AND** leaf nodes (📄) indicate analytic accounts
- **AND** hierarchy is preserved: 1 · 1.01 · 1.01.001

#### Scenario: Pills show account type and nature
- **WHEN** viewing an account in the tree
- **THEN** pills/badges display:
  - Account type: "Sintética" or "Analítica"
  - Account nature: "Receita" or "Despesa"

#### Scenario: Expand/collapse functionality
- **WHEN** user clicks the caret (›) on a synthetic account
- **THEN** child accounts expand or collapse
- **AND** state is maintained during the session

#### Scenario: No forced selection
- **WHEN** user views the tree with no account selected
- **THEN** action buttons are still available on hover
- **AND** no special message or disabled state indicates a required selection

#### Scenario: Empty state message
- **WHEN** the plano de contas is empty (no accounts)
- **THEN** an empty state message appears: "Plano de contas vazio"
- **AND** a "+ Criar a primeira conta" button is shown
- **AND** clicking it creates the first root account

#### Scenario: Status message with selected account
- **WHEN** user hovers over or interacts with an account
- **THEN** a status line appears (or disappears when no hover)
- **AND** it shows: "Selecionada: <code> <name>"

### Requirement: Removal of top toolbar buttons for Edit/Delete
The "Editar" and "Excluir" buttons in the top toolbar SHALL be removed.

#### Scenario: Only "Nova Conta Raiz" in top toolbar
- **WHEN** user views the Plano de Contas header
- **THEN** only the "+ Nova Conta Raiz" button appears in the tools section
- **AND** "Editar" and "Excluir" buttons are not shown
- **AND** users edit/delete via inline hover buttons instead

#### Scenario: "Nova Conta Raiz" only for creating roots
- **WHEN** no tree node is selected
- **THEN** "+ Nova Conta Raiz" button is visible and enabled
- **AND** it creates a root-level (first-level) account
