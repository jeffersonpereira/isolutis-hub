## ADDED Requirements

### Requirement: Escala de espaçamento em tokens
O sistema de design SHALL definir uma escala de espaçamento de base 4px como tokens CSS (`--esp-1` a `--esp-8`), e os componentes novos SHALL usar esses tokens em vez de valores numéricos soltos para margens, preenchimentos e intervalos.

#### Scenario: Tokens de espaçamento definidos
- **WHEN** o arquivo `tokens.css` é carregado
- **THEN** os tokens `--esp-1` a `--esp-8` estão definidos em `:root`
- **AND** `--esp-1` vale 4px e cada token seguinte cresce de forma monotônica

#### Scenario: Componentes novos usam os tokens
- **WHEN** os estilos dos componentes introduzidos por esta change são inspecionados
- **THEN** margens, preenchimentos e intervalos referenciam tokens `--esp-*`

---

### Requirement: Raios e camadas em tokens
O sistema de design SHALL definir os raios de borda (`--r-sm`, `--r-md`, `--r-lg`, `--r-full`) e as camadas de empilhamento (`--z-topbar`, `--z-gaveta`, `--z-modal`, `--z-paleta`, `--z-toast`) como tokens, e os estilos SHALL NOT usar valores de `z-index` literais.

#### Scenario: Camadas ordenadas
- **WHEN** os tokens de camada são lidos
- **THEN** `--z-topbar` é menor que `--z-gaveta`, que é menor que `--z-modal`, que é menor que `--z-paleta`, que é menor que `--z-toast`

#### Scenario: Sem z-index literal
- **WHEN** os arquivos `*.css` em `frontend/src/styles/` são inspecionados
- **THEN** nenhum `z-index` com valor numérico literal existe fora de `tokens.css`

---

### Requirement: Fundo da área principal em token
O sistema de design SHALL definir o fundo da área principal como o token `--canvas`, distinto da superfície dos cartões (`--surface`), nos temas claro e escuro.

#### Scenario: Canvas distinto da superfície
- **WHEN** o arquivo `tokens.css` é carregado
- **THEN** `--canvas` está definido para o tema claro e para o tema escuro
- **AND** em cada tema o valor de `--canvas` difere do de `--surface`

---

### Requirement: Alturas de controle e medidas da casca em tokens
O sistema de design SHALL definir as alturas de controles (`--controle-sm`, `--controle-md`, `--controle-lg`) e as medidas da casca (`--topbar-h`, `--sidebar-w`, `--sidebar-w-recolhida`) como tokens.

#### Scenario: Medidas da casca em tokens
- **WHEN** o arquivo `tokens.css` é carregado
- **THEN** `--sidebar-w` vale 272px
- **AND** `--sidebar-w-recolhida` é menor que `--sidebar-w`

#### Scenario: Controles com altura consistente
- **WHEN** botões e campos de formulário de tamanho padrão são exibidos
- **THEN** todos têm a altura de `--controle-md`

---

### Requirement: Cores de texto de status com contraste AA
O sistema de design SHALL definir tokens de cor para texto de status e de destaque (`--ok-texto`, `--warn-texto`, `--bad-texto`, `--info-texto`, `--teal-texto`) com contraste mínimo de 4.5:1 sobre o fundo em que são usados, nos temas claro e escuro, e o texto colorido SHALL usar esses tokens, não as cores de status usadas em bordas, barras e pontos.

#### Scenario: Selos legíveis nos dois temas
- **WHEN** um selo de status (ok, aviso, erro ou info) é exibido nos temas claro e escuro
- **THEN** o texto do selo tem contraste de pelo menos 4.5:1 sobre o fundo do selo

#### Scenario: Texto de destaque legível
- **WHEN** um texto de destaque em teal é exibido sobre o fundo claro do destaque, sobre a superfície ou sobre o fundo da página
- **THEN** o contraste é de pelo menos 4.5:1

#### Scenario: Paleta de status preservada
- **WHEN** uma borda, barra ou ponto usa a cor de status
- **THEN** continua usando as cores originais da paleta (`--ok`, `--warn`, `--bad`, `--info`)
