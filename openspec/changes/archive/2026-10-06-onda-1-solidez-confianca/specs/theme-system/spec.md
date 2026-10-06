## MODIFIED Requirements

### Requirement: Color token definitions
The CSS token system SHALL define a complete palette for light and dark themes with consistent values, using semantically accurate names that reflect the actual color they represent.

#### Scenario: Light theme colors defined
- **WHEN** page loads in light mode
- **THEN** tokens include:
  - Backgrounds: `--bg` (#ffffff), `--surface` (#ffffff), `--sunk` (#f5f7fb)
  - Text: `--ink` (#16223b), `--muted` (#56647a)
  - Accents: `--navy` (#1a2d47), `--teal` (#3b9ca8)
  - Teal scale: `--teal-mid` (#0d8792), `--teal-pale` (#dbf3f5)
  - Status colors: `--ok`, `--warn`, `--bad`, `--info`

#### Scenario: Dark theme colors defined
- **WHEN** page loads in dark mode
- **THEN** tokens include inverted palette:
  - Backgrounds: `--bg` (#0d1520), `--surface` (#151e2f), `--sunk` (#0f1829)
  - Text: `--ink` (#e8edf4), `--muted` (#a0afc4)
  - Teal scale: `--teal-mid` and `--teal-pale` com valores adaptados para dark mode

#### Scenario: Tokens --gold e --gold-soft não existem mais
- **WHEN** os arquivos CSS são inspecionados após a migração
- **THEN** nenhuma ocorrência de `--gold` ou `--gold-soft` existe em qualquer arquivo
- **AND** todos os usos anteriores foram substituídos por `--teal-mid` e `--teal-pale` respectivamente

#### Scenario: Explicit color space
- **WHEN** page loads
- **THEN** root CSS element declares `color-space: srgb`
- **AND** this ensures colors render consistently across browsers
