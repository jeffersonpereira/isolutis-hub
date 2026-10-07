## ADDED Requirements

### Requirement: Escolha explícita da empresa após o login
O sistema SHALL exibir, após a autenticação, uma tela em que o usuário escolhe a empresa em que vai trabalhar, mostrando para cada empresa o nome e o papel do usuário nela. A tela SHALL ser exibida mesmo quando o usuário tem acesso a uma única empresa.

#### Scenario: Usuário com várias empresas escolhe
- **WHEN** um usuário com acesso ativo a mais de uma empresa conclui o login
- **THEN** o sistema exibe a tela "Em qual empresa quer trabalhar?" com um cartão por empresa
- **AND** cada cartão mostra o nome da empresa e o papel do usuário nela
- **AND** a aplicação só é carregada depois que o usuário escolhe uma empresa

#### Scenario: Usuário com uma única empresa
- **WHEN** um usuário com acesso ativo a uma única empresa conclui o login
- **THEN** o sistema exibe a tela de escolha com essa empresa
- **AND** a aplicação só é carregada depois que o usuário a escolhe

#### Scenario: Última empresa usada vem pré-selecionada
- **WHEN** a tela de escolha é exibida e o navegador guarda a última empresa usada pelo usuário e ela ainda consta na lista
- **THEN** essa empresa aparece pré-selecionada e em destaque
- **AND** o usuário pode confirmá-la com um clique ou escolher outra

#### Scenario: Usuário sem acesso a nenhuma empresa
- **WHEN** um usuário autenticado não tem nenhuma membership ativa
- **THEN** o sistema informa que a conta não tem acesso a nenhuma empresa
- **AND** oferece a ação de sair
- **AND** nenhum dado de empresa é carregado

---

### Requirement: Empresa ativa vale por aba
O sistema SHALL manter a empresa ativa de forma independente em cada aba do navegador. Um recarregamento da página na mesma aba SHALL manter a empresa ativa, desde que o usuário ainda tenha acesso ativo a ela.

#### Scenario: Recarregar a página mantém a empresa
- **WHEN** o usuário recarrega a página numa aba em que já escolheu uma empresa e ainda tem acesso a ela
- **THEN** a aplicação abre diretamente na mesma empresa
- **AND** a tela de escolha não é exibida de novo

#### Scenario: Nova aba pede a escolha
- **WHEN** o usuário, já autenticado, abre a aplicação numa nova aba
- **THEN** a tela de escolha de empresa é exibida nessa aba

#### Scenario: Abas com empresas diferentes
- **WHEN** o usuário escolhe a empresa A numa aba e a empresa B em outra
- **THEN** cada aba envia e exibe somente os dados da sua própria empresa
- **AND** trocar a empresa numa aba não altera a outra

#### Scenario: Empresa guardada deixou de ser acessível
- **WHEN** a empresa guardada na aba não consta mais na lista de empresas do usuário
- **THEN** a tela de escolha é exibida
- **AND** a empresa antiga não é usada nas requisições

---

### Requirement: Troca de empresa durante o uso
O sistema SHALL mostrar a empresa ativa e o papel do usuário nela no bloco de conta da barra lateral, e SHALL permitir trocar de empresa a qualquer momento sem novo login.

#### Scenario: Empresa ativa visível
- **WHEN** o usuário está usando a aplicação
- **THEN** o bloco de conta da barra lateral exibe o nome da empresa ativa e o papel do usuário nela

#### Scenario: Trocar de empresa
- **WHEN** o usuário aciona "Trocar de empresa"
- **THEN** a empresa ativa da aba é descartada e a aplicação é recarregada
- **AND** a tela de escolha de empresa é exibida

#### Scenario: Nenhum dado de outra empresa permanece em memória
- **WHEN** o usuário troca da empresa A para a empresa B
- **THEN** nenhum registro carregado da empresa A é exibido na empresa B

#### Scenario: Acesso removido durante a sessão
- **WHEN** o usuário perde o acesso à empresa ativa enquanto usa a aplicação e uma requisição é recusada por falta de acesso a essa empresa
- **THEN** a empresa ativa da aba é descartada
- **AND** a tela de escolha de empresa é exibida

---

### Requirement: Sair limpa a empresa lembrada
O sistema SHALL descartar, ao sair, a empresa ativa da aba e a última empresa lembrada, para que a escolha de um usuário não persista para outro usuário no mesmo navegador.

#### Scenario: Logout limpa o armazenamento da empresa
- **WHEN** o usuário aciona "Sair"
- **THEN** a empresa ativa da aba e a última empresa usada são removidas do armazenamento do navegador

#### Scenario: Outro usuário entra no mesmo navegador
- **WHEN** outro usuário faz login no mesmo navegador após o logout
- **THEN** a tela de escolha não traz nenhuma empresa pré-selecionada

---

### Requirement: Isolamento de dados pela empresa ativa
O sistema SHALL responder a cada requisição apenas com dados da empresa ativa enviada na requisição, recusando empresas em que o usuário não tem membership ativa.

#### Scenario: Requisição com empresa sem acesso
- **WHEN** uma requisição autenticada informa uma empresa em que o usuário não tem membership ativa
- **THEN** o sistema recusa com erro de permissão
- **AND** nenhum dado dessa empresa é devolvido

#### Scenario: Requisição sem empresa
- **WHEN** uma requisição a um recurso de empresa não informa a empresa ativa
- **THEN** o sistema recusa com erro de permissão

#### Scenario: Mesmo usuário em duas empresas
- **WHEN** o mesmo usuário consulta a mesma listagem informando a empresa A e depois a empresa B
- **THEN** cada resposta contém somente registros da respectiva empresa
