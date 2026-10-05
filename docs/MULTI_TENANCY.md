# Operação multi-tenant

## Modelo e contexto

`empresa` é dona dos cadastros operacionais. Cada requisição autenticada que acesse esses dados envia `X-Empresa-ID`; o backend valida uma associação ativa em `usuario_empresa` e define `app.usuario_id` e `app.empresa_id` na transação. O cliente web guarda a seleção localmente e envia o cabeçalho em HTTP. O handshake WebSocket valida a mesma associação.

Papéis `admin` e `membro` pertencem à associação, não à identidade global. A coluna histórica `usuarios.admin` é convertida em associações durante a migração e zerada; a aplicação usa o papel da empresa ativa.

O GUC tenant é contexto transacional definido pelo backend depois de validar a associação. RLS protege contra consultas da aplicação sem filtro e contra erros de escopo; como qualquer GUC customizado do PostgreSQL pode ser alterado por uma sessão SQL com acesso ao runtime, RLS não é uma barreira contra execução arbitrária de SQL sob a própria credencial runtime. Evite SQL dinâmico não parametrizado e proteja a credencial runtime.

## Credenciais do banco

O serviço `app` usa `hub_runtime`, que não é proprietário das tabelas nem tem `BYPASSRLS`. O serviço `migrate` usa a credencial proprietária/migradora configurada por `HUB_MIGRATION_PASSWORD`, reservada para migrações e provisionamento. Em instalação nova com Compose, defina `HUB_RUNTIME_PASSWORD`, `HUB_MIGRATION_PASSWORD` e `HUB_SECRET_KEY` antes de subir os serviços. Os valores de desenvolvimento do Compose são somente para uso local.

Para uma instalação existente ou banco gerenciado, um DBA deve provisionar `hub_runtime` (LOGIN, sem SUPERUSER, sem CREATEDB, sem CREATEROLE, sem REPLICATION e sem BYPASSRLS), conceder acesso ao banco/schema e executar a migração com uma credencial proprietária/migradora. A identidade migradora precisa poder alterar as tabelas e executar o helper RLS `app_empresa_admin` como função definidora com `row_security=off`. A migração concede privilégios de tabela/sequência e configura privilégios default para objetos futuros criados pela identidade migradora. Configure `HUB_DATABASE_URL` da API com a credencial runtime. Não use a credencial migradora na API.

## Migração, backup e recuperação

1. Faça backup consistente do banco e confirme que a restauração foi ensaiada.
2. Em cópia representativa, execute `alembic upgrade head` com a credencial migradora. A migração 0005 preserva a UUID da empresa iSolutis e atribui a ela as linhas legadas.
3. Compare contagens, totais financeiros, unicidades, relações e memberships antes do cutover. Confirme as policies RLS, as views tenant-aware e o acesso efetivo usando `hub_runtime`.
4. Atualize a API para a credencial runtime e habilite o tráfego somente depois dos checks. A migração 0005 não oferece downgrade: em caso de falha, interrompa o tráfego e restaure o backup consistente, ou aplique uma correção roll-forward revisada.
5. Após backfill e `ANALYZE`, meça os planos e latências dos workloads reais por tenant. Não habilite particionamento ou índices covering sem comparação de leitura, escrita e espaço.

O container `migrate` é executado separadamente com `docker compose --profile migrate run --rm migrate`. O processo web não executa migrações no startup.

Para bootstrap/redefinição de acesso, use `python -m app.scripts.criar_admin --email ... --nome ... --empresa-nome ...` com `HUB_MIGRATION_DATABASE_URL` apontando para a credencial de provisionamento. Para importar dados legados, forneça sempre `--empresa-id` e `--usuario-id` de um administrador ativo daquela empresa.

## Limites operacionais atuais

A role runtime local é criada pelo script de inicialização apenas quando o volume PostgreSQL é novo. Volumes existentes não são alterados automaticamente; provisionamento de role, credenciais e grants requer o procedimento do DBA. O ensaio em cópia de produção e a coleta de baseline/EXPLAIN precisam ser feitos com dados e workload representativos antes do cutover.
