## ADDED Requirements

### Requirement: Proxy de consulta de CNPJ no backend
O sistema SHALL oferecer um endpoint autenticado que consulta a BrasilAPI e devolve um DTO próprio com os dados cadastrais do CNPJ; o navegador NÃO SHALL chamar a BrasilAPI diretamente.

#### Scenario: CNPJ válido e encontrado
- **WHEN** um usuário autenticado consulta um CNPJ válido existente
- **THEN** o endpoint devolve razão social, nome fantasia, situação, data de abertura, CNAE, e-mail, telefone e endereço

#### Scenario: CNPJ com dígito verificador inválido
- **WHEN** o CNPJ informado é inválido
- **THEN** o endpoint responde com erro de validação sem consultar o serviço externo

#### Scenario: CNPJ não encontrado
- **WHEN** a BrasilAPI informa que o CNPJ não existe
- **THEN** o endpoint responde "CNPJ não encontrado"

#### Scenario: Serviço indisponível ou limitado
- **WHEN** a BrasilAPI falha, excede o tempo ou limita as requisições
- **THEN** o endpoint responde com mensagem de indisponibilidade e a tela permite preencher manualmente

#### Scenario: Acesso sem autenticação
- **WHEN** a requisição não está autenticada
- **THEN** o endpoint nega o acesso

#### Scenario: Abuso de consultas
- **WHEN** um usuário excede o limite de consultas por período
- **THEN** o endpoint responde com limite excedido

### Requirement: Preenchimento automático ao digitar o CNPJ
O sistema SHALL, nas telas com campo de CNPJ (Dados da empresa, parceiros e clientes), consultar o proxy ao ser informado um CNPJ completo e válido e preencher os campos correspondentes, que permanecem editáveis.

#### Scenario: Preenchimento bem-sucedido
- **WHEN** o usuário digita um CNPJ válido
- **THEN** a tela exibe "Buscando…" e preenche razão social, endereço, contato e demais dados retornados

#### Scenario: Campos já preenchidos pelo usuário
- **WHEN** o usuário já havia digitado um valor em um campo que a consulta também retorna
- **THEN** o valor do usuário é preservado

#### Scenario: Falha na consulta
- **WHEN** a consulta falha
- **THEN** a tela exibe aviso discreto e o cadastro manual continua possível

#### Scenario: CPF não consulta serviço externo
- **WHEN** o tipo de inscrição é CPF
- **THEN** nenhuma consulta externa é feita

### Requirement: Inscrição como primeiros campos
O sistema SHALL apresentar "Tipo de inscrição" e "Número de inscrição" como os dois primeiros campos nas telas que possuem informação de CNPJ/CPF; os demais campos mantêm a ordem atual.

#### Scenario: Cadastro de parceiro
- **WHEN** o usuário abre o formulário de parceiro ou cliente
- **THEN** o tipo de pessoa (inscrição) e o CPF/CNPJ vêm antes de nome, contato e endereço
