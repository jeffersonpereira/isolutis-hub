## ADDED Requirements

### Requirement: Nomes de módulos alinhados ao vocabulário do usuário
O menu lateral SHALL exibir nomes de módulos que correspondam ao vocabulário natural do usuário de negócio, não ao nome interno do modelo de dados.

#### Scenario: Módulo de clientes exibe "Clientes"
- **WHEN** o menu lateral é renderizado
- **THEN** o item que navega para `id="clientes"` exibe o texto "Clientes"
- **AND** não exibe "Parceiro de Negócios"

#### Scenario: Módulo de negócios exibe "Funil de Vendas"
- **WHEN** o menu lateral é renderizado
- **THEN** o item que navega para `id="negocios"` exibe o texto "Funil de Vendas"
- **AND** não exibe "Negócios e Funil"

#### Scenario: Módulo financeiro de parceiros exibe "Fornecedores"
- **WHEN** o menu do grupo Financeiro é renderizado
- **THEN** o item que navega para `id="fin-parceiros"` exibe o texto "Fornecedores"
- **AND** não exibe "Parceiro de Negócio"

#### Scenario: IDs internos dos módulos não mudam
- **WHEN** a renomeação é aplicada
- **THEN** os campos `id` em todos os `registrarVista` permanecem inalterados
- **AND** a navegação por URL e o estado salvo em `localStorage` continuam funcionando
