## ADDED Requirements

### Requirement: Cadastro completo da empresa
O sistema SHALL armazenar e permitir editar, para a empresa ativa, tipo de inscrição (CNPJ ou CPF), número de inscrição, razão social, nome fantasia, inscrição estadual, inscrição municipal, CNAE, regime tributário, situação cadastral, data de abertura, e-mail, telefone e endereço (CEP, logradouro, número, complemento, bairro, município e UF).

#### Scenario: Salvar dados completos
- **WHEN** o administrador preenche os dados e salva
- **THEN** todos os campos informados são persistidos e exibidos ao reabrir a tela

#### Scenario: Empresa existente sem dados adicionais
- **WHEN** o administrador abre "Dados da empresa" de uma empresa que só tinha nome
- **THEN** a tela abre com os novos campos vazios e o nome atual preservado

### Requirement: Inscrição válida e única
O sistema SHALL validar o número de inscrição conforme o tipo (dígitos verificadores de CNPJ ou CPF) e SHALL impedir que duas empresas tenham a mesma inscrição.

#### Scenario: Inscrição inválida
- **WHEN** o administrador informa um CNPJ com dígito verificador incorreto
- **THEN** o sistema recusa a gravação com mensagem indicando o campo

#### Scenario: Inscrição já cadastrada
- **WHEN** o número informado já pertence a outra empresa
- **THEN** o sistema recusa a gravação sem revelar dados da outra empresa

### Requirement: Edição restrita a administradores
O sistema SHALL permitir ver e editar "Dados da empresa" somente a administradores da empresa ativa, com o tipo e o número de inscrição como primeiros campos da tela.

#### Scenario: Membro sem papel de administrador
- **WHEN** um membro comum tenta acessar a tela ou a API de atualização
- **THEN** o acesso é negado

#### Scenario: Ordem dos campos
- **WHEN** o administrador abre a tela
- **THEN** "Tipo de inscrição" e "Número de inscrição" são os primeiros campos
