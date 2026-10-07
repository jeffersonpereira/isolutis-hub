## ADDED Requirements

### Requirement: Formulário em página com seções
O sistema SHALL oferecer o formulário em página, que ocupa a área principal com cabeçalho (trilha, título e estado do registro) e campos organizados em seções nomeadas, com navegação entre as seções.

#### Scenario: Abrir o formulário em página
- **WHEN** o usuário abre um registro que usa formulário em página
- **THEN** a área principal exibe a trilha, o título do registro e as seções do formulário
- **AND** a barra lateral e a barra superior continuam visíveis

#### Scenario: Navegar entre seções
- **WHEN** o usuário escolhe uma seção na navegação do formulário
- **THEN** a página rola até essa seção e o foco vai para ela

#### Scenario: Seções em tela estreita
- **WHEN** o formulário é exibido em largura de celular
- **THEN** as seções ficam empilhadas em coluna única, sem rolagem horizontal da página

---

### Requirement: Barra de ações fixa
O formulário em página SHALL manter visíveis, durante a rolagem, as ações principais (Salvar e Cancelar) e as ações do registro, e SHALL manter a exclusão com confirmação em dois cliques.

#### Scenario: Ações sempre acessíveis
- **WHEN** o usuário rola um formulário longo
- **THEN** a barra de ações com Salvar e Cancelar permanece visível

#### Scenario: Salvar com sucesso
- **WHEN** o usuário salva um formulário válido
- **THEN** o registro é gravado e o usuário recebe confirmação
- **AND** o aviso de alterações não salvas deixa de valer

#### Scenario: Dados inválidos
- **WHEN** o usuário tenta salvar com dados inválidos
- **THEN** o formulário permanece aberto e mostra o motivo, sem perder o que foi digitado

#### Scenario: Exclusão em dois cliques
- **WHEN** o usuário aciona "Excluir" pela primeira vez
- **THEN** o botão passa a pedir "Confirmar exclusão" e nada é excluído
- **AND** somente o segundo clique exclui o registro

---

### Requirement: Proteção contra perda de alterações
O formulário em página SHALL avisar o usuário antes de descartar alterações não salvas, ao navegar dentro da aplicação, ao usar Voltar do navegador e ao recarregar ou fechar a aba.

#### Scenario: Navegar com alterações pendentes
- **WHEN** o usuário alterou um campo e tenta ir a outra tela
- **THEN** a aplicação pede confirmação antes de descartar as alterações
- **AND** se o usuário cancelar, permanece no formulário com os dados intactos

#### Scenario: Sem alterações, sem aviso
- **WHEN** o usuário não alterou nenhum campo e sai do formulário
- **THEN** nenhuma confirmação é pedida

#### Scenario: Voltar do navegador com alterações
- **WHEN** o usuário alterou um campo e aciona Voltar do navegador
- **THEN** a aplicação pede confirmação e, se cancelado, mantém o formulário aberto

#### Scenario: Recarregar com alterações
- **WHEN** o usuário alterou um campo e tenta recarregar ou fechar a aba
- **THEN** o navegador pede confirmação

#### Scenario: Valor alterado e restaurado
- **WHEN** o usuário altera um campo e volta ao valor original
- **THEN** o formulário não é tratado como alterado

---

### Requirement: Endereço próprio do registro
O formulário em página SHALL ter URL própria, de modo que o registro possa ser aberto por link, recarregado e acessado com Voltar e Avançar.

#### Scenario: Abrir por link
- **WHEN** o usuário abre diretamente a URL de um registro existente
- **THEN** o formulário em página desse registro é exibido

#### Scenario: Registro inexistente
- **WHEN** o usuário abre a URL de um registro que não existe ou que ele não pode ver
- **THEN** é exibido o estado "Registro não encontrado" com um link para voltar à listagem

#### Scenario: Novo registro
- **WHEN** o usuário aciona "Novo" numa listagem que usa formulário em página
- **THEN** a URL passa a ser a de novo registro e o formulário vazio é exibido

---

### Requirement: Conflito de edição e presença preservados
O formulário em página SHALL preservar o aviso de edição concorrente, o registro da versão gravada pela própria sessão e a indicação de presença "editando…", com o mesmo comportamento da gaveta.

#### Scenario: Outro usuário altera o registro aberto
- **WHEN** outro usuário grava o registro que está aberto em formulário em página
- **THEN** o aviso de conflito de edição é exibido

#### Scenario: A própria gravação não gera conflito
- **WHEN** o usuário grava o registro que ele mesmo mantém aberto
- **THEN** nenhum aviso de conflito é exibido

#### Scenario: Presença
- **WHEN** o usuário abre um registro em formulário em página
- **THEN** os demais usuários veem que ele está editando esse registro
- **AND** a indicação some quando ele sai do formulário

---

### Requirement: Critério de uso entre gaveta e página
O sistema SHALL manter a gaveta para edições curtas, de até cerca de oito campos e sem listas relacionadas, e SHALL usar o formulário em página para formulários longos, com seções ou listas relacionadas.

#### Scenario: Edição curta continua na gaveta
- **WHEN** o usuário edita um registro de formulário curto, como uma tarefa
- **THEN** o formulário abre na gaveta lateral

#### Scenario: Formulário longo abre em página
- **WHEN** o usuário abre um registro de formulário longo
- **THEN** o formulário abre em página

---

### Requirement: Formulário de cliente em página
O formulário de cliente SHALL abrir em página, com as seções Dados gerais, Contato, Endereço, Observações e Relacionados, mantendo as ações atuais (salvar, conversar no WhatsApp, novo negócio e excluir).

#### Scenario: Seções do cliente
- **WHEN** o usuário abre um cliente
- **THEN** o formulário mostra as seções Dados gerais, Contato, Endereço, Observações e Relacionados

#### Scenario: Ações do cliente preservadas
- **WHEN** o usuário abre um cliente existente
- **THEN** estão disponíveis salvar, conversar no WhatsApp, criar novo negócio e excluir, com o comportamento anterior

#### Scenario: Fornecedores continuam como antes
- **WHEN** o usuário abre um fornecedor na tela de Fornecedores
- **THEN** o formulário continua abrindo na gaveta com os mesmos campos
