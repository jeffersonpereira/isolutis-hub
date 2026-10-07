## ADDED Requirements

### Requirement: Ativação do 2FA conclui e preserva a sessão
O sistema SHALL permitir que o usuário conclua a ativação do 2FA em "Minha conta" (QR code, código de confirmação, códigos de backup) e permaneça autenticado na empresa ativa ao final.

#### Scenario: Ativação bem-sucedida
- **WHEN** o usuário inicia a ativação, escaneia o QR code e informa um código válido
- **THEN** o estado passa a "Ativado" e o usuário continua navegando sem novo login

#### Scenario: Código inválido
- **WHEN** o usuário informa um código incorreto
- **THEN** a tela exibe a mensagem de erro, mantém o QR code e permite nova tentativa

#### Scenario: Clique duplo em Ativar
- **WHEN** o usuário aciona "Ativar 2FA" mais de uma vez
- **THEN** apenas um fluxo de configuração fica aberto e o QR code exibido continua válido

#### Scenario: Falha ao iniciar a configuração
- **WHEN** o servidor recusa o início da configuração
- **THEN** a tela exibe uma mensagem de erro compreensível e o estado permanece "Desativado"
