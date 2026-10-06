## ADDED Requirements

### Requirement: Wizard de primeiro acesso para novas empresas
O sistema SHALL exibir um fluxo guiado de configuração inicial quando uma empresa não completou o onboarding, conduzindo o administrador pelos primeiros passos antes de acessar o painel.

#### Scenario: Wizard exibido no primeiro login do admin
- **WHEN** um administrador faz login e `empresa.onboarding_concluido = false`
- **THEN** o sistema exibe o wizard de onboarding em vez do painel
- **AND** o wizard possui 3 etapas: Perfil da Empresa, Produtos/Serviços, Tour do Painel

#### Scenario: Etapa 1 — Perfil da empresa
- **WHEN** o admin está na etapa 1 do wizard
- **THEN** o sistema exibe campos para nome comercial, segmento e logotipo (opcional)
- **AND** o botão "Próximo" só é habilitado quando o nome comercial está preenchido

#### Scenario: Etapa 2 — Cadastro inicial de produtos ou serviços
- **WHEN** o admin está na etapa 2 do wizard
- **THEN** o sistema exibe um formulário simplificado para cadastrar até 5 produtos/serviços com nome e preço
- **AND** o admin pode pular esta etapa sem cadastrar nenhum item

#### Scenario: Etapa 3 — Tour do painel
- **WHEN** o admin está na etapa 3 do wizard
- **THEN** o sistema exibe uma prévia do painel com tooltips destacando as principais seções (Clientes, Funil, Faturamento, Projetos)
- **AND** um botão "Começar a usar" conclui o onboarding

#### Scenario: Conclusão marca empresa como configurada
- **WHEN** o admin clica em "Começar a usar" ou pula o wizard
- **THEN** `empresa.onboarding_concluido` é marcado como `true`
- **AND** o admin é redirecionado para o painel
- **AND** o wizard não é exibido novamente para nenhum usuário dessa empresa

#### Scenario: Outros usuários não veem o wizard
- **WHEN** um usuário com papel "membro" faz login em uma empresa com `onboarding_concluido = false`
- **THEN** o wizard NÃO é exibido — apenas administradores realizam o onboarding
- **AND** o membro é redirecionado normalmente para o painel
