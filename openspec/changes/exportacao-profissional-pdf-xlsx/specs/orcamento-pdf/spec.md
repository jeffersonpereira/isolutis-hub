## ADDED Requirements

### Requirement: Cabeçalho fiscal padronizado no PDF de orçamento
O PDF de orçamento SHALL exibir o cabeçalho com a identidade fiscal da empresa (logomarca, nome, documento, endereço e contato, quando cadastrados) no mesmo padrão visual adotado nos relatórios financeiros exportados.

#### Scenario: Cabeçalho completo quando os dados estão cadastrados
- **WHEN** a empresa emissora tem logomarca, documento, endereço e contato cadastrados
- **AND** o usuário gera o PDF de um orçamento
- **THEN** o cabeçalho exibe a logomarca, o nome da empresa, o documento formatado, o endereço e o contato

#### Scenario: Cabeçalho sem logomarca ou dados opcionais
- **WHEN** a empresa emissora não tem logomarca, documento, endereço ou contato cadastrados
- **THEN** o cabeçalho exibe apenas os dados disponíveis, sem campos vazios visíveis
