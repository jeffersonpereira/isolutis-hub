# Design

## Context

- Empresas e vínculos: `empresa`, `usuario_empresa (empresa_id, usuario_id, papel, ativo)`, ambos com RLS. A função
  `criar_empresa` (0005) é `SECURITY DEFINER` mas liberada ao `hub_runtime` e cria a empresa com o próprio chamador como
  `admin`; a spec `provisionamento-de-empresas` já exige que a aplicação não crie empresa, portanto ela precisa ser
  revisada junto desta mudança.
- Convites (`services/convites.py`) são por empresa, emitidos por um `admin` dela, com aceite público em
  `/convite/{token}` que cria a conta ou apenas vincula uma conta existente.
- `deps.empresa_atual` valida a membership ativa pelo cabeçalho `X-Empresa-ID` e fixa empresa/usuário na transação para
  a RLS. O design do multi-tenant decidiu não haver superadmin com bypass implícito.
- `criar_admin.py` usa `HUB_MIGRATION_DATABASE_URL` (credencial migradora) e é hoje o único provisionamento.

## Goals / Non-Goals

**Goals:**
- Operador cria empresa e gerencia membros de qualquer empresa pela aplicação.
- Operador sem acesso a dados de negócio, garantido no banco e não só na API.
- Toda ação do operador auditada.

**Non-Goals:**
- Métricas de uso, plano, cobrança ou limite de usuários.
- Operador entrar na empresa para suporte (impersonar) ou ler dados de negócio.
- Promover ou remover operadores pela interface (só pelo script, por ora).
- Excluir empresa (apenas suspender).

## Decisions

### 1. Operador é identidade separada: tabela `operador_plataforma`
`operador_plataforma (usuario_id PK, criado_em)`. Não é papel em `usuario_empresa` nem coluna em `usuarios`.
Alternativa descartada: flag global no usuário, que o desenho do multi-tenant evitou por misturar plataforma com
empresa. Operador que também é membro de empresas segue sujeito às regras dessas empresas quando as usa; a área da
plataforma não concede nada dentro delas.

### 2. Papel de banco próprio `hub_plataforma` e funções `SECURITY DEFINER`
As rotas `/plataforma/*` usam um pool com outra credencial (`HUB_PLATAFORMA_DATABASE_URL`, papel `hub_plataforma`).
Esse papel NÃO tem `SELECT` nas tabelas de negócio; só executa funções `plataforma_*`
(`plataforma_listar_empresas`, `plataforma_criar_empresa`, `plataforma_definir_status`, `plataforma_listar_membros`,
`plataforma_vincular_membro`, `plataforma_definir_papel`, `plataforma_desativar_membro`). Cada função confere
`app_usuario_id()` em `operador_plataforma` e grava em `auditoria_plataforma` na mesma transação. Assim, mesmo um bug de
rota não expõe dados de negócio. O `hub_runtime` perde `EXECUTE` em `criar_empresa`, que passa a ser usada só por
`plataforma_criar_empresa`.
Alternativa descartada: usar o `hub_runtime` com checagem apenas na API, por ser um único ponto de falha sobre dados
de todos os clientes.

### 3. Status da empresa: `empresa.status` (`ativa` | `suspensa`)
Default `ativa`, CHECK nos dois valores. `deps.empresa_atual` recusa empresa suspensa com o código
`empresa_inacessivel` (o cliente já reabre a escolha de empresa); `GET /empresas` não a devolve. Nada é apagado, então
reativar restaura o acesso. Cenários de realtime/WebSocket da empresa suspensa também são encerrados na próxima
validação.

### 4. Criação de empresa por convite ao administrador inicial
`plataforma_criar_empresa(nome, inscricao?, email_admin, nome_admin)` cria a empresa sem membros e um convite de papel
`admin` com `criado_por` = operador. O aceite reaproveita o fluxo atual (conta nova define senha; conta existente só
vincula). O e-mail é enviado pelo serviço de convites existente, fora da transação do banco. O assistente de onboarding
já dispara para a empresa recém-criada no primeiro acesso do admin.
`convites.criado_por` só referencia `usuarios` e `convites` não tem RLS, então o operador (que é um usuário) emite o convite sem mudança de schema.

### 5. Gestão de membros: vincular por convite, não por senha
O operador não define senha de ninguém. "Vincular" emite convite (reaproveitando a invalidação do convite anterior).
Trocar papel e desativar atuam em `usuario_empresa`, e a regra existente de sessão invalida o acesso na requisição
seguinte. Regra do **último administrador**: a função recusa rebaixar ou desativar o último `admin` ativo da empresa.

### 6. Auditoria
`auditoria_plataforma (id, operador_id, empresa_id, acao, antes jsonb, depois jsonb, criado_em)`, append-only (sem
`UPDATE`/`DELETE` para nenhum papel da aplicação). Gravada dentro de cada função `plataforma_*`.

### 7. Frontend
Vista `plataforma` registrada só quando `GET /me` traz `operador: true`; item no menu do usuário. Telas: lista de
empresas com busca, detalhe da empresa (membros, convites pendentes, status) e formulário de nova empresa, seguindo os
componentes de cadastro em página existentes.

### 8. Primeiro operador
(`GET /plataforma/acesso` substitui o campo `operador` em `/auth/eu` previsto antes: não toca o contrato de login.)

`criar_admin.py --operador` marca o usuário em `operador_plataforma`; `--empresa-*` deixa de ser obrigatório quando só
se pede `--operador`.

## Risks / Trade-offs

- **Concentração de poder** → só operadores, papel de banco restrito, auditoria append-only e sem leitura de dados de
  negócio; revisar a lista de operadores por rotina operacional.
- **Convite com e-mail errado** → a empresa nasce sem administrador; o operador reenvia/reemite pela gestão de membros.
- **Segunda credencial de banco por ambiente** → documentada em `README`/`docs`. Sem a variável, a API sobe com aviso e
  as rotas `/plataforma/*` respondem 503 (falhar na inicialização quebraria implantações que ainda não usam a área).
- **Empresa suspensa com sessão aberta** → bloqueio na próxima requisição, não instantâneo; aceitável.
