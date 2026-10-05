## ADDED Requirements

### Requirement: Operações pertencem a uma empresa
Toda operação de negócio e todo cadastro editável SHALL pertencer a exatamente uma empresa. O sistema SHALL armazenar a propriedade como `empresa_id` e SHALL usar `empresa` como nome da entidade persistida. Dados sem proprietário, empresa inexistente e proprietário implícito SHALL ser recusados.

#### Scenario: Criar registro operacional
- **WHEN** um usuário autenticado cria um registro operacional no contexto de uma empresa autorizada
- **THEN** o servidor grava o `empresa_id` do contexto autenticado no registro
- **AND** o servidor ignora ou rejeita qualquer `empresa_id` fornecido no corpo que não corresponda ao contexto

#### Scenario: Contexto de empresa ausente
- **WHEN** uma operação tenant-scoped chega sem empresa ativa válida
- **THEN** o servidor recusa a operação antes de ler ou alterar dados tenant-scoped

### Requirement: Usuários acessam empresas por associação
O sistema SHALL manter a identidade de login global em `usuarios` e SHALL conceder acesso por associação ativa em `usuario_empresa`. Cada associação SHALL conter um papel de empresa, no mínimo `admin` ou `membro`. Usuários SHALL poder pertencer a mais de uma empresa; privilégios administrativos SHALL ser avaliados no contexto da empresa ativa.

#### Scenario: Listar empresas disponíveis
- **WHEN** um usuário autenticado solicita suas empresas
- **THEN** o servidor retorna somente empresas com associação ativa daquele usuário

#### Scenario: Selecionar empresa sem associação
- **WHEN** o usuário seleciona uma empresa para a qual não tem associação ativa
- **THEN** o servidor recusa o acesso e não retorna dados da empresa

#### Scenario: Administrar membros
- **WHEN** um administrador da empresa gerencia membros daquela empresa
- **THEN** o servidor permite a operação somente para essa associação e não altera papéis ou vínculos de outras empresas

### Requirement: Seleção explícita e autorização do tenant
Toda requisição autenticada que acesse dados tenant-scoped SHALL identificar a empresa ativa por `X-Empresa-ID`. O backend SHALL validar a associação ativa do usuário antes da operação, definir o contexto de tenant na transação e SHALL falhar fechado se a seleção ou autorização não for válida. WebSocket SHALL validar a mesma associação e contexto.

#### Scenario: Requisição autorizada para a empresa ativa
- **WHEN** a requisição contém `X-Empresa-ID` de uma associação ativa do usuário
- **THEN** as leituras e gravações ficam limitadas à empresa indicada

#### Scenario: Trocar empresa ativa
- **WHEN** o usuário faz requisições consecutivas para duas empresas às quais pertence
- **THEN** cada requisição usa exclusivamente o tenant explicitamente selecionado naquela requisição
- **AND** o contexto não vaza entre transações ou conexões reutilizadas pelo pool

#### Scenario: Acesso não autorizado
- **WHEN** o usuário omite a empresa, fornece um ID inválido ou não tem membership ativo
- **THEN** o backend retorna erro de autorização sem revelar existência ou conteúdo dos dados

### Requirement: Isolamento de leitura e escrita
As consultas e gravações de APIs, relatórios, exportações, documentos, buscas, agregações, scripts operacionais e eventos em tempo real SHALL ser restritos à empresa ativa. Nenhum resultado SHALL combinar linhas de empresas diferentes.

#### Scenario: Leitura por tenant
- **WHEN** duas empresas possuem registros do mesmo tipo
- **THEN** cada usuário vê apenas registros da empresa ativa para a qual tem associação

#### Scenario: Escrita por tenant
- **WHEN** um usuário cria, atualiza ou remove uma operação
- **THEN** a operação só afeta registros pertencentes à empresa ativa autorizada

#### Scenario: Relatório ou agregação
- **WHEN** uma consulta calcula totais, painéis, fluxo financeiro ou exportação
- **THEN** todos os filtros e joins limitam o cálculo à empresa ativa

### Requirement: Relações entre registros respeitam a empresa
Toda relação entre registros tenant-scoped SHALL ser validada no PostgreSQL para que ambos pertençam à mesma empresa. Tabelas que participam de relações SHALL usar chaves únicas e estrangeiras compostas por identificador e `empresa_id`, conforme necessário. Relações de tabelas filhas SHALL preservar a empresa do pai.

#### Scenario: Criar relação da mesma empresa
- **WHEN** um registro é associado a outro registro da mesma empresa
- **THEN** a chave estrangeira composta permite a relação se as demais regras forem válidas

#### Scenario: Criar relação cruzada
- **WHEN** uma escrita direta ou da aplicação tenta associar registros de empresas diferentes
- **THEN** o banco rejeita a escrita por constraint, mesmo se a validação do serviço for contornada

### Requirement: Row-Level Security reforça o isolamento
Tabelas tenant-scoped SHALL ter RLS habilitada e forçada, com políticas de leitura e escrita usando o contexto transacional `app.empresa_id`. O papel de runtime SHALL ser distinto do papel de migração e SHALL não ser proprietário das tabelas nem possuir `BYPASSRLS`. Contexto ausente SHALL resultar em nenhuma linha acessível.

#### Scenario: Consultar sem contexto RLS
- **WHEN** uma conexão executa consulta tenant-scoped sem `app.empresa_id`
- **THEN** nenhuma linha tenant-scoped fica visível

#### Scenario: Tentativa de escrita em outro tenant
- **WHEN** o runtime tenta inserir ou atualizar uma linha com empresa diferente do contexto ativo
- **THEN** a política RLS rejeita a operação

#### Scenario: Execução de migração
- **WHEN** uma migração precisa alterar dados ou schema tenant-scoped
- **THEN** ela usa credencial de migração separada da credencial de runtime

### Requirement: Cadastros globais são explicitamente limitados
Somente identidades globais e catálogos de referência compartilhados SHALL ser acessíveis sem escopo de empresa. `usuarios`, `municipio`, `instituicao_financeira` e códigos estáveis de papéis SHALL ser globais; cadastros operacionais, incluindo produtos, parceiros, categorias, investidores e atribuições de papéis a parceiros, SHALL ser isolados por empresa.

#### Scenario: Ler catálogo de referência
- **WHEN** uma operação autorizada consulta municípios ou instituições financeiras
- **THEN** o catálogo compartilhado pode ser reutilizado sem duplicação por empresa

#### Scenario: Criar cadastro editável
- **WHEN** uma empresa cria produto, categoria, investidor ou papel de parceiro
- **THEN** o cadastro e suas atribuições pertencem somente àquela empresa

### Requirement: Chaves únicas respeitam a empresa
Restrições de unicidade para dados operacionais SHALL incluir `empresa_id`, exceto quando a unicidade global for uma regra explícita de identidade ou referência. Numeração de orçamento SHALL ser única por empresa, e a sequência SHALL ser particionada por empresa e ano.

#### Scenario: Mesmo valor único em empresas distintas
- **WHEN** duas empresas cadastram registros com o mesmo nome, código, documento ou número de negócio
- **THEN** ambos são aceitos quando a regra de unicidade é tenant-local

#### Scenario: Orçamento simultâneo
- **WHEN** empresas distintas emitem orçamento no mesmo ano, inclusive simultaneamente
- **THEN** cada empresa recebe sequência independente sem colisão ou compartilhamento de contador

#### Scenario: Rollback de emissão de orçamento
- **WHEN** a transação que alocou o próximo número de orçamento faz rollback
- **THEN** a sequência transacional daquela empresa e ano pode reutilizar o número
- **AND** uma emissão simultânea de outra empresa ou ano não bloqueia nessa mesma linha de sequência

### Requirement: Consultas por período permitem range scan
Consultas operacionais filtradas por ano, mês ou período SHALL expressar o filtro como intervalo semiaberto sobre a coluna de data (`>= início` e `< próximo_início`) em vez de aplicar funções como `extract` à coluna filtrada. Agregações SHALL agrupar os resultados filtrados depois de reduzir o intervalo.

#### Scenario: Listar dados por ano e mês
- **WHEN** uma consulta lista receitas, despesas ou títulos para um período
- **THEN** a cláusula de filtro usa limites semiabertos diretamente na coluna de data
- **AND** o tenant ativo é aplicado como predicado junto com o intervalo

### Requirement: Índices tenant seguem consultas e relações reais
Índices para tabelas tenant-scoped SHALL alinhar as colunas de igualdade do tenant e filtros com os padrões observados de ordenação e relacionamento. Migrações SHALL revisar/substituir índices existentes e índices do lado filho das FKs compostas, evitando duplicatas sem benefício demonstrado. Particionamento, covering indexes e índices caros SHALL depender de planos e medições representativas, sem pressupor ganho apenas por tipo de plano.

#### Scenario: Listagem tenant por data ou ordem
- **WHEN** os índices são desenhados para uma listagem tenant-scoped frequente
- **THEN** a chave considera `empresa_id`, os filtros da consulta e a ordenação real com desempate estável

#### Scenario: Avaliar índice candidato
- **WHEN** uma migration propõe índice adicional, GIN composto, `INCLUDE` ou particionamento
- **THEN** a decisão compara planos com `EXPLAIN (ANALYZE, BUFFERS)` e mede custo de leitura, escrita e espaço em dados representativos

### Requirement: Parceiros recebem múltiplas tags personalizadas
Cada empresa SHALL poder criar tags próprias para classificar parceiros. Tags SHALL ser distintas dos papéis de parceiro (`cliente`, `fornecedor`, `funcionario`): papéis continuam controlando regras de domínio, enquanto tags são classificações organizacionais livres. Um parceiro SHALL poder ter zero ou várias tags, todas pertencentes à mesma empresa.

#### Scenario: Criar tag para uma empresa
- **WHEN** um administrador cria uma tag com nome não vazio
- **THEN** a tag fica associada à empresa ativa e pode ser atribuída aos parceiros dessa empresa
- **AND** outra empresa pode criar tag de mesmo nome sem colisão

#### Scenario: Recusar tag duplicada normalizada
- **WHEN** a empresa tenta criar tag cujo nome já existe após trim e comparação sem diferenciar maiúsculas/minúsculas
- **THEN** o sistema recusa a duplicata

#### Scenario: Atribuir várias tags
- **WHEN** um usuário autorizado cria ou atualiza um parceiro com vários IDs de tag ativos da empresa atual
- **THEN** todas as associações são gravadas atomicamente
- **AND** nenhuma tag é tratada como papel de domínio

#### Scenario: Recusar associação cross-tenant
- **WHEN** uma operação tenta associar parceiro e tag pertencentes a empresas diferentes
- **THEN** validação de serviço e chave estrangeira composta recusam a associação

### Requirement: Parceiros podem ser filtrados por tags
A listagem de parceiros SHALL aceitar várias tags como filtro. A semântica padrão SHALL ser OR entre tags selecionadas e AND entre a dimensão de tags, o filtro de papel e o texto de busca. A listagem SHALL retornar cada parceiro no máximo uma vez. Com nenhuma tag selecionada, as tags não restringem o resultado.

#### Scenario: Filtro por qualquer tag selecionada
- **WHEN** a listagem recebe duas ou mais tags da empresa ativa
- **THEN** retorna parceiros associados a pelo menos uma dessas tags
- **AND** combina esse resultado com papel e busca textual por interseção

#### Scenario: Sem filtro de tags
- **WHEN** a listagem não recebe IDs de tag
- **THEN** a dimensão de tags não exclui parceiros

#### Scenario: Tag de outro tenant ou inexistente no filtro
- **WHEN** a listagem recebe ID de tag fora da empresa ativa ou inexistente
- **THEN** o sistema recusa o filtro ou o ignora sem expor dados de outro tenant

### Requirement: Tags usadas são arquivadas
Uma tag SHALL poder ser desativada para impedir novas atribuições, preservando associações existentes. Tags desativadas SHALL permanecer visíveis nos parceiros já classificados e não SHALL aparecer como opção para novas atribuições ou filtros padrão. A exclusão física SHALL ser recusada enquanto houver associações.

#### Scenario: Arquivar tag em uso
- **WHEN** um administrador desativa uma tag que já classifica parceiros
- **THEN** as associações permanecem e a tag aparece como arquivada nos detalhes existentes
- **AND** a tag não pode ser atribuída a novos parceiros nem selecionada no filtro padrão

#### Scenario: Excluir tag não utilizada
- **WHEN** um administrador solicita exclusão física de tag sem associações
- **THEN** o sistema pode removê-la

#### Scenario: Excluir tag utilizada
- **WHEN** um administrador solicita exclusão física de tag que ainda possui associações
- **THEN** o sistema recusa a exclusão sem remover associações implicitamente

### Requirement: Tags legadas não são inferidas
A migração SHALL criar o catálogo tenant-scoped de tags e sua tabela de associação vazios. Ela SHALL preservar os parceiros existentes sem tags, sem converter papéis, segmentos ou texto livre em tags automaticamente.

#### Scenario: Migrar parceiros existentes
- **WHEN** a migração de tags é aplicada aos parceiros existentes
- **THEN** os parceiros ficam sem tags até classificação explícita por usuário ou importação autorizada

### Requirement: Migração preserva e atribui propriedade legada
A migração multi-tenant SHALL preservar os IDs, relações, histórico e valores existentes. Todo dado operacional pré-existente SHALL ser atribuído à empresa iSolutis existente; nenhum dado SHALL ser dividido por cliente ou descartado. Antes do cutover, o sistema SHALL validar ausência de órfãos, relações cruzadas e conflitos de unicidade.

#### Scenario: Backfill da empresa existente
- **WHEN** as tabelas legadas recebem `empresa_id`
- **THEN** todas as linhas existentes apontam para a empresa iSolutis e mantêm as relações originais

#### Scenario: Falha de validação de migração
- **WHEN** o backfill encontra órfãos ou colisões incompatíveis
- **THEN** a migração não habilita o cutover multi-tenant e informa as linhas conflitantes para resolução

#### Scenario: Tenantização concluída
- **WHEN** backfill e validações terminam com sucesso
- **THEN** `empresa_id` torna-se obrigatório, as FKs compostas e unicidades são instaladas e as políticas RLS são habilitadas
