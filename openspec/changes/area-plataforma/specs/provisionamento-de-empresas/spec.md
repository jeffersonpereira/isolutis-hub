# Spec Delta

## MODIFIED Requirements

### Requirement: Empresas são criadas somente pelo operador da plataforma
O sistema SHALL permitir a criação de empresas apenas pelo operador da plataforma, pela área da plataforma ou por
procedimento administrativo fora da aplicação. Nenhum outro usuário da aplicação, inclusive `admin` de empresa, SHALL
poder criar empresas.

#### Scenario: Usuário autenticado tenta criar empresa pela API
- **WHEN** um usuário autenticado que não é operador envia uma requisição de criação de empresa à API
- **THEN** a operação não está disponível
- **AND** nenhuma empresa é criada

#### Scenario: Administrador de empresa não cria outra empresa
- **WHEN** um `admin` de uma empresa procura a opção de criar nova empresa na aplicação
- **THEN** a aplicação não oferece essa opção

#### Scenario: Banco recusa a criação pelo papel da aplicação
- **WHEN** a conexão usada pelas rotas de empresa da aplicação tenta executar a função de criação de empresa
  diretamente no banco
- **THEN** o banco recusa por falta de privilégio

### Requirement: Operador cria empresa e administrador inicial
O sistema SHALL manter um procedimento do operador que cria a empresa e o administrador inicial com o papel `admin`, sem
depender de flag global no usuário. Pela área da plataforma, o administrador inicial SHALL ser vinculado por convite; o
script de terminal SHALL continuar disponível para o primeiro operador e para recuperação.

#### Scenario: Operador cria empresa com administrador pelo script
- **WHEN** o operador executa o procedimento informando e-mail, nome e nome da empresa
- **THEN** a empresa é criada
- **AND** o usuário é vinculado a ela com o papel `admin`

#### Scenario: Operador cria empresa pela área da plataforma
- **WHEN** o operador cria a empresa pela área da plataforma informando o e-mail do administrador
- **THEN** a empresa é criada e o administrador recebe um convite com papel `admin`

#### Scenario: Administrador inicial segue o onboarding
- **WHEN** o administrador inicial entra numa empresa recém-criada
- **THEN** o assistente de configuração inicial é exibido
