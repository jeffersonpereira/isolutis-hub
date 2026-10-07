## MODIFIED Requirements

### Requirement: Configuração de 2FA pelo usuário
O sistema SHALL permitir que qualquer usuário, independentemente do papel na empresa, ative autenticação de dois fatores via TOTP, compatível com Google Authenticator e Authy. A configuração SHALL ficar na tela "Minha conta".

#### Scenario: Usuário inicia setup de 2FA
- **WHEN** o usuário acessa Minha conta e clica em "Ativar 2FA"
- **THEN** o sistema gera um segredo TOTP e exibe um QR code para escanear com o aplicativo autenticador
- **AND** exibe o código de provisão URI como alternativa ao QR code
- **AND** exibe 8 códigos de backup para uso em caso de perda do dispositivo

#### Scenario: Usuário sem papel de administrador configura o 2FA
- **WHEN** um usuário que não é administrador da empresa ativa acessa Minha conta
- **THEN** a opção de ativar o 2FA está disponível e funcional

#### Scenario: Confirmação valida que o app foi configurado corretamente
- **WHEN** o usuário escaneia o QR code e insere o código de 6 dígitos gerado pelo app
- **THEN** o sistema valida o código e ativa o 2FA para o usuário
- **AND** invalida todas as sessões ativas (forçando novo login com 2FA)
- **AND** exibe confirmação "Autenticação em dois fatores ativada"

#### Scenario: Código inválido no setup
- **WHEN** o usuário insere um código TOTP incorreto durante a confirmação de setup
- **THEN** o sistema exibe erro "Código inválido. Verifique o horário do seu dispositivo."
- **AND** o 2FA não é ativado
