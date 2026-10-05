## Context

O banco hoje possui `companies` somente no módulo financeiro e em `parceiro_negocio`. `empresa_atual()` escolhe a empresa mais antiga, sem validar vínculo com o usuário. O domínio comercial, operações e vários cadastros não têm proprietário. O usuário é uma identidade global (`usuarios`), mas `admin` também é global. A numeração do orçamento usa sequência global por ano.

A revisão de DBA confirmou que a fronteira tenant deve ser aplicada no modelo relacional, nas consultas e na autorização. Apenas filtrar algumas rotas não garante isolamento, e apenas adicionar `empresa_id` às tabelas principais não impede relações cruzadas entre tenants.

## Goals / Non-Goals

**Goals:**
- Renomear o conceito persistido para `empresa` e todas as referências para `empresa_id`.
- Fazer cada registro operacional pertencer a exatamente uma empresa.
- Permitir que uma identidade de usuário participe de várias empresas com papéis e estado de acesso por empresa.
- Garantir que autorização, FKs, unicidades e RLS impeçam leitura, escrita ou vínculo entre tenants.
- Migrar os dados existentes para a empresa iSolutis preservando IDs, relações, auditoria e operações.

**Non-Goals:**
- Compartilhar dados operacionais entre empresas ou modelar grupos empresariais/consolidação contábil.
- Transformar catálogos de referência públicos em cadastros tenantizados.
- Prover faturamento SaaS, provisionamento automático ou administração comercial da plataforma.
- Permitir tenants sem isolamento lógico no banco.

## Decisions

1. **Empresa é a fronteira de propriedade.** Renomear `companies` para `empresa`, `company_id` para `empresa_id` e o modelo ORM para `Empresa`. Registros existentes pertencem à empresa iSolutis criada na migração financeira. API e frontend adotam a nomenclatura `empresa`.

2. **Identidade global, acesso por associação.** `usuarios` continua global para login/e-mail. Nova tabela `usuario_empresa` associa `(empresa_id, usuario_id)` com papel (`admin` ou `membro`), estado ativo e autoria. O atual `usuarios.admin` deixa de autorizar operações de tenant; privilégios de administração tornam-se por empresa. Não há papel de superadministrador da plataforma nesta entrega.

3. **Empresa ativa explícita por requisição.** APIs autenticadas recebem `X-Empresa-ID`. O backend valida associação ativa do usuário antes de executar operações tenant-scoped e grava `app.empresa_id` transaction-local junto de `app.usuario_id`. WebSocket autentica o mesmo contexto. Uma empresa não é inferida pelo primeiro registro nem aceita sem membership.

4. **Tenantização de todas as operações e cadastros editáveis.** Acrescentar `empresa_id NOT NULL` a parceiros, papéis atribuídos, produtos, negócios, orçamentos/itens, sequências de orçamento, receitas, despesas, categorias, investidores/investimentos, projetos/etapas, tarefas/checklists, plano de contas, contas bancárias e títulos financeiros. Tabelas filhas também carregam `empresa_id` para permitir FKs compostas e políticas RLS diretas.

5. **Catálogos compartilhados limitados.** `usuarios` (identidade), `municipio`, `instituicao_financeira` e códigos estáveis de `papel_parceiro` são globais. Os vínculos `parceiro_papel` são por empresa. Produtos, categorias, investidores e demais cadastros criados pela empresa são tenant-scoped; investidores com o mesmo nome em tenants distintos são registros separados.

6. **Tags são classificação livre, papéis são semântica de domínio.** `tag_parceiro(empresa_id, id, nome, ativo, ...)` guarda tags definidas pela empresa. `(empresa_id, lower(btrim(nome)))` é único. `parceiro_tag(empresa_id, parceiro_id, tag_id, ...)` é associação N:N com FKs compostas para parceiro e tag; não pode cruzar tenants. Tags não substituem `papel_parceiro`: regras como negócio exigir papel cliente continuam baseadas em papéis. Parceiros existentes iniciam sem tags; nenhuma tag é inferida automaticamente.

7. **Integridade cross-tenant no PostgreSQL.** Toda tabela que é alvo de relação tenant expõe `UNIQUE(id, empresa_id)`. FKs de negócio usam `(registro_id, empresa_id)`; filhos carregam o tenant e referenciam o pai com chave composta. Índices e chaves únicas de domínio são prefixados por empresa. Isso complementa filtros obrigatórios do serviço.

8. **RLS como segunda barreira obrigatória.** Habilitar e forçar Row-Level Security para tabelas tenant-scoped com políticas `USING` e `WITH CHECK` baseadas em `current_setting('app.empresa_id', true)`. A aplicação usa papel PostgreSQL sem ownership e sem `BYPASSRLS`; migrações usam papel distinto. Variáveis de contexto são definidas localmente à transação para evitar vazamento pelo pool.

9. **Numeração de orçamento por empresa e ano.** A sequência passa a ter chave `(empresa_id, ano)`; `numero` é único por empresa. A função de numeração recebe empresa explicitamente e bloqueia/atualiza a sequência por tenant/ano.

10. **Migração em fases, aditiva e com verificação.** Não editar migrations já aplicadas. Renomear/add estruturas; criar membership para usuários existentes na iSolutis preservando papel administrativo por empresa; adicionar `empresa_id` nullable e backfill de todas as linhas existentes para iSolutis; verificar órfãos e conflitos; criar índices/FKs compostas; tornar NOT NULL; habilitar RLS; então ativar a exigência de tenant no backend. Criar catálogo e associação de tags vazios, sem classificar automaticamente parceiros legados. Backup é obrigatório antes do cutover. Rollback após habilitar tenants adicionais é restore/roll-forward, não downgrade destrutivo.

11. **Filtro por várias tags usa OR.** `tag_ids` combina-se por OR dentro da dimensão tags (parceiro tem qualquer tag selecionada); papel, busca e tags se combinam por AND. Tag inativa não aparece nas opções de filtro nem pode ser atribuída novamente, mas vínculos existentes seguem visíveis no detalhe. Tags usadas são arquivadas, não apagadas; exclusão física fica restrita a tags sem vínculos.

12. **Índices vêm dos padrões de consulta, não de uma regra cega.** Para cada tenant-scoped listagem, combinar igualdade em `empresa_id` com filtros e ordenação usados pela tela. Candidatos iniciais a validar: parceiros `(empresa_id, nome, id)`; negócios `(empresa_id, etapa, previsao, id)` e parcial `(empresa_id, previsao, id)` para abertos; orçamentos `(empresa_id, numero)` único e parcial `(empresa_id, data, id)` para enviados; receitas `(empresa_id, vencimento, criado_em, id)`; despesas `(empresa_id, data, criado_em, id)`; projetos `(empresa_id, entrega, id)`; tarefas `(empresa_id, coluna, prioridade_ordem, prazo, criado_em, id)`. Restrições compostas e índices no lado filho das FKs serão inventariados. Esses índices substituem ou ampliam os existentes, não são adicionados cegamente em duplicata; cada candidato será conferido por `EXPLAIN (ANALYZE, BUFFERS)` sob o papel runtime/RLS.

13. **Consultas por período usam intervalos sargáveis.** Filtros `extract(year/month FROM data) = ...` serão substituídos por intervalos semiabertos `[início, próximo_início)` para habilitar range scan nos B-trees por `(empresa_id, data)`. Agregações continuam agrupando por mês depois do filtro. Resultados paginados terão ordenação estável com desempate por ID.

14. **Não particionar nem adicionar índices caros sem evidência.** Não adotar particionamento, `INCLUDE`/covering indexes, índices adicionais por status ou GIN multicoluna sem planos, latências e tamanhos de tenant que justifiquem custo de escrita, espaço e operação. GIN trigram existente em tarefas é preservado inicialmente; busca de parceiro substring pode usar GIN separado combinado por bitmap com filtro B-tree tenant-first, sujeito à medição.

15. **Tags seguem acesso bidirecional simples.** PK `(empresa_id, parceiro_id, tag_id)` serve os chips por parceiro; índice `(empresa_id, tag_id, parceiro_id)` serve filtros de tags. Filtro OR será feito com `EXISTS` (ou plano equivalente) para não duplicar parceiros. O nome será trim-normalizado na escrita; índice único por empresa sobre nome case-insensitive e índice de opções ativas/ordenadas serão avaliados para evitar função repetida ou índice duplicado.

16. **Sequência de orçamento preserva o contrato sem lacunas em rollback.** O contador transacional em linha `(empresa_id, ano)` permanece porque o schema atual explicitamente devolve o número quando a transação faz rollback. A chave composta remove contenção entre empresas e anos, mas emissões simultâneas no mesmo tenant/ano ainda serializam. `nextval` só será alternativa se o negócio aceitar lacunas; qualquer mudança requer decisão funcional, não apenas benchmark.

17. **RLS e views são revisadas em conjunto.** Views que acessam dados tenant serão `security_invoker=true` no PostgreSQL 16 ou explicitamente protegidas; funções e triggers serão auditadas para não escapar do contexto. RLS reduz o risco de filtro omitido, mas a GUC customizável não é defesa contra SQL arbitrário executado sob o mesmo papel; membership no backend continua autoridade.

### Índices candidatos por padrão de acesso

Os candidatos abaixo correspondem às consultas atuais do código e devem ser validados em dados representativos com RLS. A migração deve substituir ou ampliar índices existentes, não manter duplicatas. Índice parcial e combinação de colunas dependem da seletividade observada.

| Consulta principal | Índice candidato inicial | Notas |
|---|---|---|
| Parceiros por empresa e nome | B-tree `(empresa_id, nome, id)` | Para substring, avaliar GIN trigram em nome/documento e bitmap com tenant; manter o GIN só se busca substring for frequente. Documento único parcial por `(empresa_id, cpf_cnpj)`. |
| Parceiro por tags | PK `(empresa_id, parceiro_id, tag_id)` e inverso `(empresa_id, tag_id, parceiro_id)` | O primeiro carrega chips; o segundo inicia filtro OR por tag via `EXISTS`. |
| Negócios por etapa/previsão | `(empresa_id, etapa, previsao, id)`; parcial `(empresa_id, previsao, id)` para etapas abertas | Substitui índices de etapa/previsão e previsão aberta atuais depois de comparar os planos. |
| Orçamentos por número/status/data | Único `(empresa_id, numero)`; parcial `(empresa_id, data, id)` para enviados | Não duplicar ordenação se o índice unique já atender `ORDER BY numero DESC`; status vencido é derivado e não entra em predicado volátil. |
| Receitas por vencimento e histórico do parceiro | `(empresa_id, vencimento, criado_em, id)` e, se consultado, `(empresa_id, cliente_id, vencimento)` | Grupo de parcelas pode usar unique parcial `(empresa_id, grupo_id, parcela)` quando o grupo não é NULL. |
| Despesas por período/status | `(empresa_id, data, criado_em, id)`; parciais por status apenas se seletividade justificar | Range de data é pré-requisito para aproveitar B-tree; evitar `INCLUDE(valor)` sem prova de index-only scan. |
| Investimentos | `(empresa_id, data, id)` e `(empresa_id, investidor_id, data)` | Sustenta lista temporal e totais agrupados por investidor. |
| Projetos | `(empresa_id, entrega, id)`, `(empresa_id, cliente_id)` e unique parcial `(empresa_id, negocio_id)` | Negócio opcional; índice unique parcial evita redundância para NULLs. |
| Tarefas | `(empresa_id, coluna, prioridade_ordem, prazo, criado_em, id)` e parcial para responsável/prazo abertos | GIN trigram existente em busca permanece candidato global; comparar bitmap combinado com tenant B-tree. |
| Títulos financeiros | `(empresa_id, tipo_conta, status, data_vencimento, id)` ou por data antes dos filtros, conforme plano; índices parciais abertos/quitados | Escolher a ordenação de chaves pelos filtros mais seletivos e pelas consultas de fluxo de caixa. |

Toda FK composta tenant-scoped será acompanhada de índice de filho quando existir consulta, join ou ação referencial que o use; o PostgreSQL cria índice no alvo único, mas não no lado filho. Catálogos financeiros já indexados por empresa só precisam de rename/revisão de redundância.

### Plano de medição

Capturar cardinalidade/tamanho por tabela e distribuição p50/p95/máximo de linhas por empresa; frequência de busca e concorrência de gravação/orçamento. Após backfill, executar `ANALYZE`. Comparar `EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)` para lista por empresa/ordem, períodos por data/status, busca de parceiro, filtro OR de tags, kanban, painéis, fluxo financeiro, detalhe com filhos e writes concorrentes, usando runtime role com RLS em tenant pequeno e grande. Medir p50/p95, heap/buffer reads, sort/hash spill, WAL, custo de escrita e tamanho de índices. Não assumir que `Index Scan` é melhor que `Seq Scan`; não adotar particionamento, BRIN, covering ou GIN multicoluna sem evidência de custo/benefício.

## Risks / Trade-offs

- **Migração de alto impacto e potencialmente longa** → fases expand/contract, backfill verificável e índices concorrentes quando o volume justificar; ensaio em cópia de produção e backup antes do cutover.
- **RLS configurada incorretamente ou conexão com privilégio de bypass** → papel de runtime separado, `FORCE ROW LEVEL SECURITY`, cenários de isolamento no SQL e validação de configuração do banco no deploy.
- **Contexto tenant ausente ou stale no pool** → `set_config(..., true)` em cada transação, falha fechada quando header/membership/contexto faltar e testes de alternância entre tenants na mesma conexão.
- **Breaking change no API e integração externa** → comunicar nova exigência de `X-Empresa-ID`; identificar clientes externos antes da implantação. O esquema interno e tipos frontend mudam para `empresa_id`.
- **Unicidades antes globais podem colidir após dividir dados** → inventariar e resolver colisões antes de criar índices compostos; dados existentes ficam juntos em iSolutis, então não devem criar colisões novas por backfill.
- **Sem superadmin da plataforma** → operações globais de suporte ficam fora de escopo; eventual modelo de plataforma deve ser adicionado separadamente sem bypass implícito da empresa.
- **Índices tenant-first podem aumentar write amplification e espaço** → migrar os índices existentes em vez de duplicá-los e manter candidatos condicionados a planos e medições por tenant.
- **Contenção por numeração sem lacunas no mesmo tenant/ano** → manter transação curta, medir bursts concorrentes e monitorar espera na linha do contador; tenants e anos diferentes usam locks independentes.
- **RLS em views pode não aplicar o contexto do chamador por padrão** → `security_invoker` em PostgreSQL 16, revisão de funções/triggers e planos medidos sob runtime role com RLS ativa.

## Migration Plan

1. Criar `empresa` e `usuario_empresa`, renomeando `companies` sem recriar IDs; mapear `usuarios.admin` existente para papel da associação com iSolutis.
2. Adicionar `empresa_id` nullable às tabelas legadas, preencher com o ID iSolutis e auditar contagens, órfãos, vínculos e unicidades.
3. Incluir empresa nas sequências e números de orçamento; preencher sequência por ano a partir dos números existentes.
4. Criar `UNIQUE(id, empresa_id)`, índices compostos dirigidos às consultas observadas, FKs compostas e colunas tenant nos filhos; revisar/remover índices redundantes, validar constraints e tornar as colunas NOT NULL.
5. Separar papéis PostgreSQL de migração e runtime; habilitar/forçar RLS e instalar políticas para tabelas tenant; converter views para semântica invoker e revisar funções/triggers.
6. Publicar backend que resolve `X-Empresa-ID` por membership, define o contexto transacional e aplica o tenant a todos os serviços; em seguida publicar frontend com seleção/listagem de empresas e header.
7. Após backfill/índices, rodar `ANALYZE`; comparar `EXPLAIN (ANALYZE, BUFFERS, WAL)` das consultas críticas com runtime role/RLS e dados representativos por tenant; medir leituras e escrita sob carga e remover candidatos que não melhorem objetivo sem regressão aceitável.
8. Habilitar tráfego multi-tenant após verificação automatizada de isolamento e performance. Manter backup e plano de roll-forward; não fazer downgrade depois de cadastrar dados de outro tenant.

## Open Questions

- O cabeçalho `X-Empresa-ID` é o mecanismo escolhido inicialmente; caso existam consumidores terceiros, é necessário definir período de compatibilidade e versão de API.
- Confirmar inventário de integrações externas antes do breaking change. Por ora o design assume clientes internos e cutover coordenado.
- Capturar distribuição e crescimento de dados por empresa, latências p50/p95, frequência das buscas e concorrência de escrita antes de fixar SLA ou aprovar índices opcionais/particionamento.
