## ADDED Requirements

### Requirement: Escala tipográfica em tokens
O sistema de design SHALL definir todos os tamanhos de fonte como tokens CSS nomeados semanticamente, eliminando valores numéricos soltos nos arquivos de estilo.

#### Scenario: Tokens tipográficos cobrem todos os usos existentes
- **WHEN** o arquivo `tokens.css` é carregado
- **THEN** os seguintes tokens estão definidos em `:root`:
  - `--text-2xs: 9.5px` (tagline da marca)
  - `--text-xs: 11px` (labels, pills, uppercase)
  - `--text-sm: 12px` (sub, legendas)
  - `--text-base: 13px` (corpo)
  - `--text-md: 15px` (h2)
  - `--text-lg: 18px` (drawer h2)
  - `--text-xl: 26px` (h1)

#### Scenario: Nenhum tamanho de fonte hardcoded nos arquivos CSS
- **WHEN** os arquivos `*.css` em `frontend/src/styles/` são inspecionados
- **THEN** nenhum `font-size` com valor numérico literal existe fora de `tokens.css`
- **AND** todos os `font-size` referenciam um dos tokens `--text-*`

---

### Requirement: Tokens de sombra padronizados
O sistema de design SHALL definir tokens de elevação/sombra para uso consistente em toda a aplicação.

#### Scenario: Tokens de sombra disponíveis
- **WHEN** o arquivo `tokens.css` é carregado
- **THEN** os seguintes tokens estão definidos:
  - `--shadow-sm: 0 1px 3px rgba(0,0,0,.08)`
  - `--shadow-md: 0 4px 12px rgba(0,0,0,.12)`
  - `--shadow-lg: -12px 0 40px rgba(0,0,0,.20)`

#### Scenario: Drawer usa token de sombra
- **WHEN** o drawer lateral é exibido
- **THEN** seu `box-shadow` referencia `var(--shadow-lg)` em vez de valor hardcoded

---

### Requirement: Fontes hospedadas localmente
O sistema SHALL servir todas as fontes tipográficas a partir do próprio servidor, sem dependência de serviços externos.

#### Scenario: Nenhuma requisição ao Google Fonts
- **WHEN** a aplicação carrega em um browser sem acesso externo
- **THEN** todas as fontes renderizam corretamente
- **AND** nenhuma requisição de rede é feita para `fonts.googleapis.com` ou `fonts.gstatic.com`

#### Scenario: Fontes carregadas com font-display swap
- **WHEN** a página carrega e as fontes ainda não estão em cache
- **THEN** o texto é exibido imediatamente com fonte de fallback (`system-ui`)
- **AND** substitui para a fonte correta quando o arquivo `.woff2` termina de carregar

#### Scenario: Apenas os pesos utilizados são servidos
- **WHEN** a pasta `frontend/public/fonts/` é inspecionada
- **THEN** contém apenas: Montserrat 600, IBM Plex Sans 400 e 500, IBM Plex Mono 400
- **AND** não inclui pesos não utilizados pela aplicação
