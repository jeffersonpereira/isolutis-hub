## MODIFIED Requirements

### Requirement: Menu item names and organization
The navigation menu SHALL display modules with specific names and groupings as defined by the menu structure.

#### Scenario: "Clientes" renamed to "Parceiro de Negócios"
- **WHEN** user views the navigation menu
- **THEN** the module previously labeled "Clientes" is now labeled "Parceiro de Negócios"
- **AND** it appears as a top-level menu item (not in a group)

#### Scenario: "Negócios" renamed to "Negócios e Funil"
- **WHEN** user views the navigation menu
- **THEN** the module labeled "Negócios" is now labeled "Negócios e Funil"
- **AND** it belongs to the "Comercial" group

#### Scenario: "Orçamentos" in Comercial group
- **WHEN** user views the navigation menu
- **THEN** "Orçamentos" appears as a child of the "Comercial" group
- **AND** it is positioned below "Negócios e Funil" within the group

#### Scenario: "Faturamento" in Financeiro group
- **WHEN** user views the navigation menu
- **THEN** "Faturamento" is no longer a top-level item
- **AND** it appears as a child of the "Financeiro" group
- **AND** it is positioned below other financial modules (Plano de Contas, Contas Bancárias, etc.)

#### Scenario: "Despesas" and "Investimentos" removed
- **WHEN** user views the navigation menu
- **THEN** neither "Despesas" nor "Investimentos" appear in the menu
- **AND** these modules are no longer accessible from navigation (no broken links)

#### Scenario: Menu order is correct
- **WHEN** user views the complete navigation menu
- **THEN** items appear in this order:
  - Painel
  - Parceiro de Negócios
  - Comercial (group)
    - Negócios e Funil
    - Orçamentos
  - Projetos
  - Tarefas
  - Produtos
  - Financeiro (group)
    - Plano de Contas
    - Contas Bancárias
    - Parceiros
    - Títulos
    - Fluxo de Caixa
    - Faturamento
  - Equipe
