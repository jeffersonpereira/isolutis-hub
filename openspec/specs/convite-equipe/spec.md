## ADDED Requirements

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
O sistema SHALL oferecer uma tela pública onde o convidado define sua própria senha ao aceitar o convite.

#### Scenario: Token válido exibe tela de aceite
- **WHEN** o convidado acessa `/convite/{token}` com token válido (não expirado, não usado)
- **THEN** a tela exibe "Você foi convidado por [nome do admin] para entrar em [nome da empresa]"
- **AND** exibe formulário com campos de senha e confirmação de senha
- **AND** não exibe campos de e-mail (já está vinculado ao convite)

#### Scenario: Aceite cria usuário e autentica
- **WHEN** o convidado preenche senha válida e confirma
- **THEN** o sistema cria o usuário com a senha definida
- **AND** vincula o usuário à empresa com o papel definido no convite
- **AND** marca o convite como `usado_em = now()`
- **AND** autentica o usuário e redireciona para o painel

#### Scenario: Token expirado exibe mensagem clara
- **WHEN** o convidado acessa `/convite/{token}` com token expirado (mais de 72h)
- **THEN** a tela exibe "Este convite expirou. Peça ao administrador que envie um novo convite."
- **AND** nenhum formulário de senha é exibido

#### Scenario: Token já utilizado é rejeitado
- **WHEN** o convidado tenta acessar `/convite/{token}` com token que já foi aceito
- **THEN** a tela exibe "Este convite já foi utilizado. Faça login normalmente."
- **AND** exibe link para a tela de login

---

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
