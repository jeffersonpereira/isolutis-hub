## MODIFIED Requirements

### Requirement: Admin cria convite por e-mail
O sistema SHALL permitir que administradores convidem novos membros enviando um link por e-mail, em vez de criar o usuário com senha inicial. O convite SHALL carregar um dos papéis `admin`, `financeiro`, `comercial` ou `membro`, e esse papel SHALL ser o aplicado à membership ao aceitar.

#### Scenario: Admin envia convite
- **WHEN** um administrador preenche nome, e-mail e papel do convidado e clica em "Enviar convite"
- **THEN** o sistema cria um registro `convite` com token UUID único, o papel escolhido e expiração de 72 horas
- **AND** envia um e-mail para o endereço informado contendo o link de aceite
- **AND** exibe confirmação "Convite enviado para [email]"

#### Scenario: Papel do convite oferece os quatro papéis
- **WHEN** o administrador abre o formulário de convite
- **THEN** o campo de papel oferece Administrador, Financeiro, Comercial e Membro

#### Scenario: Papel inválido no convite
- **WHEN** é enviado um convite com papel diferente dos quatro permitidos
- **THEN** o sistema recusa com erro de validação
- **AND** nenhum convite é criado

#### Scenario: Aceite aplica o papel do convite
- **WHEN** o convidado aceita um convite com papel `financeiro`
- **THEN** a membership na empresa é criada com o papel `financeiro`

#### Scenario: E-mail já pertence a membro ativo
- **WHEN** o admin tenta convidar um e-mail que já é membro ativo da empresa
- **THEN** o sistema exibe erro "Este e-mail já é membro da equipe"
- **AND** nenhum convite é criado

#### Scenario: Convite duplicado para mesmo e-mail
- **WHEN** já existe um convite pendente (não expirado, não usado) para o mesmo e-mail na mesma empresa
- **THEN** o sistema invalida o convite anterior e cria um novo
- **AND** apenas o link mais recente é válido
