# scrollable-sidebar-menu Specification

## Purpose
Comportamento do menu lateral de navegação: rolagem interna, largura e visibilidade dos blocos de presença e conta.

## Requirements

### Requirement: Menu lateral com scroll quando expande
O menu de navegação (`#nav`) SHALL ocupar o espaço vertical restante da barra lateral, definido por layout flexível e sem altura calculada à mão, e permitir scroll interno quando os itens expandidos excedem esse espaço.

#### Scenario: Menu expande sem ocultar presença
- **WHEN** usuário clica para expandir um grupo de menu (ex: Financeiro)
- **THEN** os itens filhos aparecem visíveis
- **AND** a seção "Usando agora" permanece visível no final da sidebar

#### Scenario: Menu com scroll quando cresce muito
- **WHEN** múltiplos grupos estão expandidos simultaneamente
- **THEN** o menu exibe scroll bar vertical se exceder o espaço disponível
- **AND** a seção "Usando agora" continua acessível sem scroll

#### Scenario: Presença e informações de conta ficam fixas
- **WHEN** usuário faz scroll no menu lateral
- **THEN** o `.online` (Usando agora) permanece visível no final
- **AND** o `.conta` (informações da conta e botões) permanece visível
- **AND** esses elementos não são ocultados pelo menu

#### Scenario: Bloco de presença cresce
- **WHEN** muitas pessoas estão online e o bloco "Usando agora" ocupa mais altura
- **THEN** o menu reduz a própria altura visível automaticamente
- **AND** nenhum item de menu fica coberto pelos blocos fixos

### Requirement: Layout responsivo mantém presença visível
Em qualquer tamanho de tela ou quantidade de itens de menu, a seção de presença do usuário SHALL permanecer acessível.

#### Scenario: Desktop com menu grande
- **WHEN** na visualização desktop com todos os grupos expandidos
- **THEN** o menu faz scroll interno para caber na altura da viewport
- **AND** "Usando agora" é sempre alcançável sem scroll da página

#### Scenario: Mobile com menu responsivo
- **WHEN** em tela pequena
- **THEN** o layout responsivo continua funcionando sem alterações
- **AND** a presença continua visível na ordem correta

### Requirement: Largura ampliada da barra lateral
A barra lateral de navegação SHALL ter 272px de largura em telas acima do ponto de quebra móvel (860px), de modo que nomes longos de itens de menu não sejam truncados.

#### Scenario: Largura em desktop
- **WHEN** a aplicação é exibida em viewport com mais de 860px de largura
- **THEN** a barra lateral tem 272px de largura
- **AND** a área de conteúdo ocupa o restante da largura

#### Scenario: Layout móvel inalterado
- **WHEN** a aplicação é exibida em viewport com até 860px de largura
- **THEN** a barra lateral continua como faixa horizontal de abas no topo
- **AND** a largura de 272px não é aplicada

### Requirement: Barra de rolagem do menu discreta e no tema
A barra de rolagem do menu lateral SHALL ser fina e usar cores derivadas dos tokens do tema, de forma que acompanhe o tema claro e o escuro.

#### Scenario: Aparência da barra de rolagem
- **WHEN** o menu excede o espaço disponível e exibe rolagem
- **THEN** a barra de rolagem é fina
- **AND** suas cores vêm de variáveis de `tokens.css`, sem valores de cor fixos nos estilos do menu

#### Scenario: Troca de tema
- **WHEN** o usuário alterna entre tema claro e escuro
- **THEN** a barra de rolagem do menu acompanha as cores do tema ativo

#### Scenario: Navegador sem suporte a barra personalizada
- **WHEN** o navegador não suporta a personalização da barra de rolagem
- **THEN** o menu continua rolável com a barra nativa
