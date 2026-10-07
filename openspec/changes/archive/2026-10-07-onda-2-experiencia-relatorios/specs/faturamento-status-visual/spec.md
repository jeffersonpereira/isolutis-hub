## MODIFIED Requirements

### Requirement: Hierarquia visual de status de vencimento
A listagem de lançamentos de receita SHALL sinalizar visualmente o estado de cada lançamento em relação à data de vencimento, usando o sistema de cores semânticas existente.

#### Scenario: Lançamento recebido exibe cor positiva
- **WHEN** um lançamento tem `status = 'recebido'`
- **THEN** a pill de status exibe "Recebido" com classe `pill ok`

#### Scenario: Lançamento previsto futuro exibe cor neutra
- **WHEN** um lançamento tem `status != 'recebido'` e `vencimento >= hoje`
- **THEN** a pill de status exibe "Previsto" com classe `pill` (sem modificador de cor)

#### Scenario: Lançamento que vence hoje exibe alerta leve
- **WHEN** um lançamento tem `status != 'recebido'` e `vencimento = hoje`
- **THEN** a pill de status exibe "Vence hoje" com classe `pill warn`

#### Scenario: Lançamento vencido exibe alerta crítico
- **WHEN** um lançamento tem `status != 'recebido'` e `vencimento < hoje`
- **THEN** a pill de status exibe "Vencido" com classe `pill bad`
- **AND** a linha da tabela recebe fundo `var(--bad-bg)` para destaque visual

#### Scenario: Lógica de status calculada no frontend
- **WHEN** a listagem de lançamentos é renderizada
- **THEN** o status visual é calculado comparando `vencimento` com a data atual no cliente
- **AND** nenhuma alteração no backend ou no schema de dados é necessária para o cálculo visual

#### Scenario: Campo notificado_em indica quando alerta por e-mail foi enviado
- **WHEN** o sistema envia um e-mail de alerta para um lançamento
- **THEN** o campo `notificado_em` é atualizado com o timestamp do envio
- **AND** o campo é `null` enquanto nenhuma notificação foi enviada para aquele lançamento
- **AND** o campo não é exposto na interface do usuário (uso interno do sistema de notificações)
