## ADDED Requirements

### Requirement: Zona de alertas ativos no painel
O painel SHALL exibir uma zona de alertas destacada quando há itens que requerem atenção imediata, posicionada acima dos KPIs.

#### Scenario: Alertas exibidos quando há pendências
- **WHEN** `GET /api/v1/painel` retorna alertas com contagem maior que zero
- **THEN** a zona de alertas é visível acima dos KPIs
- **AND** cada alerta exibe o contador e uma descrição acionável
- **AND** clicar em um alerta navega para o módulo correspondente

#### Scenario: Zona oculta quando não há pendências
- **WHEN** todos os contadores de alerta são zero
- **THEN** a zona de alertas não é renderizada
- **AND** nenhum espaço em branco ou mensagem "tudo certo" é exibido

---

### Requirement: Alerta de lançamentos vencidos
O painel SHALL alertar sobre lançamentos de receita com status diferente de "recebido" e vencimento anterior à data atual.

#### Scenario: Lançamentos vencidos contabilizados
- **WHEN** existem lançamentos com `status != 'recebido'` e `vencimento < hoje`
- **THEN** o painel exibe "N recebimento(s) vencido(s)" com cor `--bad`
- **AND** clicar navega para o módulo Recebimentos

#### Scenario: Threshold de dias configurável internamente
- **WHEN** o alerta é calculado
- **THEN** considera apenas lançamentos vencidos há mais de 3 dias (evitar alertar no mesmo dia do vencimento)

---

### Requirement: Alerta de orçamentos sem resposta
O painel SHALL alertar sobre orçamentos com status "enviado" que não receberam resposta há mais de 15 dias.

#### Scenario: Orçamentos parados alertados
- **WHEN** existem orçamentos com `status = 'enviado'` e `data < hoje - 15 dias`
- **THEN** o painel exibe "N orçamento(s) sem resposta há 15+ dias" com cor `--warn`
- **AND** clicar navega para o módulo Orçamentos com filtro "enviado" aplicado

#### Scenario: Orçamentos recentes não alertam
- **WHEN** todos os orçamentos enviados têm `data >= hoje - 15 dias`
- **THEN** nenhum alerta de orçamento é exibido

---

### Requirement: Alerta de projetos com entrega atrasada
O painel SHALL alertar sobre projetos com data de entrega no passado e progresso inferior a 100%.

#### Scenario: Projetos atrasados alertados
- **WHEN** existem projetos com `entrega < hoje` e pelo menos uma etapa não concluída
- **THEN** o painel exibe "N projeto(s) com entrega atrasada" com cor `--bad`
- **AND** clicar navega para o módulo Projetos

#### Scenario: Projeto concluído não alerta mesmo com data passada
- **WHEN** todas as etapas de um projeto estão com `status = 'concluido'`
- **THEN** esse projeto não é contabilizado no alerta mesmo se `entrega < hoje`
