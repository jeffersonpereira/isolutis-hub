## ADDED Requirements

### Requirement: Consistent color rendering across browsers
The iSolutis Hub color palette SHALL render consistently across Chrome, Firefox, Brave, Safari, and Edge without appearing excessively dark in any browser.

#### Scenario: Light mode colors consistent
- **WHEN** user has OS in light mode and no theme override is set
- **THEN** background is white (#ffffff) and text is dark (#16223b) in all browsers
- **AND** sidebar is navy (#1a2d47) in all browsers
- **AND** accent color is turquesa (#3b9ca8) in all browsers
- **AND** colors appear identical in Chrome, Firefox, Brave, Safari, and Edge

#### Scenario: Dark mode colors consistent
- **WHEN** user has OS in dark mode (or sets theme to dark)
- **THEN** background is dark (#0d1520) and text is light (#e8edf4) in all browsers
- **AND** sidebar is turquesa (#3b9ca8) in all browsers
- **AND** accent is appropriately inverted in all browsers
- **AND** no browser renders colors significantly darker or lighter than others

#### Scenario: Chrome renders same as Brave
- **WHEN** opening same screen in Chrome and Brave with identical settings
- **THEN** colors appear visually identical
- **AND** no browser-specific color adjustments or overrides are visible

### Requirement: sRGB color space enforcement
The system SHALL explicitly specify sRGB color space to prevent browser-specific color gamut issues.

#### Scenario: Color space declared
- **WHEN** page loads
- **THEN** root CSS sets `color-space: srgb`
- **AND** this forces consistent color rendering across browser color-management implementations

### Requirement: Prefers-color-scheme compatibility
The system SHALL correctly respond to OS-level dark mode preferences without Chrome incorrectly forcing dark mode.

#### Scenario: Respects OS preference
- **WHEN** OS is in light mode
- **THEN** `@media (prefers-color-scheme: light)` rules apply correctly
- **AND** page displays light theme regardless of browser

#### Scenario: Overrides OS preference when theme is set
- **WHEN** user has set explicit theme via `[data-theme="dark"]` attribute on root
- **THEN** dark theme applies regardless of OS preference
- **AND** `@media (prefers-color-scheme)` does not override the explicit `[data-theme]`
