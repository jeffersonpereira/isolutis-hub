## ADDED Requirements

### Requirement: Papéis por empresa
O sistema SHALL atribuir a cada usuário, em cada empresa, exatamente um dos papéis `admin`, `financeiro`, `comercial` ou `membro`. O papel SHALL valer somente na empresa em que foi atribuído.

#### Scenario: Papéis diferentes em empresas diferentes
- **WHEN** um usuário é `admin` na empresa A e `membro` na empresa B
- **THEN** na empresa A ele tem as permissões de administrador
- **AND** na empresa B ele tem somente as permissões básicas

#### Scenario: Valor de papel inválido
- **WHEN** é solicitado um papel diferente de `admin`, `financeiro`, `comercial` ou `membro` ao criar ou atualizar um usuário
- **THEN** o sistema recusa a operação com erro de validação
- **AND** o papel do usuário permanece inalterado

---

### Requirement: Matriz de permissões por papel
O sistema SHALL derivar as permissões de um usuário exclusivamente do seu papel na empresa ativa, conforme a matriz: `admin` tem `base`, `comercial`, `financeiro` e `administracao`; `financeiro` tem `base` e `financeiro`; `comercial` tem `base` e `comercial`; `membro` tem somente `base`.

#### Scenario: Permissões do administrador
- **WHEN** um `admin` acessa qualquer área da empresa ativa
- **THEN** o acesso é permitido

#### Scenario: Permissões do financeiro
- **WHEN** um usuário `financeiro` acessa o módulo financeiro, o faturamento, as despesas ou os relatórios
- **THEN** o acesso é permitido
- **AND** o acesso a clientes completos, negócios, orçamentos, produtos, usuários e dados da empresa é recusado

#### Scenario: Permissões do comercial
- **WHEN** um usuário `comercial` acessa clientes, negócios, orçamentos ou produtos
- **THEN** o acesso é permitido
- **AND** o acesso ao módulo financeiro, faturamento, despesas, relatórios, usuários e dados da empresa é recusado

#### Scenario: Permissões do membro
- **WHEN** um usuário `membro` acessa painel, tarefas ou projetos
- **THEN** o acesso é permitido
- **AND** o acesso a áreas comerciais, financeiras e administrativas é recusado

---

### Requirement: Permissões impostas no backend
O sistema SHALL verificar a permissão exigida em toda rota de dados da empresa, no servidor, a cada requisição, recusando com erro de permissão (HTTP 403) quando o papel do usuário na empresa ativa não a possui. A ocultação de menus no front SHALL NOT ser a única proteção.

#### Scenario: Chamada direta à API sem permissão
- **WHEN** um usuário `membro` chama diretamente `GET /negocios` ou `GET /financeiro/titulos`
- **THEN** o sistema responde 403
- **AND** nenhum dado é devolvido

#### Scenario: Mudança de papel vale imediatamente
- **WHEN** o papel de um usuário é rebaixado enquanto ele está com a aplicação aberta
- **THEN** a próxima requisição dele a uma área sem permissão é recusada

#### Scenario: Nenhuma rota fica sem checagem
- **WHEN** a suíte de testes percorre todas as rotas da API
- **THEN** cada rota exige uma permissão ou consta na lista explícita de rotas públicas
- **AND** o teste falha se uma rota nova não declarar permissão

---

### Requirement: Lista de permissões entregue ao cliente
O sistema SHALL informar ao cliente, para cada empresa acessível, o papel do usuário e a lista de permissões dele, e o cliente SHALL decidir menus e carga de dados somente por essa lista.

#### Scenario: Listagem de empresas traz papel e permissões
- **WHEN** o cliente consulta as empresas do usuário
- **THEN** cada empresa vem com o papel do usuário e a lista de permissões correspondente

#### Scenario: Menu reflete as permissões
- **WHEN** um usuário `comercial` abre a aplicação
- **THEN** o menu exibe Clientes, Negócios, Orçamentos, Produtos, Projetos e Tarefas
- **AND** não exibe o grupo Financeiro, Faturamento, Despesas, Relatórios, Equipe nem Dados da empresa

#### Scenario: Carga inicial só do que é permitido
- **WHEN** um usuário `membro` abre a aplicação
- **THEN** o front carrega apenas os dados que a permissão `base` autoriza
- **AND** nenhuma requisição a recursos sem permissão é disparada
- **AND** a aplicação abre normalmente, sem erro

#### Scenario: Paleta de comandos e menu "+ Novo" respeitam o papel
- **WHEN** um usuário `membro` abre a paleta de comandos ou o menu "+ Novo"
- **THEN** são listadas apenas telas e ações que o papel permite
- **AND** nenhuma tela ou ação comercial, financeira ou administrativa aparece

#### Scenario: URL direta de tela sem permissão
- **WHEN** um usuário abre pela barra de endereço a URL de uma tela que o papel dele não permite
- **THEN** o painel é exibido e o endereço é corrigido para o do painel

#### Scenario: Minha conta e consulta de CNPJ para qualquer papel
- **WHEN** um usuário de qualquer papel abre "Minha conta" ou consulta um CNPJ
- **THEN** o acesso é permitido pela permissão `base`

#### Scenario: Dados da empresa exigem administração
- **WHEN** um usuário que não é `admin` tenta ler ou atualizar os dados cadastrais da empresa
- **THEN** o sistema responde 403

#### Scenario: Falha isolada não impede a abertura
- **WHEN** uma das requisições de carga inicial falha
- **THEN** a aplicação abre com os demais dados carregados

---

### Requirement: Painel limitado às permissões do papel
O sistema SHALL devolver no painel somente os blocos de informação que o papel do usuário pode ver, e o front SHALL omitir os blocos ausentes.

#### Scenario: Membro vê o painel sem agregados comerciais ou financeiros
- **WHEN** um usuário `membro` abre o painel
- **THEN** a resposta não contém blocos de funil, orçamentos, faturamento nem despesas
- **AND** a tela exibe apenas os blocos permitidos

#### Scenario: Administrador vê o painel completo
- **WHEN** um `admin` abre o painel
- **THEN** todos os blocos são exibidos

---

### Requirement: Lista mínima de clientes para identificar registros
O sistema SHALL oferecer a qualquer papel uma lista contendo somente identificador e nome dos clientes, para que telas básicas mostrem o nome do cliente, sem expor os demais dados do cadastro.

#### Scenario: Membro vê o nome do cliente num projeto
- **WHEN** um usuário `membro` abre um projeto vinculado a um cliente
- **THEN** o nome do cliente é exibido

#### Scenario: Lista mínima não traz dados de contato
- **WHEN** um usuário sem permissão `comercial` consulta a lista mínima de clientes
- **THEN** cada item contém somente `id` e `nome`

#### Scenario: Cadastro completo exige permissão comercial
- **WHEN** um usuário sem permissão `comercial` consulta a lista completa de clientes
- **THEN** o sistema responde 403

---

### Requirement: Atribuição e proteção do papel de administrador
O sistema SHALL permitir que apenas um `admin` atribua ou altere papéis na empresa, SHALL impedir que o usuário altere o próprio papel ou desative a si mesmo, e SHALL garantir que a empresa mantenha pelo menos um `admin` ativo.

#### Scenario: Admin atribui papel
- **WHEN** um `admin` define o papel `financeiro` para um usuário da empresa
- **THEN** o usuário passa a ter o papel `financeiro` nessa empresa

#### Scenario: Usuário sem permissão administrativa tenta atribuir papel
- **WHEN** um usuário que não é `admin` tenta alterar o papel de alguém
- **THEN** o sistema responde 403
- **AND** nenhum papel é alterado

#### Scenario: Admin não rebaixa a si mesmo
- **WHEN** um `admin` tenta mudar o próprio papel ou se desativar
- **THEN** o sistema recusa com a mensagem de que não é possível retirar o próprio acesso de administrador

#### Scenario: Última administração preservada
- **WHEN** uma operação deixaria a empresa sem nenhum `admin` ativo
- **THEN** o sistema recusa a operação com a mensagem "Precisa existir pelo menos um administrador ativo."

---

### Requirement: Migração dos papéis existentes
O sistema SHALL, ao migrar para os quatro papéis, converter as memberships e os convites pendentes com papel `membro` em `comercial` e preservar os `admin`, de modo que nenhum usuário perca o acesso comercial que já tinha.

#### Scenario: Membro atual vira comercial
- **WHEN** a migração é executada sobre uma empresa com usuários `membro`
- **THEN** esses usuários passam a ter o papel `comercial`
- **AND** continuam acessando clientes, negócios, orçamentos e produtos

#### Scenario: Administradores preservados
- **WHEN** a migração é executada
- **THEN** todos os usuários `admin` continuam `admin`

#### Scenario: Convites pendentes convertidos
- **WHEN** existem convites pendentes com papel `membro` na migração
- **THEN** eles passam a ter o papel `comercial`
