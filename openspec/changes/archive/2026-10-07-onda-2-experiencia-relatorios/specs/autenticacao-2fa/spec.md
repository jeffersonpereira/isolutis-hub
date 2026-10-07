## ADDED Requirements

### Requirement: Configuração de 2FA pelo usuário
O sistema SHALL permitir que qualquer usuário ative autenticação de dois fatores via TOTP, compatível com Google Authenticator e Authy.

#### Scenario: Usuário inicia setup de 2FA
- **WHEN** o usuário acessa Configurações → Segurança e clica em "Ativar autenticação em dois fatores"
- **THEN** o sistema gera um segredo TOTP e exibe um QR code para escanear com o aplicativo autenticador
- **AND** exibe o código de provisão URI como alternativa ao QR code
- **AND** exibe 8 códigos de backup para uso em caso de perda do dispositivo

#### Scenario: Confirmação valida que o app foi configurado corretamente
- **WHEN** o usuário escaneia o QR code e insere o código de 6 dígitos gerado pelo app
- **THEN** o sistema valida o código e ativa o 2FA para o usuário
- **AND** invalida todas as sessões ativas (forçando novo login com 2FA)
- **AND** exibe confirmação "Autenticação em dois fatores ativada"

#### Scenario: Código inválido no setup
- **WHEN** o usuário insere um código TOTP incorreto durante a confirmação de setup
- **THEN** o sistema exibe erro "Código inválido. Verifique o horário do seu dispositivo."
- **AND** o 2FA não é ativado

---

### Requirement: Login com 2FA ativo
O sistema SHALL exigir o segundo fator no login quando o usuário tem 2FA ativo.

#### Scenario: Login solicita segundo fator
- **WHEN** o usuário entra com e-mail e senha corretos e tem 2FA ativo
- **THEN** o sistema retorna `{ requer_2fa: true }` sem emitir JWT de acesso
- **AND** o frontend exibe campo para inserir o código TOTP

#### Scenario: Código TOTP correto completa o login
- **WHEN** o usuário insere o código TOTP válido na tela de segundo fator
- **THEN** o sistema emite o JWT de acesso normalmente
- **AND** o usuário é redirecionado para o painel

#### Scenario: Código de backup aceito em caso de perda do dispositivo
- **WHEN** o usuário insere um código de backup válido (não usado anteriormente)
- **THEN** o login é completado normalmente
- **AND** o código de backup é marcado como usado e não pode ser reutilizado

---

### Requirement: Desativação e gestão de 2FA
O sistema SHALL permitir que o usuário desative o 2FA após confirmar a identidade.

#### Scenario: Desativar 2FA exige confirmação
- **WHEN** o usuário clica em "Desativar 2FA" nas configurações de segurança
- **THEN** o sistema solicita o código TOTP atual (ou código de backup) para confirmar
- **AND** após validação, o 2FA é desativado e o segredo é removido

#### Scenario: Admin pode ser forçado a ter 2FA em produção
- **WHEN** `AMBIENTE = "producao"` e um administrador sem 2FA ativo faz login
- **THEN** o sistema redireciona obrigatoriamente para o setup de 2FA antes de acessar qualquer tela
- **AND** exibe aviso "Autenticação em dois fatores é obrigatória para administradores"
