## ADDED Requirements

### Requirement: Financial titles are the source for financial movement classification
The system SHALL use the existing financial control and its operation nature for financial movement classification, without relying on a separate legacy revenue table or expense and investment helper tables.

#### Scenario: Legacy helper tables are removed
- **WHEN** the finance schema cleanup is applied
- **THEN** the approved legacy `lancamento_receita`, `despesas`, `investimentos`, `categorias_despesa`, and `investidores` tables are absent
- **AND** the existing financial control and `plano_contas` remain available

#### Scenario: Existing finance control is not removed as a dependency
- **WHEN** the database dependencies of `lancamento_receita` are inspected
- **THEN** only the legacy relation is targeted for removal
- **AND** the existing financial control's tables, views, and constraints are preserved

#### Scenario: Cleanup can be safely reapplied
- **WHEN** the cleanup migration runs in a database where one or more legacy tables are already absent
- **THEN** the migration completes without failing due only to those missing tables
