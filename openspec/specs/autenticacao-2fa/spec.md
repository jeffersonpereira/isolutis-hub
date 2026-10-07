# autenticacao-2fa Specification

## Purpose
Autenticação em dois fatores (TOTP) opcional para todos os usuários, com etapa de código em rota própria (`/login/2fa`) e proteção contra tentativas.
## Requirements
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

### Requirement: Login com 2FA ativo
O sistema SHALL exigir o segundo fator no login quando o usuário tem 2FA ativo. O frontend SHALL conduzir essa etapa na rota `/login/2fa`.

#### Scenario: Login solicita segundo fator
- **WHEN** o usuário entra com e-mail e senha corretos e tem 2FA ativo
- **THEN** o sistema retorna `{ requer_2fa: true, token_temporario }` sem emitir JWT de acesso
- **AND** o frontend navega para `/login/2fa` para inserir o código TOTP

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

---

### Requirement: 2FA opcional para todos os usuários
O sistema SHALL tratar a autenticação em dois fatores como opcional para todos os usuários, independentemente de perfil (incluindo administradores) ou ambiente. O sistema MUST NOT forçar a ativação do 2FA como condição de acesso.

#### Scenario: Administrador sem 2FA acessa o sistema
- **WHEN** um administrador sem 2FA ativo faz login com e-mail e senha corretos
- **THEN** o sistema emite o JWT de acesso normalmente
- **AND** nenhuma tela ou aviso bloqueante de configuração de 2FA é exibido

#### Scenario: Ambiente de produção não altera a regra
- **WHEN** `AMBIENTE = "producao"` e qualquer usuário sem 2FA faz login
- **THEN** o login é concluído sem exigir ativação de 2FA

---

### Requirement: Rota dedicada para o segundo fator
O sistema SHALL apresentar a etapa de código do segundo fator em uma rota própria do frontend, `/login/2fa`, acessada após o login com senha de um usuário com 2FA ativo. O token temporário MUST ficar apenas em memória e NEVER ser colocado na URL, em `localStorage` ou em `sessionStorage`.

#### Scenario: Login com 2FA ativo leva à rota do segundo fator
- **WHEN** o usuário entra com e-mail e senha corretos e tem 2FA ativo
- **THEN** o frontend navega para `/login/2fa`
- **AND** exibe o campo para o código TOTP e a opção de usar código de backup
- **AND** a URL não contém o token temporário

#### Scenario: Acesso direto sem token pendente
- **WHEN** o usuário abre `/login/2fa` sem ter feito o login com senha na sessão atual
- **THEN** o frontend redireciona para `/login` e exibe o formulário de login

#### Scenario: Recarregar a página na rota do segundo fator
- **WHEN** o usuário recarrega a página em `/login/2fa`
- **THEN** o token temporário em memória é perdido
- **AND** o frontend redireciona para `/login`, exigindo nova entrada com senha

#### Scenario: Voltar ao login cancela o fluxo
- **WHEN** o usuário aciona "Voltar ao login" (ou o botão voltar do navegador) em `/login/2fa`
- **THEN** o token temporário é descartado da memória
- **AND** o frontend retorna a `/login` com o foco no campo de e-mail

#### Scenario: Código válido conclui o login pela rota
- **WHEN** o usuário informa um código TOTP ou backup válido em `/login/2fa`
- **THEN** o sistema emite o JWT de acesso e o frontend segue para o painel
- **AND** o token temporário é descartado da memória

---

### Requirement: Proteção contra tentativas no segundo fator
O sistema SHALL limitar as tentativas de código em `POST /auth/2fa/verificar` e MUST invalidar o token temporário após 5 códigos incorretos, exigindo novo login com senha. O token temporário MUST NOT ser aceito como token de acesso à API.

#### Scenario: Quinto código incorreto invalida o token temporário
- **WHEN** o usuário informa 5 códigos incorretos com o mesmo token temporário
- **THEN** o sistema rejeita a 5ª tentativa com erro de autenticação indicando que é preciso entrar novamente
- **AND** o token temporário passa a ser rejeitado, mesmo que o código informado depois esteja correto

#### Scenario: Frontend volta ao login após invalidação
- **WHEN** o sistema informa que o token temporário foi invalidado por excesso de erros
- **THEN** o frontend descarta o token e retorna a `/login` com mensagem pedindo para entrar novamente

#### Scenario: Limite de tentativas por usuário
- **WHEN** o número de falhas de segundo fator de um usuário excede o limite da janela de tempo, mesmo com novos logins
- **THEN** o sistema responde `429` em `POST /auth/2fa/verificar` até a janela expirar

#### Scenario: Token temporário não acessa a API
- **WHEN** um cliente envia o token temporário como `Authorization: Bearer` a um endpoint protegido
- **THEN** o sistema responde `401`, independentemente da versão de sessão do usuário

#### Scenario: Token temporário é de uso único
- **WHEN** o usuário conclui o segundo fator com sucesso
- **THEN** o mesmo token temporário não pode ser usado novamente em `/auth/2fa/verificar`
