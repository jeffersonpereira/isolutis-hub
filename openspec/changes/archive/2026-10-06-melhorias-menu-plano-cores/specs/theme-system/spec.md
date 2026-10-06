## MODIFIED Requirements

### Requirement: Color token definitions
The CSS token system SHALL define a complete palette for light and dark themes with consistent values.

#### Scenario: Light theme colors defined
- **WHEN** page loads in light mode
- **THEN** tokens include:
  - Backgrounds: `--bg` (#ffffff), `--surface` (#ffffff), `--sunk` (#f5f7fb)
  - Text: `--ink` (#16223b), `--muted` (#56647a)
  - Accents: `--navy` (#1a2d47), `--teal` (#3b9ca8)
  - Status colors: `--ok`, `--warn`, `--bad`, `--info`

#### Scenario: Dark theme colors defined
- **WHEN** page loads in dark mode
- **THEN** tokens include inverted palette:
  - Backgrounds: `--bg` (#0d1520), `--surface` (#151e2f), `--sunk` (#0f1829)
  - Text: `--ink` (#e8edf4), `--muted` (#a0afc4)
  - Accents: `--navy` (mapped to teal), `--teal` (#3b9ca8)

#### Scenario: Explicit color space
- **WHEN** page loads
- **THEN** root CSS element declares `color-space: srgb`
- **AND** this ensures colors render consistently across browsers

### Requirement: Color scheme detection and override
The theme system SHALL respect OS-level dark mode preference while allowing explicit theme override.

#### Scenario: Responds to prefers-color-scheme
- **WHEN** browser `prefers-color-scheme` is light
- **THEN** light theme tokens apply
- **AND** when `prefers-color-scheme` is dark, dark theme tokens apply

#### Scenario: Explicit data-theme overrides preference
- **WHEN** root element has `data-theme="dark"` attribute
- **THEN** dark theme tokens apply regardless of `prefers-color-scheme`
- **AND** when `data-theme="light"`, light theme tokens apply

#### Scenario: No browser-specific rendering differences
- **WHEN** opening page in Chrome, Firefox, Brave, Safari, Edge
- **THEN** colors render identically in all browsers
- **AND** no excessive darkening or lightening occurs in any single browser

### Requirement: Status and semantic colors
The theme system SHALL include semantic colors for different message types.

#### Scenario: Success/OK color
- **WHEN** displaying success messages or indicators
- **THEN** `--ok` color is used (#4a9d6f in light, #6fd19f in dark)
- **AND** `--ok-bg` provides the background color for success UI elements

#### Scenario: Warning color
- **WHEN** displaying warning messages or indicators
- **THEN** `--warn` color is used (#b89a3d in light, #d9b860 in dark)

#### Scenario: Error/Bad color
- **WHEN** displaying error messages or indicators
- **THEN** `--bad` color is used (#a85d52 in light, #d98a7f in dark)

#### Scenario: Info color
- **WHEN** displaying informational messages
- **THEN** `--info` color is used (#5b8dd9 in light, #9cc2f0 in dark)
