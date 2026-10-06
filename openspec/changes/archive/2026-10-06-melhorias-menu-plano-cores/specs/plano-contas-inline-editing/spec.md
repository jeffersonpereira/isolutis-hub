## ADDED Requirements

### Requirement: Inline action buttons on tree nodes
The Plano de Contas tree SHALL display edit, delete, and add-child action buttons directly on each tree node, revealed on mouse hover or keyboard focus.

#### Scenario: Hover reveals actions
- **WHEN** user hovers mouse over a tree node (account)
- **THEN** buttons for edit (✏️), delete (🗑️), and add child (+) appear to the right of the account name
- **AND** buttons remain visible while mouse is over the node

#### Scenario: Focus reveals actions
- **WHEN** user focuses on a tree node using keyboard navigation
- **THEN** action buttons are visible
- **AND** buttons remain visible until focus moves away

#### Scenario: Add child button only for synthetic accounts
- **WHEN** viewing an analytic account (type "A")
- **THEN** the add-child button (+) is disabled or hidden
- **AND** only synthetic accounts (type "S") show an enabled add-child button

#### Scenario: Edit action opens form
- **WHEN** user clicks the edit (✏️) button on a tree node
- **THEN** the account form drawer opens with the account's current data pre-filled
- **AND** the account remains selected in the tree while form is open

#### Scenario: Delete action prompts for confirmation
- **WHEN** user clicks the delete (🗑️) button on a tree node
- **THEN** a confirmation dialog appears asking to confirm deletion
- **AND** if user confirms, the account is deleted and tree refreshes
- **AND** if user cancels, no action occurs

#### Scenario: Add child button creates new account
- **WHEN** user clicks the add-child (+) button on a synthetic account
- **THEN** the account form opens in "new" mode with the parent account pre-selected
- **AND** user can enter details for the new child account

### Requirement: No required node selection
The Plano de Contas tree SHALL NOT require selecting a node before taking action. Actions SHALL be accessible directly from any node.

#### Scenario: Actions available without selection
- **WHEN** page loads with no node selected
- **THEN** action buttons appear on hover for any node
- **AND** user can edit, delete, or add without first clicking to select

#### Scenario: Remove selection-dependent UI
- **WHEN** no node is selected
- **THEN** "Edit" and "Delete" buttons in top toolbar are not shown or are hidden
- **AND** "+ Nova Conta Raiz" button is shown (for creating root-level accounts)
