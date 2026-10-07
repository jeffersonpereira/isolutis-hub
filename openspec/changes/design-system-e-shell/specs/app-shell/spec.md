## ADDED Requirements

### Requirement: Estrutura da casca com pontos de referência
A aplicação SHALL ter uma casca com barra superior (`header`), barra lateral de navegação (`nav`) e área principal (`main`), e SHALL oferecer um link "Pular para o conteúdo" como primeiro elemento focável.

#### Scenario: Pontos de referência presentes
- **WHEN** a aplicação é exibida após o login
- **THEN** existem exatamente um `header` com `role="banner"`, uma navegação principal com nome acessível e um `main`

#### Scenario: Pular para o conteúdo
- **WHEN** o usuário pressiona Tab pela primeira vez ao carregar a aplicação
- **THEN** o primeiro foco vai para "Pular para o conteúdo"
- **AND** ao ativá-lo, o foco passa para a área principal

---

### Requirement: Barra superior
A barra superior SHALL exibir o título da tela atual, o botão "+ Novo", o gatilho da paleta de comandos com a dica do atalho, a alternância de tema e o menu do usuário, e SHALL permanecer visível durante a rolagem da página.

#### Scenario: Título acompanha a tela
- **WHEN** o usuário navega para outra tela
- **THEN** o título da barra superior passa a mostrar o nome dessa tela

#### Scenario: Barra visível ao rolar
- **WHEN** o usuário rola uma tela longa
- **THEN** a barra superior continua visível no topo

---

### Requirement: Ação rápida "+ Novo"
A barra superior SHALL oferecer o botão "+ Novo", que abre um menu com as ações rápidas de criação disponíveis ao usuário, e SHALL listar apenas ações das telas que o usuário pode acessar.

#### Scenario: Criar a partir de qualquer tela
- **WHEN** o usuário abre "+ Novo" e escolhe "Novo cliente"
- **THEN** o formulário de novo cliente é aberto, de qualquer tela em que ele esteja

#### Scenario: Ações respeitam o acesso do usuário
- **WHEN** um usuário abre "+ Novo"
- **THEN** o menu não lista ações de telas que ele não pode acessar

#### Scenario: Navegação por teclado no menu
- **WHEN** o menu "+ Novo" está aberto
- **THEN** as setas movem o destaque entre as ações, Enter executa a ação destacada e Esc fecha o menu devolvendo o foco ao botão

---

### Requirement: Menu do usuário
A barra superior SHALL oferecer o menu do usuário com nome e e-mail, acesso a "Minha conta" e "Trocar senha" e a ação "Sair".

#### Scenario: Abrir o menu do usuário
- **WHEN** o usuário aciona o menu do usuário
- **THEN** são exibidos nome, e-mail, "Minha conta", "Trocar senha" e "Sair"

#### Scenario: Sair
- **WHEN** o usuário aciona "Sair"
- **THEN** a sessão é encerrada e a tela de login é exibida

#### Scenario: Fechar o menu
- **WHEN** o menu do usuário está aberto e o usuário pressiona Esc ou clica fora dele
- **THEN** o menu fecha e o foco volta ao botão que o abriu

---

### Requirement: Barra lateral com ícones e recolhimento
A barra lateral SHALL exibir um ícone ao lado do nome de cada item de menu e SHALL poder ser recolhida para mostrar somente os ícones, lembrando a preferência do usuário.

#### Scenario: Itens com ícone
- **WHEN** a barra lateral está expandida
- **THEN** cada item de menu e cada grupo exibem um ícone ao lado do nome

#### Scenario: Recolher a barra lateral
- **WHEN** o usuário aciona o botão de recolher
- **THEN** a barra lateral passa a mostrar somente ícones
- **AND** cada item mantém nome acessível e dica com o nome
- **AND** a área principal ocupa o espaço liberado

#### Scenario: Preferência lembrada
- **WHEN** o usuário recolhe a barra lateral e recarrega a aplicação
- **THEN** a barra lateral continua recolhida

#### Scenario: Blocos fixos na barra recolhida
- **WHEN** a barra lateral está recolhida
- **THEN** a indicação de sincronização e o acesso à conta continuam visíveis

---

### Requirement: Menu em painel no celular
Em telas de até 860px, a barra lateral SHALL ficar oculta e ser aberta como painel sobreposto por um botão da barra superior, substituindo a faixa horizontal de abas.

#### Scenario: Abrir o painel de menu
- **WHEN** o usuário, numa tela de até 860px, aciona o botão de menu
- **THEN** a navegação aparece como painel sobreposto com fundo escurecido
- **AND** o foco fica preso no painel

#### Scenario: Navegar fecha o painel
- **WHEN** o usuário escolhe um item de menu no painel
- **THEN** o painel fecha e a tela escolhida é exibida

#### Scenario: Fechar sem navegar
- **WHEN** o painel está aberto e o usuário pressiona Esc ou toca no fundo escurecido
- **THEN** o painel fecha e o foco volta ao botão de menu

#### Scenario: Faixa de abas removida
- **WHEN** a aplicação é exibida em tela de até 860px
- **THEN** a navegação não aparece como faixa horizontal de abas no topo

---

### Requirement: Paleta de comandos
A aplicação SHALL oferecer uma paleta de comandos, aberta por Ctrl+K ou ⌘+K e pelo gatilho da barra superior, que permita ir a qualquer tela e executar ações rápidas, com busca que ignora acentos e diferença entre maiúsculas e minúsculas. A paleta SHALL listar apenas telas e ações que o usuário pode acessar.

#### Scenario: Abrir pelo atalho
- **WHEN** o usuário pressiona Ctrl+K (ou ⌘+K)
- **THEN** a paleta abre com o campo de busca focado
- **AND** o atalho do navegador não é acionado

#### Scenario: Filtrar sem acento
- **WHEN** o usuário digita "orcamen" na paleta
- **THEN** o item "Orçamentos" aparece nos resultados

#### Scenario: Ir para uma tela
- **WHEN** o usuário escolhe uma tela na paleta e confirma com Enter
- **THEN** a paleta fecha e a tela é exibida

#### Scenario: Executar uma ação rápida
- **WHEN** o usuário escolhe "Novo cliente" na paleta
- **THEN** a paleta fecha e o formulário de novo cliente é aberto

#### Scenario: Sem resultados
- **WHEN** o texto digitado não corresponde a nenhum item
- **THEN** a paleta exibe uma mensagem de que nada foi encontrado

#### Scenario: Navegação por teclado
- **WHEN** a paleta está aberta
- **THEN** as setas movem o destaque entre os resultados, Enter confirma e Esc fecha a paleta devolvendo o foco ao elemento que o tinha antes

#### Scenario: Acessibilidade da paleta
- **WHEN** a paleta está aberta
- **THEN** o campo de busca tem papel de combobox e aponta para o item destacado
- **AND** a lista tem papel de listbox e cada resultado papel de option
- **AND** o foco permanece preso na paleta

#### Scenario: Respeita o acesso do usuário
- **WHEN** um usuário abre a paleta
- **THEN** ela não lista telas nem ações que ele não pode acessar

#### Scenario: Não busca registros
- **WHEN** o usuário digita o nome de um cliente na paleta
- **THEN** a paleta não lista registros, apenas telas e ações
