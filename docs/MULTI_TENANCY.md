# Operação multi-tenant

## Modelo e contexto

`empresa` é dona dos cadastros operacionais. Cada requisição autenticada que acesse esses dados envia `X-Empresa-ID`; o backend valida uma associação ativa em `usuario_empresa` e define `app.usuario_id` e `app.empresa_id` na transação. O cliente web guarda a seleção localmente e envia o cabeçalho em HTTP. O handshake WebSocket valida a mesma associação.

Os papéis `admin`, `financeiro`, `comercial` e `membro` pertencem à associação (`usuario_empresa.papel`), não à identidade global. A coluna `usuarios.admin` foi removida na migração 0010; a aplicação usa o papel da empresa ativa.

Permissões derivadas do papel (`app/domain/papeis.py`; o backend recusa com 403 e o front decide menus e carga só pela lista de permissões de `GET /empresas`):

| Permissão | Cobre | admin | financeiro | comercial | membro |
|---|---|:-:|:-:|:-:|:-:|
| `base` | painel (blocos permitidos), tarefas, projetos, equipe (lista), lista mínima de clientes, Minha conta, consulta de CNPJ | ✓ | ✓ | ✓ | ✓ |
| `comercial` | clientes (cadastro completo), negócios, orçamentos, produtos | ✓ | | ✓ | |
| `financeiro` | módulo financeiro, parceiros, faturamento, despesas, relatórios | ✓ | ✓ | | |
| `administracao` | usuários, convites, dados da empresa, onboarding | ✓ | | | |

`tests/test_permissoes_rotas.py` falha se uma rota de dados não declarar permissão (`exige(...)`). A migração 0010 converteu os antigos `membro` em `comercial`. Empresas são criadas só pelo operador (`criar_admin`); `POST /empresas` não existe e `criar_empresa` não é executável pela credencial da API.

O GUC tenant é contexto transacional definido pelo backend depois de validar a associação. RLS protege contra consultas da aplicação sem filtro e contra erros de escopo; como qualquer GUC customizado do PostgreSQL pode ser alterado por uma sessão SQL com acesso ao runtime, RLS não é uma barreira contra execução arbitrária de SQL sob a própria credencial runtime. Evite SQL dinâmico não parametrizado e proteja a credencial runtime.

## Credenciais do banco

O serviço `app` usa `hub_runtime`, que não é proprietário das tabelas nem tem `BYPASSRLS`. O serviço `migrate` usa a credencial proprietária/migradora configurada por `HUB_MIGRATION_PASSWORD`, reservada para migrações e provisionamento. Em instalação nova com Compose, defina `HUB_RUNTIME_PASSWORD`, `HUB_MIGRATION_PASSWORD` e `HUB_SECRET_KEY` antes de subir os serviços. Os valores de desenvolvimento do Compose são somente para uso local.

Para uma instalação existente ou banco gerenciado, um DBA deve provisionar `hub_runtime` (LOGIN, sem SUPERUSER, sem CREATEDB, sem CREATEROLE, sem REPLICATION e sem BYPASSRLS), conceder acesso ao banco/schema e executar a migração com uma credencial proprietária/migradora. A identidade migradora precisa poder alterar as tabelas e executar o helper RLS `app_empresa_admin` como função definidora com `row_security=off`. A migração concede privilégios de tabela/sequência e configura privilégios default para objetos futuros criados pela identidade migradora. Configure `HUB_DATABASE_URL` da API com a credencial runtime. Não use a credencial migradora na API.

## Área da plataforma (operador)

A migração 0017 cria a identidade do operador (`operador_plataforma`), o `empresa.status` (`ativa`/`suspensa`), a
auditoria `auditoria_plataforma` e o papel `hub_plataforma` (sem login, quando não existe).

- **Credencial.** Habilite o login do papel e informe a URL na API: `ALTER ROLE hub_plataforma LOGIN PASSWORD '...'` e
  `HUB_PLATAFORMA_DATABASE_URL`. O papel NÃO tem privilégio em nenhuma tabela: só executa as funções `plataforma_*`
  (`SECURITY DEFINER`), que conferem o operador, aplicam as regras (último administrador) e gravam a auditoria na mesma
  transação. Sem a variável, as rotas `/plataforma/*` respondem 503; o resto do Hub não é afetado.
- **Quem cria empresas.** `hub_runtime` perdeu `EXECUTE` em `criar_empresa`. O `admin` de uma empresa atualiza os dados
  dela, mas um gatilho recusa a mudança de `status` por `hub_runtime`/`hub_plataforma`: só as funções do operador a fazem.
- **Auditoria.** `auditoria_plataforma` só recebe inserções (nenhum papel da aplicação tem privilégio, e um gatilho recusa
  UPDATE/DELETE até do dono). Revise periodicamente a lista de operadores: `select * from operador_plataforma`.
- **Primeiro operador.** `python -m app.scripts.criar_admin --email ... --nome ... --operador` (credencial migradora).
- **Suspensão.** Empresa suspensa sai da escolha de empresa e recusa requisições (`empresa_inacessivel`) na próxima
  chamada; os dados ficam intactos. O operador não vê dados de negócio de nenhuma empresa.
- **Reversão.** `alembic downgrade 0016` (o papel `hub_plataforma` é do cluster e não é removido).

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

## Escopo de acesso dentro da empresa (migração 0013)

Além do isolamento entre empresas, a 0013 restringe **dentro** da empresa o que cada pessoa vê e edita (change OpenSpec `escopo-de-acesso`):

- **Papel** (admin, financeiro, comercial, membro) continua liberando áreas; **equipes** (`equipe`, `equipe_lider`, `equipe_membro`) definem de quem a pessoa enxerga registros: ela e toda a árvore que lidera. Admin vê tudo; a área financeira não é escopada.
- **Dono**: `responsavel_id` em clientes (`parceiro_negocio`), negócios, projetos, etapas e tarefas; o orçamento segue o negócio. O dono do cliente vê tudo do cliente; registro sem dono herda a visibilidade do registro acima e, sem nenhum dono acima, é visível a todos da área.
- **Projetos**: participantes (responsável, responsáveis de etapa e `projeto_participante`) veem o projeto inteiro e editam só o que é seu; quem só executa uma tarefa vê só ela.
- **Imposição**: as políticas `tenant_*` dessas tabelas viraram `RESTRICTIVE` e ganharam políticas permissivas `escopo_*` de leitura e escrita. Troca de dono e vínculo com cliente são conferidos pelo gatilho `app_validar_escopo`, que registra as transferências em `transferencia_dono` (leitura só para admin).
- **Contexto por transação**: a API grava `app.usuario_id` e `app.empresa_id` e chama `app_definir_escopo()`, que grava `app.usuarios_visiveis`, `app.ve_tudo`, `app.ve_financeiro` e `app.lider`. A sessão reaplica esse contexto em toda nova transação (`after_begin` em `app/db.py`). Sem contexto, as funções falham fechadas (ninguém no escopo, sem admin).
- **Funções `SECURITY DEFINER`** (`app_dono_cliente`, `app_pode_ver_*`, `app_pode_editar_*`, `app_clientes_referencia`…) leem tabelas com `row_security = off`, como `app_empresa_admin`. Por isso a identidade migradora precisa poder ignorar RLS (superusuário, `BYPASSRLS` ou, no Neon, o papel proprietário do banco), e todas as funções filtram explicitamente por `app_empresa_id()`.

### Deploy

1. Aplique a 0013 primeiro numa branch do Neon: `alembic upgrade head`, depois `pytest tests/test_escopo_sql.py tests/test_escopo_api.py` apontando para ela.
2. Publique backend e frontend logo após a migração.
3. **Monte as equipes imediatamente** (Administração › Equipes). Até lá, cada pessoa vê só o que é dela, mais o que não tem dono, e os líderes perdem a visão do time.
4. Revise os donos atribuídos aos clientes (o responsável do negócio mais recente com cada um).
5. Rollback: `alembic downgrade 0012` descarta equipes, participantes, donos de cliente e o registro de transferências.

### Desempenho medido (PostgreSQL 16 local, `hub_runtime`)

Carga sintética: 40 pessoas, 3.000 clientes, 10.000 negócios, 2.000 projetos e 20.000 tarefas numa empresa.

| Consulta | Visíveis | Tempo |
|---|---|---|
| `count(*)` negócios, líder de 9 pessoas | 3.350 | 118 ms |
| `count(*)` tarefas, líder | 8.512 | 475 ms |
| `count(*)` negócios, comercial sem liderança | 487 | 86 ms |
| `count(*)` projetos, comercial | 99 | 25 ms |
| `count(*)` tarefas, admin (atalho `app_ve_tudo`) | 20.000 | 16 ms |

As regras são funções avaliadas linha a linha, então os planos usam varredura sequencial; o custo cresce com o tamanho da tabela, não com o que a pessoa vê. Para os volumes atuais (centenas a poucos milhares de registros por empresa) isso fica em dezenas de milissegundos. **Pendência:** acima de ~10 mil tarefas ou negócios por empresa, pré-calcular por transação os conjuntos de projetos e clientes visíveis e reescrever as políticas como predicados indexáveis.
