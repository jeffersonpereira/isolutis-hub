## ADDED Requirements

### Requirement: Menu lateral com scroll quando expande
O menu de navegação (`#nav`) DEVE ter altura máxima definida e permitir scroll interno quando os itens expandidos excedem o espaço disponível na sidebar.

#### Scenario: Menu expande sem ocultar presença
- **WHEN** usuário clica para expandir um grupo de menu (ex: Financeiro)
- **THEN** os itens filhos aparecem visíveis
- **AND** a seção "Usando agora" permanece visível no final da sidebar

#### Scenario: Menu com scroll quando cresce muito
- **WHEN** múltiplos grupos estão expandidos simultaneamente
- **THEN** o menu exibe scroll bar vertical se exceder a altura máxima
- **AND** a seção "Usando agora" continua acessível sem scroll

#### Scenario: Presença e informações de conta ficam fixas
- **WHEN** usuário faz scroll no menu lateral
- **THEN** o `.online` (Usando agora) permanece visível no final
- **AND** o `.conta` (informações da conta e botões) permanece visível
- **AND** esses elementos não são ocultados pelo menu

### Requirement: Layout responsivo mantém presença visível
Em qualquer tamanho de tela ou quantidade de itens de menu, a seção de presença do usuário deve permanecer acessível.

#### Scenario: Desktop com menu grande
- **WHEN** na visualização desktop com todos os grupos expandidos
- **THEN** o menu faz scroll interno para caber na altura da viewport
- **AND** "Usando agora" é sempre alcançável sem scroll da página

#### Scenario: Mobile com menu responsivo
- **WHEN** em tela pequena
- **THEN** o layout responsivo continua funcionando sem alterações
- **AND** a presença continua visível na ordem correta
