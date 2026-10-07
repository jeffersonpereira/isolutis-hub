## ADDED Requirements

### Requirement: Rota por tela
Cada tela da aplicação SHALL ter uma URL própria baseada no seu identificador, e navegar para uma tela SHALL atualizar o endereço do navegador.

#### Scenario: Navegar atualiza a URL
- **WHEN** o usuário escolhe "Clientes" no menu
- **THEN** o endereço do navegador passa a ser `/clientes`
- **AND** a tela de clientes é exibida

#### Scenario: Abrir por link
- **WHEN** o usuário abre diretamente a URL de uma tela que ele pode acessar
- **THEN** essa tela é exibida após o login

#### Scenario: Tela sem permissão
- **WHEN** o usuário abre a URL de uma tela que ele não pode acessar
- **THEN** o painel é exibido no lugar
- **AND** o endereço é corrigido para o do painel

---

### Requirement: Histórico do navegador
A navegação entre telas e registros SHALL funcionar com Voltar e Avançar do navegador.

#### Scenario: Voltar
- **WHEN** o usuário vai de Clientes para Negócios e aciona Voltar
- **THEN** a tela de Clientes é exibida e o endereço volta a ser `/clientes`

#### Scenario: Avançar
- **WHEN** o usuário aciona Voltar e depois Avançar
- **THEN** a tela anterior à ação de Voltar é exibida novamente

---

### Requirement: Recarregar mantém a tela
Recarregar a página SHALL reabrir a mesma tela ou registro indicado pela URL.

#### Scenario: Recarregar uma tela
- **WHEN** o usuário recarrega a página em `/fin-titulos`
- **THEN** a tela de Títulos Financeiros é exibida

#### Scenario: Recarregar um registro
- **WHEN** o usuário recarrega a página na URL de um registro
- **THEN** o registro é exibido novamente em formulário em página

---

### Requirement: Rota de registro
As telas que usam formulário em página SHALL expor a rota de novo registro (`/<tela>/novo`) e a de registro existente (`/<tela>/<id>`).

#### Scenario: Abrir um registro
- **WHEN** o usuário abre um cliente da listagem
- **THEN** o endereço passa a ser `/clientes/<id>`

#### Scenario: Voltar da edição para a listagem
- **WHEN** o usuário aciona Voltar a partir de `/clientes/<id>`
- **THEN** a listagem de clientes é exibida

---

### Requirement: Rotas reservadas preservadas
As rotas `/login`, `/login/2fa` e `/convite/<token>` SHALL continuar funcionando como hoje, fora do roteamento de telas.

#### Scenario: Login e segundo fator
- **WHEN** o usuário faz login com 2FA ativo
- **THEN** o fluxo passa por `/login/2fa` e conclui como antes, terminando na tela inicial

#### Scenario: Convite
- **WHEN** o usuário abre `/convite/<token>`
- **THEN** a tela pública de convite é exibida, sem interferência do roteador de telas

---

### Requirement: Endereço desconhecido
Um endereço que não corresponda a nenhuma rota SHALL levar ao painel, sem tela em branco e sem erro.

#### Scenario: Rota inexistente
- **WHEN** o usuário abre `/rota-que-nao-existe`
- **THEN** o painel é exibido
- **AND** o endereço é corrigido sem criar nova entrada no histórico

---

### Requirement: Aba salva vale somente na raiz
A última tela usada SHALL ser reaberta apenas quando o endereço for a raiz (`/`); um endereço de tela explícito SHALL sempre prevalecer sobre a tela salva.

#### Scenario: Raiz reabre a última tela
- **WHEN** o usuário abre `/` depois de ter usado "Orçamentos"
- **THEN** a tela de Orçamentos é exibida

#### Scenario: Endereço explícito prevalece
- **WHEN** o usuário abre `/clientes` tendo usado "Orçamentos" por último
- **THEN** a tela de Clientes é exibida
