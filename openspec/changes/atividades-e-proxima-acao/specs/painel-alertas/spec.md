# Spec Delta

## ADDED Requirements

### Requirement: Alerta de negócios sem próxima ação
Para usuários com permissão `comercial`, o painel SHALL alertar sobre negócios em etapa aberta sem próxima ação definida.

#### Scenario: Negócios sem próxima ação alertados
- **WHEN** existem negócios em etapa aberta sem próxima ação
- **THEN** o painel exibe "N negócio(s) sem próxima ação" com cor `--bad`
- **AND** clicar navega para o funil de vendas

#### Scenario: Usuário sem permissão comercial
- **WHEN** o usuário não tem permissão `comercial`
- **THEN** o alerta não é calculado nem exibido

### Requirement: Alerta de próximas ações vencidas
Para usuários com permissão `comercial`, o painel SHALL alertar sobre negócios em etapa aberta cuja próxima ação tem data
anterior a hoje.

#### Scenario: Ações vencidas alertadas
- **WHEN** existem negócios abertos com data da próxima ação anterior a hoje
- **THEN** o painel exibe "N próxima(s) ação(ões) vencida(s)" com cor `--warn`
- **AND** clicar navega para o funil de vendas

#### Scenario: Ação para hoje não alerta
- **WHEN** todas as próximas ações têm data igual ou posterior a hoje
- **THEN** nenhum alerta de ação vencida é exibido
