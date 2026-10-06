## ADDED Requirements

### Requirement: Comercial menu group
The navigation menu SHALL include a new collapsible group named "Comercial" that contains sales-related modules.

#### Scenario: Group appears in menu
- **WHEN** user views the left sidebar navigation
- **THEN** a "Comercial" group appears in the menu
- **AND** it contains two menu items: "Negócios e Funil" and "Orçamentos"

#### Scenario: Group is collapsible
- **WHEN** user clicks on the "Comercial" group name
- **THEN** the group expands or collapses (toggling the state)
- **AND** a caret icon (›) rotates to indicate expand/collapse state

#### Scenario: Group expands when child is active
- **WHEN** user navigates to a screen within the "Comercial" group (e.g., Orçamentos)
- **THEN** the "Comercial" group automatically expands
- **AND** the active child item is highlighted

#### Scenario: Group state persists
- **WHEN** user expands the "Comercial" group and navigates away
- **THEN** the group collapse state persists during the session
- **AND** when returning, the group is in the same state (expanded or collapsed)

### Requirement: Comercial group order
The "Comercial" group SHALL appear in the correct position in the menu hierarchy.

#### Scenario: Menu order
- **WHEN** user views the navigation menu
- **THEN** menu items appear in order: Painel → Parceiro de Negócios → Comercial (with children) → Produtos → Tarefas → Projetos → Financeiro → Equipe
