# Spec Delta

## ADDED Requirements

### Requirement: Empresa suspensa fora da escolha e do acesso
O sistema SHALL omitir empresas suspensas da lista de empresas do usuário e SHALL recusar uma empresa suspensa como
empresa ativa de uma requisição.

#### Scenario: Empresa suspensa não aparece na escolha
- **WHEN** um usuário membro de uma empresa suspensa e de uma ativa conclui o login
- **THEN** a tela de escolha lista somente a empresa ativa

#### Scenario: Usuário só com empresas suspensas
- **WHEN** todas as empresas do usuário estão suspensas
- **THEN** o sistema informa que a conta não tem acesso a nenhuma empresa e oferece sair

#### Scenario: Suspensão durante o uso
- **WHEN** a empresa ativa de uma aba é suspensa e a aba faz uma requisição
- **THEN** o sistema recusa com erro de permissão de empresa inacessível
- **AND** a tela de escolha de empresa é exibida
