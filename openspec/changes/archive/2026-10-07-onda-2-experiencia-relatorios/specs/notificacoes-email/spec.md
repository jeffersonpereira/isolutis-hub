## ADDED Requirements

### Requirement: Alertas automáticos por e-mail para lançamentos vencendo
O sistema SHALL enviar e-mails proativos para usuários sobre lançamentos de receita que vencem no dia, evitando que vencimentos passem despercebidos.

#### Scenario: E-mail enviado para lançamentos que vencem hoje
- **WHEN** o job de notificação executa e existem lançamentos com `vencimento = hoje` e `status != 'recebido'` sem notificação prévia
- **THEN** o sistema envia um e-mail consolidado para o administrador da empresa listando todos esses lançamentos
- **AND** marca `notificado_em = now()` em cada lançamento notificado
- **AND** não envia e-mail novamente para o mesmo lançamento

#### Scenario: Sem lançamentos vencendo não envia e-mail
- **WHEN** o job executa e não há lançamentos vencendo hoje sem notificação
- **THEN** nenhum e-mail é enviado

---

### Requirement: Alertas automáticos por e-mail para orçamentos sem resposta
O sistema SHALL notificar quando orçamentos enviados ficam sem resposta por tempo excessivo.

#### Scenario: E-mail enviado para orçamentos parados há 7 dias
- **WHEN** o job de notificação executa e existem orçamentos com `status = 'enviado'` e `data < hoje - 7 dias` sem notificação prévia
- **THEN** o sistema envia e-mail para o administrador listando os orçamentos sem resposta
- **AND** inclui no e-mail: número do orçamento, nome do cliente e dias aguardando
- **AND** marca `notificado_em = now()` no orçamento

---

### Requirement: Controle de frequência de notificações
O sistema SHALL respeitar limites de frequência para evitar excesso de e-mails.

#### Scenario: Lançamento já notificado não recebe novo e-mail antes de 24h
- **WHEN** um lançamento já tem `notificado_em` definido há menos de 24 horas
- **THEN** o job não envia novo e-mail para esse lançamento mesmo se ele ainda não foi recebido

#### Scenario: Job executa periodicamente sem configuração externa
- **WHEN** a aplicação inicia
- **THEN** o job de notificação é agendado para executar a cada hora automaticamente
- **AND** o job respeita SMTP desconfigurado: se `HUB_SMTP_HOST` está vazio, loga aviso e pula silenciosamente

#### Scenario: SMTP inativo não causa falha da aplicação
- **WHEN** o servidor SMTP não está acessível durante execução do job
- **THEN** o job registra o erro em log estruturado
- **AND** a aplicação continua operando normalmente
- **AND** o `notificado_em` NÃO é atualizado (permite reenvio na próxima execução)
