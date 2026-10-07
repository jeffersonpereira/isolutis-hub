# convite-equipe Specification

## Purpose
Convite por e-mail para ingressar na equipe de uma empresa, com tela pública de aceite e acompanhamento dos convites pendentes.
## Requirements
### Requirement: Admin cria convite por e-mail
O sistema SHALL permitir que administradores convidem novos membros enviando um link por e-mail, em vez de criar o usuário com senha inicial.

#### Scenario: Admin envia convite
- **WHEN** um administrador preenche nome, e-mail e papel do convidado e clica em "Enviar convite"
- **THEN** o sistema cria um registro `convite` com token UUID único e expiração de 72 horas
- **AND** envia um e-mail para o endereço informado contendo o link de aceite
- **AND** exibe confirmação "Convite enviado para [email]"

#### Scenario: E-mail já pertence a membro ativo
- **WHEN** o admin tenta convidar um e-mail que já é membro ativo da empresa
- **THEN** o sistema exibe erro "Este e-mail já é membro da equipe"
- **AND** nenhum convite é criado

#### Scenario: Convite duplicado para mesmo e-mail
- **WHEN** já existe um convite pendente (não expirado, não usado) para o mesmo e-mail na mesma empresa
- **THEN** o sistema invalida o convite anterior e cria um novo
- **AND** apenas o link mais recente é válido

---

### Requirement: Novo membro aceita convite e define senha
O sistema SHALL oferecer uma tela pública onde o convidado aceita o convite. Quando o e-mail do convite ainda não tem conta, o convidado define a própria senha. Quando o e-mail já tem conta, o convidado SHALL se autenticar normalmente (incluindo 2FA, se ativo) e o aceite SHALL NOT alterar a senha nem reativar a conta.

#### Scenario: Token válido exibe tela de aceite
- **WHEN** o convidado acessa `/convite/{token}` com token válido (não expirado, não usado) e o e-mail do convite não tem conta
- **THEN** a tela exibe "Você foi convidado por [nome do admin] para entrar em [nome da empresa]"
- **AND** exibe formulário com campos de senha e confirmação de senha
- **AND** não exibe campos de e-mail (já está vinculado ao convite)

#### Scenario: Aceite cria usuário e autentica
- **WHEN** o convidado, sem conta prévia, preenche senha válida e confirma
- **THEN** o sistema cria o usuário com a senha definida
- **AND** vincula o usuário à empresa com o papel definido no convite
- **AND** marca o convite como `usado_em = now()`
- **AND** autentica o usuário e redireciona para o painel

#### Scenario: Token válido para e-mail que já tem conta pede login
- **WHEN** o convidado acessa `/convite/{token}` com token válido e o e-mail do convite já tem conta
- **THEN** a tela exibe o convite e orienta a entrar com a conta existente
- **AND** não exibe campos de definição de senha

#### Scenario: Aceite por conta existente após login
- **WHEN** o convidado entra com o e-mail do convite (informando o código de 2FA, se a conta tiver 2FA ativo) e o convite pendente é concluído
- **THEN** o sistema vincula o usuário à empresa com o papel definido no convite
- **AND** marca o convite como `usado_em = now()`
- **AND** a senha da conta permanece inalterada

#### Scenario: Aceite de conta existente sem autenticação é recusado
- **WHEN** o aceite é solicitado para um e-mail que já tem conta e a requisição não traz autenticação válida
- **THEN** o sistema recusa com erro de autenticação
- **AND** a senha, o estado ativo da conta e as memberships permanecem inalterados
- **AND** o convite continua pendente

#### Scenario: Aceite autenticado como outro usuário é recusado
- **WHEN** um usuário autenticado tenta aceitar um convite cujo e-mail pertence a outra conta
- **THEN** o sistema recusa com erro de permissão
- **AND** nenhuma membership é criada e o convite continua pendente

#### Scenario: Conta desativada não é reativada pelo convite
- **WHEN** o aceite é solicitado para um e-mail cuja conta está desativada
- **THEN** o sistema recusa o aceite
- **AND** a conta permanece desativada

#### Scenario: Convite reativa membership removida
- **WHEN** um usuário que foi removido da equipe da empresa aceita um novo convite para ela
- **THEN** a membership é reativada com o papel definido no convite

#### Scenario: Token expirado exibe mensagem clara
- **WHEN** o convidado acessa `/convite/{token}` com token expirado (mais de 72h)
- **THEN** a tela exibe "Este convite expirou. Peça ao administrador que envie um novo convite."
- **AND** nenhum formulário de senha é exibido

#### Scenario: Token já utilizado é rejeitado
- **WHEN** o convidado tenta acessar `/convite/{token}` com token que já foi aceito
- **THEN** a tela exibe "Este convite já foi utilizado. Faça login normalmente."
- **AND** exibe link para a tela de login

#### Scenario: Aceite funciona com o papel de runtime da API
- **WHEN** o aceite é executado pela conexão da API, que não é proprietária das tabelas nem ignora RLS, sem empresa ativa e por quem ainda não é administrador
- **THEN** a membership é criada ou reativada com o papel do convite
- **AND** a criação só é possível por meio de um convite válido e pendente do próprio usuário

#### Scenario: Inserção direta de membership continua recusada
- **WHEN** a conexão da API tenta inserir diretamente em `usuario_empresa` sem ser administradora da empresa ativa
- **THEN** o banco recusa por política de segurança de linha

#### Scenario: Aceites simultâneos do mesmo convite
- **WHEN** duas requisições de aceite do mesmo token chegam ao mesmo tempo
- **THEN** apenas uma é concluída
- **AND** a outra recebe a resposta de convite já utilizado

### Requirement: Admin visualiza status dos convites pendentes
O sistema SHALL exibir na tela de equipe os convites enviados e ainda não aceitos.

#### Scenario: Convites pendentes listados na tela de equipe
- **WHEN** um administrador acessa a tela de Equipe
- **THEN** convites não aceitos aparecem em seção separada "Convites pendentes"
- **AND** cada convite exibe: e-mail, data de envio e quando expira

#### Scenario: Admin pode cancelar convite pendente
- **WHEN** o admin clica em "Cancelar" em um convite pendente
- **THEN** o convite é invalidado imediatamente
- **AND** o link enviado por e-mail para aquele convite para de funcionar
