## ADDED Requirements

### Requirement: Cabeçalho de página padronizado
Toda tela SHALL abrir com um cabeçalho de página que mostre o título, uma descrição curta opcional e as ações principais da tela, com a mesma hierarquia visual em todas as telas.

#### Scenario: Título, descrição e ações
- **WHEN** uma tela de listagem é exibida
- **THEN** o cabeçalho mostra o título, a descrição e as ações principais à direita

#### Scenario: Cabeçalho em tela estreita
- **WHEN** a tela é exibida em largura de celular
- **THEN** as ações passam para baixo do título sem sobrepor o texto nem gerar rolagem horizontal da página

---

### Requirement: Tabela de dados
As listagens SHALL usar tabela com cabeçalho fixo durante a rolagem vertical, destaque da linha sob o cursor, rolagem horizontal contida na própria tabela e linhas clicáveis acessíveis por teclado.

#### Scenario: Cabeçalho fixo
- **WHEN** o usuário rola uma tabela longa
- **THEN** o cabeçalho de colunas permanece visível

#### Scenario: Linha clicável por teclado
- **WHEN** o usuário navega com Tab até uma linha clicável e pressiona Enter
- **THEN** o registro da linha é aberto

#### Scenario: Tabela larga em tela estreita
- **WHEN** a tabela é mais larga que a tela
- **THEN** somente a tabela rola na horizontal
- **AND** o restante da página não rola na horizontal

---

### Requirement: Barra de ferramentas de listagem
Listagens com busca ou filtros SHALL agrupá-los numa barra de ferramentas acima da tabela, com campo de busca e a contagem de resultados.

#### Scenario: Busca e contagem
- **WHEN** o usuário digita no campo de busca de uma listagem
- **THEN** a tabela mostra apenas os resultados correspondentes
- **AND** a barra informa a quantidade de resultados exibidos

---

### Requirement: Selos de status
Estados de registros (por exemplo ativo, pendente, atrasado, concluído) SHALL ser exibidos como selos com cor semântica e texto, e SHALL NOT depender apenas da cor para transmitir o significado.

#### Scenario: Selo com texto
- **WHEN** um registro tem um status
- **THEN** o selo exibe o texto do status além da cor

#### Scenario: Cores nos dois temas
- **WHEN** o tema muda de claro para escuro
- **THEN** os selos mantêm contraste legível nos dois temas

---

### Requirement: Estados de vazio, erro e carregamento
Toda listagem e todo painel SHALL tratar três estados: vazio, com mensagem e ação sugerida; erro, com mensagem e ação de tentar de novo; e carregando, com indicador de esqueleto.

#### Scenario: Lista vazia
- **WHEN** uma listagem não tem registros
- **THEN** é exibida uma mensagem explicativa com a ação de criar o primeiro registro, quando o usuário puder criá-lo

#### Scenario: Falha ao carregar
- **WHEN** o carregamento de uma tela falha
- **THEN** é exibida uma mensagem de erro com a ação "Tentar de novo"
- **AND** a falha não deixa a tela em branco

#### Scenario: Carregando
- **WHEN** os dados de uma tela ainda estão sendo carregados
- **THEN** é exibido um indicador de carregamento no lugar do conteúdo

---

### Requirement: Cartões e indicadores
Agrupamentos de conteúdo SHALL usar cartões com a mesma superfície, borda, raio e espaçamento, e indicadores numéricos SHALL usar o mesmo formato de rótulo, valor e apoio.

#### Scenario: Cartões consistentes
- **WHEN** duas telas diferentes exibem cartões
- **THEN** ambos usam a mesma superfície, borda, raio e espaçamento definidos nos tokens

---

### Requirement: Melhoria das telas existentes sem perda de funcionalidade
A reestilização dos componentes SHALL ser aplicada às telas existentes sem remover funcionalidades nem alterar o comportamento de negócio.

#### Scenario: Todas as telas continuam operáveis
- **WHEN** cada tela da aplicação é aberta após a reestilização
- **THEN** suas listagens, buscas, ações e formulários continuam funcionando como antes

#### Scenario: Telas nos dois temas e no celular
- **WHEN** cada tela é exibida em tema claro, tema escuro e largura de celular
- **THEN** não há texto ilegível, sobreposição de elementos nem rolagem horizontal da página
