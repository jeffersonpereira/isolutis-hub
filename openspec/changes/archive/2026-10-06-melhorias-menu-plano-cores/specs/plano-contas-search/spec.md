## ADDED Requirements

### Requirement: Search input in Plano de Contas header
The Plano de Contas screen SHALL include a search input field that filters the account tree by code or name in real time.

#### Scenario: Search input appears in header
- **WHEN** user navigates to the Plano de Contas screen
- **THEN** a search input field is visible in the page header
- **AND** it has placeholder text "Pesquisar contas..."
- **AND** it has an accessible label for screen readers

#### Scenario: Exact match filtering
- **WHEN** user types a query in the search input
- **THEN** the tree is filtered to show only accounts matching the query (code or name, case-insensitive)
- **AND** filtering is applied in real time as user types
- **AND** tree maintains hierarchy even when filtered

#### Scenario: Substring matching
- **WHEN** user types "rent" in search
- **THEN** accounts with "rent" in code or name appear (e.g., "Aluguel", "1.01.001 Rental")
- **AND** all matching accounts and their ancestors remain visible to maintain tree structure

#### Scenario: Clear search
- **WHEN** user clears the search input (deletes text or clicks clear button)
- **THEN** full tree is restored immediately
- **AND** search input is focused and ready for new input

#### Scenario: Search preserves tree state
- **WHEN** user has expanded/collapsed certain nodes before searching
- **THEN** search results respect the previous expand/collapse state for matching nodes
- **AND** non-matching branches remain collapsed as they were

### Requirement: Search focus management
The search input focus SHALL be preserved and restored correctly when searching and re-rendering.

#### Scenario: Input retains focus during typing
- **WHEN** user types in the search input
- **THEN** the input stays focused (cursor position is maintained)
- **AND** re-rendering of filtered tree does not blur the input
