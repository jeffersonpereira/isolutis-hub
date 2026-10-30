# Spec Delta

## ADDED Requirements

### Requirement: Operador da plataforma como identidade distinta
O sistema SHALL reconhecer o operador da plataforma por registro próprio, independente dos papéis de empresa. Somente
operadores SHALL acessar a área da plataforma. Ser `admin` de uma empresa NÃO SHALL conceder acesso à área.

#### Scenario: Operador acessa a área
- **WHEN** um operador autenticado abre a área da plataforma
- **THEN** o sistema lista as empresas

#### Scenario: Usuário comum não acessa
- **WHEN** um usuário que não é operador chama uma rota da plataforma, inclusive `admin` de empresa
- **THEN** o sistema recusa com erro de permissão
- **AND** a aplicação não exibe a opção da área da plataforma para ele

#### Scenario: Primeiro operador pelo script
- **WHEN** o operador executa o script de provisionamento com a opção de operador para um e-mail
- **THEN** esse usuário passa a ser operador da plataforma

### Requirement: Operador não acessa dados de negócio
O sistema SHALL impedir, no banco, que as rotas da plataforma leiam dados de negócio de qualquer empresa (financeiro,
clientes, negócios, orçamentos, projetos, tarefas). O operador SHALL ver apenas metadados da empresa e seus membros.

#### Scenario: Rota da plataforma não alcança dados de negócio
- **WHEN** a conexão usada pelas rotas da plataforma tenta ler uma tabela de dados de negócio
- **THEN** o banco recusa por falta de privilégio

#### Scenario: Detalhe da empresa só traz metadados
- **WHEN** o operador abre o detalhe de uma empresa
- **THEN** vê nome, CNPJ, status, membros com papel e convites pendentes
- **AND** não vê nenhum registro de negócio da empresa

### Requirement: Listagem de empresas
O sistema SHALL listar para o operador todas as empresas com nome, inscrição (CNPJ), status e quantidade de membros
ativos, com busca por nome ou CNPJ.

#### Scenario: Lista com contagem
- **WHEN** o operador abre a lista de empresas
- **THEN** cada empresa mostra nome, CNPJ, status e o número de membros ativos

#### Scenario: Busca
- **WHEN** o operador busca por parte do nome ou pelo CNPJ
- **THEN** a lista mostra somente as empresas correspondentes

### Requirement: Criação de empresa com administrador inicial por convite
O sistema SHALL permitir ao operador criar uma empresa informando o nome e o e-mail e o nome do administrador inicial.
A criação SHALL emitir convite com papel `admin` para esse e-mail e enviá-lo por e-mail, sem definir senha pelo
operador.

#### Scenario: Empresa criada com convite
- **WHEN** o operador informa nome da empresa, nome e e-mail do administrador e confirma
- **THEN** a empresa é criada com status `ativa`
- **AND** um convite com papel `admin` é emitido e enviado ao e-mail informado
- **AND** a ação é registrada na auditoria

#### Scenario: Administrador aceita e inicia o onboarding
- **WHEN** o administrador aceita o convite
- **THEN** é vinculado à empresa com papel `admin`
- **AND** ao entrar na empresa vê o assistente de configuração inicial

#### Scenario: Administrador já tem conta
- **WHEN** o e-mail informado já pertence a um usuário existente
- **THEN** o aceite apenas vincula a conta à nova empresa, sem alterar a senha

#### Scenario: Dados inválidos
- **WHEN** o nome está vazio ou o e-mail é inválido
- **THEN** o sistema recusa com erro de validação
- **AND** nenhuma empresa é criada

### Requirement: Suspender e reativar empresa
O sistema SHALL permitir ao operador suspender e reativar uma empresa sem apagar dados. Empresa suspensa SHALL recusar
requisições de seus membros.

#### Scenario: Suspender
- **WHEN** o operador suspende uma empresa
- **THEN** o status passa a `suspensa`
- **AND** a próxima requisição de qualquer membro nessa empresa é recusada
- **AND** nenhum dado da empresa é removido

#### Scenario: Reativar
- **WHEN** o operador reativa uma empresa suspensa
- **THEN** os membros voltam a escolher e usar a empresa normalmente

### Requirement: Gestão de membros por empresa
O sistema SHALL permitir ao operador, para qualquer empresa, ver membros e convites pendentes, convidar novos membros
com um dos papéis `admin`, `financeiro`, `comercial` ou `membro`, trocar o papel de um membro, desativar e reativar
um membro e reenviar um convite. O operador SHALL NOT definir ou ver senhas.

#### Scenario: Ver membros
- **WHEN** o operador abre uma empresa
- **THEN** vê cada membro com nome, e-mail, papel e estado, e os convites pendentes

#### Scenario: Convidar membro
- **WHEN** o operador convida um e-mail com um papel válido
- **THEN** um convite é emitido e enviado, e o convite pendente anterior do mesmo e-mail é invalidado

#### Scenario: Trocar papel
- **WHEN** o operador altera o papel de um membro
- **THEN** o novo papel vale na requisição seguinte desse membro

#### Scenario: Desativar membro
- **WHEN** o operador desativa um membro
- **THEN** ele perde o acesso à empresa na requisição seguinte

### Requirement: Empresa nunca fica sem administrador
O sistema SHALL recusar rebaixar ou desativar o último `admin` ativo de uma empresa.

#### Scenario: Último administrador
- **WHEN** o operador tenta rebaixar ou desativar o único `admin` ativo de uma empresa
- **THEN** o sistema recusa com mensagem explicativa
- **AND** o papel e o estado do membro permanecem inalterados

### Requirement: Auditoria das ações do operador
O sistema SHALL registrar, de forma que não possa ser alterada pela aplicação, toda ação do operador: quem, quando,
empresa, ação e os valores antes e depois.

#### Scenario: Ação registrada
- **WHEN** o operador cria empresa, muda status, convida, troca papel ou desativa membro
- **THEN** um registro de auditoria com operador, empresa, ação, antes e depois é gravado na mesma transação

#### Scenario: Registro não é alterável
- **WHEN** a conexão da aplicação tenta alterar ou apagar um registro de auditoria da plataforma
- **THEN** o banco recusa
