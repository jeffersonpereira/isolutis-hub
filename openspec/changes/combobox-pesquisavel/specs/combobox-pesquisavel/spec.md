## ADDED Requirements

### Requirement: Localizar item por digitação
O sistema SHALL permitir que o usuário digite no campo de seleção para filtrar as opções, sem diferenciar maiúsculas/minúsculas nem acentos, por rótulo e por código.

#### Scenario: Filtrar instituição pelo nome
- **WHEN** o usuário digita "ita" no campo "Instituição financeira"
- **THEN** a lista mostra apenas instituições cujo código ou nome contenha "ita"

#### Scenario: Sem resultados
- **WHEN** nenhum item corresponde ao texto digitado
- **THEN** a lista exibe a mensagem "Nenhum resultado"

### Requirement: Valor sempre vem de uma opção
O sistema SHALL gravar apenas o identificador de uma opção existente; texto livre digitado e não escolhido NÃO SHALL ser enviado.

#### Scenario: Escolher opção
- **WHEN** o usuário seleciona uma opção
- **THEN** o campo exibe o rótulo e o formulário passa a carregar o identificador da opção

#### Scenario: Sair do campo sem escolher
- **WHEN** o usuário sai do campo com texto que não foi escolhido
- **THEN** o campo restaura o rótulo da opção selecionada ou fica vazio, e a validação de obrigatório se aplica

### Requirement: Operação por teclado e acessibilidade
O sistema SHALL permitir abrir, navegar (setas), escolher (Enter) e fechar (Esc) a lista pelo teclado e expor papéis ARIA de combobox e listbox.

#### Scenario: Escolher com o teclado
- **WHEN** o usuário digita, usa a seta para baixo e pressiona Enter
- **THEN** a opção destacada é selecionada e a lista fecha

#### Scenario: Esc fecha sem alterar
- **WHEN** a lista está aberta e o usuário pressiona Esc
- **THEN** a lista fecha e o valor anterior é mantido

### Requirement: Estados do campo
O sistema SHALL suportar os estados desabilitado, obrigatório, lista vazia e valor pré-selecionado na edição.

#### Scenario: Edição com valor existente
- **WHEN** a gaveta de edição abre para um registro com instituição já definida
- **THEN** o campo exibe o rótulo da instituição atual
