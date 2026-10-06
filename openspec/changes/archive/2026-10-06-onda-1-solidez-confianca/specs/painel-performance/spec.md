## ADDED Requirements

### Requirement: Funil calculado por agregação no banco
O endpoint do painel SHALL calcular o funil de negócios usando queries `GROUP BY` no banco de dados, sem carregar registros individuais em memória.

#### Scenario: Funil retorna dados agregados
- **WHEN** `GET /api/v1/painel` é chamado
- **THEN** a query de funil usa `SELECT etapa, COUNT(*), SUM(valor), SUM(mensal) FROM negocios GROUP BY etapa`
- **AND** nenhum objeto `Negocio` é instanciado apenas para calcular o funil

#### Scenario: Performance com grande volume de dados
- **WHEN** a empresa tem 1.000+ negócios cadastrados
- **THEN** o endpoint responde em menos de 500ms
- **AND** o uso de memória da query não cresce proporcionalmente ao número de registros

---

### Requirement: Orçamentos aguardando calculados por query filtrada
O endpoint do painel SHALL obter orçamentos aguardando resposta com query direta no banco, sem carregar todos os orçamentos e filtrar em Python.

#### Scenario: Query filtrada por status enviado
- **WHEN** `GET /api/v1/painel` é chamado
- **THEN** a busca de orçamentos aguardando usa cláusula `WHERE status = 'enviado'` na query SQL
- **AND** não chama `svc_orcamentos.listar()` sem filtro

---

### Requirement: Skeleton de loading na carga inicial
A interface SHALL exibir placeholders visuais animados enquanto os dados do painel carregam, em vez de conteúdo vazio ou em branco.

#### Scenario: Skeleton exibido durante carregarTudo()
- **WHEN** o usuário faz login e a aplicação inicia `carregarTudo()`
- **THEN** a área de KPIs exibe blocos cinza animados com shimmer
- **AND** a área de gráfico exibe um placeholder de altura equivalente
- **AND** nenhum texto de dado real aparece antes do carregamento concluir

#### Scenario: Skeleton substituído por dados reais
- **WHEN** `carregarTudo()` conclui com sucesso
- **THEN** os skeletons são substituídos pelos componentes reais sem flash de conteúdo
