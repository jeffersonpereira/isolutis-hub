## ADDED Requirements

### Requirement: Paleta de cores primárias dessaturada
A aplicação SHALL definir cores primárias dessaturadas (Navy e Teal) via CSS custom properties que reduzem fadiga visual mantendo identidade de marca.

Cores específicas:
- `--navy`: #1a2d47 (light mode)
- `--navy-deep`: #0f1b2e (light mode)  
- `--teal`: #3b9ca8 (light mode)
- `--gold`: #0d8792 (light mode)

#### Scenario: Cores primárias aplicadas no header
- **WHEN** usuário visualiza aplicação em light mode
- **THEN** header exibe navy como cor de fundo sem saturação excessiva

#### Scenario: Cores primárias em dark mode
- **WHEN** usuário ativa dark mode (via preferência do sistema ou seletor)
- **THEN** navy e teal ajustam-se para dark mode (#3b9ca8, #0d1520) mantendo harmonia

### Requirement: Paleta de cores neutras harmoniosa
A aplicação SHALL definir cores neutras (backgrounds, surfaces, borders) em progressão harmoniosa que cria hierarquia visual clara.

Cores específicas (light mode):
- `--bg`: #f5f7fb (fundo principal)
- `--surface`: #ffffff (superfícies de conteúdo)
- `--sunk`: #e8ecf2 (superfícies deprimidas)
- `--line`: #dce4f0 (borders e divisores)

#### Scenario: Progressão de profundidade em light mode
- **WHEN** usuário visualiza cards ou containers aninhados
- **THEN** background, surface, sunk formam progressão visual clara do fundo para o conteúdo

#### Scenario: Borders legíveis sem agressividade
- **WHEN** usuário visualiza inputs, dividers, separadores
- **THEN** `--line` fornece contraste suficiente (WCAG AA) sem ser agressivo

### Requirement: Cores de status dessaturadas e consistentes
A aplicação SHALL definir cores de status (OK, Warn, Bad, Info) dessaturadas com backgrounds claros para indicar estados sem fadiga visual.

Cores status (light mode):
- `--ok`: #4a9d6f (OK), `--ok-bg`: #e9f3ee (fundo OK)
- `--warn`: #b89a3d (Warn), `--warn-bg`: #f9f5e5 (fundo Warn)
- `--bad`: #a85d52 (Bad), `--bad-bg`: #f9ede9 (fundo Bad)
- `--info`: #5b8dd9 (Info), `--info-bg`: #e8eef9 (fundo Info)

#### Scenario: Estado OK em lista de itens
- **WHEN** item marcado com status OK
- **THEN** texto exibe cor dessaturada #4a9d6f sobre background #e9f3ee com contraste ≥ 4.5:1 (WCAG AA)

#### Scenario: Alertas legíveis em formulários
- **WHEN** usuário vê validação de erro (Bad)
- **THEN** cor Bad #a85d52 exibe-se claramente em inputs, mensagens com background #f9ede9 sem agressividade

#### Scenario: Status cores em dark mode
- **WHEN** dark mode ativado
- **THEN** cores de status ajustam-se (ex: `--ok`: #6fd19f, `--warn`: #d9b860) mantendo semântica

### Requirement: Aplicação de paleta em todos os componentes
A aplicação SHALL usar CSS custom properties de cores em todos os componentes (buttons, inputs, cards, headers, etc.) sem hard-coded color values.

#### Scenario: Botão primário usa token Navy
- **WHEN** componente Button renderizado com variant="primary"
- **THEN** background-color usa `var(--accent)` (#1a2d47) em light mode

#### Scenario: Inputs com borders usando token Line
- **WHEN** componente Input renderizado
- **THEN** border-color usa `var(--line)` (#dce4f0) sem hard-coded #d3dbe6

#### Scenario: Cards com surface background
- **WHEN** componente Card renderizado
- **THEN** background-color usa `var(--surface)` (#ffffff)

### Requirement: Suporte a light e dark mode com temas consistentes
A aplicação SHALL suportar light mode (padrão) e dark mode com paleta de cores ajustada via `@media (prefers-color-scheme: dark)` e `[data-theme="dark"]`.

#### Scenario: Transição automática para dark mode
- **WHEN** sistema operacional ou navegador está em dark mode
- **THEN** CSS custom properties mudam automaticamente sem JavaScript (via @media query)

#### Scenario: Seletor manual de tema dark
- **WHEN** usuário clica no seletor de tema e escolhe "Dark"
- **THEN** atributo `data-theme="dark"` aplicado ao `<html>` e cores ajustam-se via CSS

#### Scenario: Alternância sem flash de cores
- **WHEN** usuário alterna entre light e dark mode
- **THEN** transição é suave sem flashing de cores antigas

### Requirement: Validação de contraste WCAG AA
A aplicação SHALL garantir que todas as combinações críticas de texto e fundo mantêm contraste mínimo 4.5:1 (WCAG AA) conforme especificação WCAG 2.1.

#### Scenario: Texto em backgrounds neutros
- **WHEN** qualquer texto (#16223b ou #e8edf4) renderizado sobre backgrounds (#f5f7fb, #ffffff, #e8ecf2)
- **THEN** razão de contraste ≥ 4.5:1 medida por ferramentas WCAG

#### Scenario: Cores status em backgrounds status
- **WHEN** texto de status (#4a9d6f) sobre background status (#e9f3ee)
- **THEN** razão de contraste ≥ 4.5:1

#### Scenario: Links e conteúdo destacado
- **WHEN** links ou elementos em accent (#1a2d47) em backgrounds variados
- **THEN** razão de contraste ≥ 4.5:1 em todos os modos de tema

