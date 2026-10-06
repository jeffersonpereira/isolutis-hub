## ADDED Requirements

### Requirement: Pipeline de CI automatizado
O sistema SHALL executar verificações automáticas de qualidade em todo push para qualquer branch, garantindo que código com erros não chegue à branch principal.

#### Scenario: Push em branch de feature dispara CI
- **WHEN** um desenvolvedor faz push para qualquer branch
- **THEN** o pipeline executa na ordem: lint e type-check do backend (ruff + mypy), lint e type-check do frontend (eslint + tsc), testes do backend (pytest), testes do frontend (vitest)
- **AND** falha em qualquer etapa interrompe as etapas seguintes
- **AND** o resultado é visível no Pull Request como check

#### Scenario: Falha de lint bloqueia merge
- **WHEN** o pipeline falha na etapa de lint
- **THEN** o merge do Pull Request fica bloqueado no GitHub
- **AND** a mensagem de erro indica qual arquivo e linha causou a falha

#### Scenario: Todos os checks passam
- **WHEN** todas as etapas do pipeline passam com sucesso
- **THEN** o Pull Request fica desbloqueado para merge

---

### Requirement: Pipeline de CD automatizado
O sistema SHALL realizar deploy automático para produção quando um push ocorre na branch `main` e todos os checks de CI passam.

#### Scenario: Merge em main dispara deploy
- **WHEN** um Pull Request é mergeado na branch `main`
- **AND** todos os checks de CI passam
- **THEN** o pipeline executa o build Docker (multi-stage: frontend + backend)
- **AND** faz push da imagem para o registry configurado
- **AND** realiza o deploy no ambiente de produção

#### Scenario: Falha no build Docker bloqueia deploy
- **WHEN** o build Docker falha durante o CD
- **THEN** o deploy não ocorre
- **AND** o ambiente de produção anterior permanece ativo sem interrupção

---

### Requirement: Health check no container
O container Docker SHALL declarar um health check que verifica a disponibilidade da aplicação.

#### Scenario: Container saudável
- **WHEN** o container está rodando e a aplicação respondendo
- **THEN** `GET /api/saude` retorna HTTP 200
- **AND** o status do container é `healthy`

#### Scenario: Container não saudável
- **WHEN** a aplicação não responde ao health check por 3 tentativas consecutivas
- **THEN** o status do container é `unhealthy`
- **AND** o orquestrador pode reiniciar o container automaticamente

---

### Requirement: Migração automática no startup
O container SHALL executar `alembic upgrade head` antes de iniciar o servidor, garantindo que o schema do banco esteja sempre sincronizado com o código.

#### Scenario: Startup com migrações pendentes
- **WHEN** o container inicia e há migrações não aplicadas
- **THEN** as migrações são aplicadas antes do servidor aceitar requisições
- **AND** o servidor inicia normalmente após a migração concluir com sucesso

#### Scenario: Startup com migração falhando
- **WHEN** uma migração falha durante o startup
- **THEN** o container encerra com código de erro não-zero
- **AND** o servidor não inicia
