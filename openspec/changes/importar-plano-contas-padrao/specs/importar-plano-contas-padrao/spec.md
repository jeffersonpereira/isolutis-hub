# Spec Delta

## ADDED Requirements

### Requirement: Importação do plano padrão para empresa sem plano
O sistema SHALL permitir a usuários com a permissão `financeiro` importar o plano de contas padrão para a empresa ativa
quando ela não tem nenhuma conta. A importação SHALL criar todas as contas do plano padrão, em três níveis, numa única
operação atômica, com identificadores novos a cada importação.

#### Scenario: Empresa sem plano importa o padrão
- **WHEN** um usuário com permissão `financeiro` solicita a importação numa empresa sem contas
- **THEN** todas as contas do plano padrão são criadas na empresa ativa, com a hierarquia de pai e filhas preservada
- **AND** a resposta traz o plano criado, ordenado por código

#### Scenario: Duas empresas importam o mesmo plano
- **WHEN** duas empresas diferentes importam o plano padrão
- **THEN** ambas recebem o plano completo, sem conflito de identificadores
- **AND** cada empresa vê somente as próprias contas

#### Scenario: Falha não deixa plano pela metade
- **WHEN** a importação falha em qualquer ponto
- **THEN** nenhuma conta é criada na empresa

### Requirement: Importação recusada quando já existe plano
O sistema SHALL recusar a importação, sem alterar nada, quando a empresa já tem ao menos uma conta de plano de contas, e
SHALL NOT apagar, sobrescrever nem mesclar contas existentes.

#### Scenario: Empresa com contas
- **WHEN** a importação é solicitada numa empresa que já tem pelo menos uma conta
- **THEN** o sistema recusa com erro de conflito e mensagem explicativa
- **AND** as contas existentes permanecem inalteradas

#### Scenario: Importações simultâneas
- **WHEN** duas pessoas da mesma empresa sem plano solicitam a importação ao mesmo tempo
- **THEN** exatamente uma cria o plano
- **AND** a outra recebe o erro de conflito e nenhuma conta é duplicada

### Requirement: Conta de aporte de sócios marcada na importação
O sistema SHALL marcar como conta de aporte de sócios a conta analítica de receita "Aportes de Capital" (código
`7.02.001`) ao importar o plano padrão.

#### Scenario: Aporte de sócios disponível após a importação
- **WHEN** o plano padrão é importado
- **THEN** a conta `7.02.001` está marcada como aporte de sócio
- **AND** nenhuma outra conta está marcada

### Requirement: Permissão e isolamento da importação
O sistema SHALL exigir a permissão `financeiro` na empresa ativa para importar o plano padrão e SHALL criar as contas
somente na empresa ativa.

#### Scenario: Papel sem permissão financeira
- **WHEN** um usuário com papel `membro` ou `comercial` solicita a importação
- **THEN** o sistema recusa com erro de permissão
- **AND** nenhuma conta é criada

#### Scenario: Administrador importa
- **WHEN** um `admin` da empresa solicita a importação
- **THEN** a importação é aceita nas mesmas condições do papel `financeiro`
