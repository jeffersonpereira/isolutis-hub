## 1. Preparar o modelo e a migração

- [x] 1.1 Inventariar tabelas, relações, índices únicos, padrões WHERE/ORDER BY e consultas mais frequentes/caras; registrar contagens e tamanho por tabela/tenant como baseline.
- [x] 1.2 Criar migração aditiva que renomeia `companies` para `empresa`, cria `usuario_empresa` e preserva o ID da iSolutis.
- [x] 1.3 Mapear membros existentes para iSolutis e migrar `usuarios.admin` para papel administrativo da associação, sem elevar privilégios globais.
- [x] 1.4 Adicionar `empresa_id` nullable a todas as tabelas operacionais e filhas; preencher por backfill com a iSolutis existente.
- [x] 1.5 Tenantizar sequência/função/número de orçamento e backfill dos contadores por empresa e ano.
- [x] 1.6 Validar órfãos, relações cross-tenant, colisões de unicidade e contagens antes de tornar as colunas NOT NULL.
- [x] 1.7 Adicionar uniques `(id, empresa_id)` e chaves estrangeiras compostas; verificar índices do lado filho, pois o PostgreSQL não os cria automaticamente.
- [x] 1.8 Substituir/ampliar índices atuais com candidatos por padrão real de consulta e evitar duplicatas para os mesmos prefixos e ordenações.
- [x] 1.9 Tornar `empresa_id` NOT NULL, definir constraints de tenant e registrar estratégia de restore/roll-forward da migração.
- [x] 1.10 Criar `tag_parceiro` e `parceiro_tag` sem classificar registros legados; adicionar unicidade case-insensitive por empresa e FKs compostas.
- [x] 1.11 Implementar índice de associação por parceiro e índice inverso por tag; usar consulta `EXISTS` para filtro OR sem duplicar parceiros.

## 2. Autenticação, membership e contexto tenant

- [x] 2.1 Implementar listagem de empresas do usuário e operações de membership com papéis por empresa.
- [x] 2.2 Resolver `X-Empresa-ID`, validar associação ativa e definir `app.usuario_id`/`app.empresa_id` transaction-local em dependências de requisição.
- [x] 2.3 Migrar autorização administrativa de `usuarios.admin` para papel `admin` da empresa nas rotas de equipe e finanças.
- [x] 2.4 Aplicar o contexto de empresa ao handshake do WebSocket e à presença/notificações.
- [x] 2.5 Atualizar scripts CLI, bootstrap de administrador, importador legado e operações de manutenção para exigir empresa explícita quando acessarem dados tenant.

## 3. Isolar todas as operações

- [x] 3.1 Adicionar `empresa_id` a schemas, modelos, serviços e consultas de parceiros, clientes e papéis de parceiro.
- [x] 3.2 Implementar CRUD/arquivamento de tags por empresa e atribuição múltipla atômica de tag IDs a parceiros, mantendo tags distintas de papéis.
- [x] 3.3 Adicionar filtro de listagem com semântica OR entre `tag_ids`, AND com busca/papel e resultados sem duplicação.
- [x] 3.4 Aplicar escopo e ownership a produtos, negócios, orçamentos/itens/sequências e todas as agregações/documentos comerciais.
- [x] 3.5 Aplicar escopo e ownership a faturamento, despesas, categorias, investidores/investimentos e relatórios financeiros existentes.
- [x] 3.6 Aplicar escopo e ownership a projetos/etapas, tarefas/checklists, equipe e consultas de autoria/responsáveis.
- [x] 3.7 Verificar que exportações, buscas, painéis, relatórios e cargas em lote sempre restringem empresa e relações.
- [x] 3.8 Atualizar referências API/OpenAPI para `empresa` e `empresa_id`, adicionar `X-Empresa-ID` e regenerar tipos do frontend.
- [x] 3.9 Implementar seleção de empresa ativa na interface e enviar o header em todas as chamadas HTTP e WebSocket.

## 4. Defesa no banco com RLS

- [x] 4.1 Criar papel runtime sem ownership e sem `BYPASSRLS`, papel de migração separado e configuração segura no Compose/deploy.
- [x] 4.2 Habilitar e forçar RLS em cada tabela tenant-scoped com políticas `USING` e `WITH CHECK` baseadas em `app.empresa_id`.
- [x] 4.3 Confirmar que tabelas globais se limitam às identidades e catálogos compartilhados definidos no design.
- [ ] 4.4 Confirmar que contexto ausente, inválido ou transação subsequente no pool não expõe dados de outro tenant.
- [x] 4.5 Revisar views, funções e triggers com acesso a tabelas tenant; usar `security_invoker=true` nas views tenant-aware sob PostgreSQL 16.

## 5. Verificação e rollout

- [x] 5.1 Adicionar testes de serviço/API para leitura, escrita, membership, papéis, alternância de empresa e respostas sem vazamento.
- [x] 5.2 Expandir testes SQL para FKs compostas, uniques tenant-local, sequência de orçamento e policies RLS sob papel runtime.
- [ ] 5.3 Atualizar E2E para selecionar empresas e validar isolamento com duas empresas e usuários com memberships distintos.
- [ ] 5.4 Cobrir nomes de tags duplicados após normalização, arquivo de tags usadas, associação cross-tenant e filtros OR/AND.
- [x] 5.5 Documentar criação de empresa, associação de usuários, credenciais de banco, migração, backup, cutover e recuperação.
- [ ] 5.6 Ensaiar migração e cutover em cópia representativa; comparar contagens, chaves e totais financeiros antes de habilitar tráfego multi-tenant.
- [x] 5.7 Reescrever filtros de ano/mês em datas como intervalos semiabertos e usar ordenação estável com desempate por ID.
- [ ] 5.8 Após backfill e `ANALYZE`, comparar planos `EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)` das consultas críticas sob runtime role/RLS para tenants pequenos e grandes.
- [ ] 5.9 Medir latência p50/p95, leituras, escrita, tamanho de índices e concorrência de orçamento; manter particionamento, covering e índices opcionais condicionados à evidência.
