## ADDED Requirements

### Requirement: Conta do plano filtrada pela natureza do título
O sistema SHALL listar, no campo "Conta do plano de contas" do lançamento de título, somente contas analíticas cuja natureza corresponda ao tipo do título: despesa para título a pagar e receita para título a receber.

#### Scenario: Título a pagar lista despesas
- **WHEN** o usuário seleciona o tipo "A pagar" no lançamento de título
- **THEN** o campo lista apenas contas analíticas de natureza despesa

#### Scenario: Título a receber lista receitas
- **WHEN** o usuário seleciona o tipo "A receber"
- **THEN** o campo lista apenas contas analíticas de natureza receita

#### Scenario: Troca de tipo recarrega as opções
- **WHEN** o usuário altera o tipo do título
- **THEN** as opções são recalculadas e a conta anteriormente escolhida, se incompatível, é limpa

#### Scenario: Contas filhas herdam a natureza da raiz
- **WHEN** uma conta analítica descende de uma raiz de natureza despesa
- **THEN** ela é listada para título a pagar e não para título a receber

### Requirement: Estados do carregamento do plano de contas
O sistema SHALL distinguir, no lançamento de título, os estados carregando, vazio e erro ao obter o plano de contas.

#### Scenario: Plano sem conta compatível
- **WHEN** não existe conta analítica da natureza exigida
- **THEN** o campo exibe uma orientação para cadastrar uma conta antes

#### Scenario: Falha ao carregar
- **WHEN** a consulta do plano de contas falha
- **THEN** a tela exibe a mensagem de erro e permite tentar novamente, sem apresentar o campo como vazio
