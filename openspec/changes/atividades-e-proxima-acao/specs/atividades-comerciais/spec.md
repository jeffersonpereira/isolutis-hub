# Spec Delta

## Purpose

Guarda no Hub o histórico datado das interações da equipe com cada cliente e negócio (notas, ligações, reuniões e
e-mails), para que o relacionamento não dependa da memória de quem atendeu.

## ADDED Requirements

### Requirement: Registro de atividade
O sistema SHALL permitir que usuários com permissão `comercial` registrem uma atividade com tipo (`nota`, `ligacao`,
`reuniao` ou `email`), data e hora em que ocorreu, descrição obrigatória, cliente obrigatório, negócio opcional e
responsável. Sem responsável informado, o responsável é quem registrou.

#### Scenario: Atividade registrada no cliente
- **WHEN** um usuário comercial envia tipo `ligacao`, data/hora, descrição e um cliente válido
- **THEN** a atividade é criada com o usuário atual como responsável
- **AND** passa a constar na linha do tempo desse cliente

#### Scenario: Descrição vazia recusada
- **WHEN** a descrição está vazia ou só tem espaços
- **THEN** a API responde 422 e nada é gravado

#### Scenario: Tipo inválido recusado
- **WHEN** o tipo não é um de `nota`, `ligacao`, `reuniao`, `email`
- **THEN** a API responde 422

#### Scenario: Sem permissão comercial
- **WHEN** um usuário com papel `membro` ou `financeiro` tenta listar ou registrar atividades
- **THEN** a API responde 403

### Requirement: Vínculo da atividade com negócio do mesmo cliente
Uma atividade ligada a um negócio SHALL pertencer ao mesmo cliente desse negócio.

#### Scenario: Negócio de outro cliente recusado
- **WHEN** a atividade informa um negócio cujo cliente é diferente do cliente da atividade
- **THEN** a API responde 422 com mensagem explicando a divergência

#### Scenario: Negócio informado sem cliente
- **WHEN** a atividade informa apenas o negócio
- **THEN** o cliente da atividade é o cliente desse negócio

### Requirement: Data da atividade não pode estar no futuro
A data e hora da atividade SHALL ser igual ou anterior ao momento do registro, porque a atividade descreve algo que já
aconteceu; o que ainda vai acontecer é a próxima ação do negócio.

#### Scenario: Atividade futura recusada
- **WHEN** a data/hora informada é posterior ao momento atual (com tolerância de 5 minutos)
- **THEN** a API responde 422 sugerindo registrar como próxima ação

### Requirement: Linha do tempo do cliente
O sistema SHALL exibir no cliente todas as atividades dele, da mais recente para a mais antiga, mostrando tipo, data,
responsável, descrição e o negócio vinculado quando houver.

#### Scenario: Ordem cronológica inversa
- **WHEN** o usuário abre um cliente com três atividades em datas diferentes
- **THEN** a mais recente aparece primeiro

#### Scenario: Cliente sem atividades
- **WHEN** o cliente não tem atividades
- **THEN** a linha do tempo mostra um estado vazio com o botão para registrar a primeira

#### Scenario: Paginação
- **WHEN** o cliente tem mais de 50 atividades
- **THEN** a linha do tempo carrega as 50 mais recentes e oferece carregar as anteriores

### Requirement: Linha do tempo do negócio
O sistema SHALL exibir no negócio apenas as atividades vinculadas a ele, na mesma ordem e formato da linha do tempo do
cliente, e permitir registrar uma atividade já vinculada ao negócio.

#### Scenario: Só atividades do negócio
- **WHEN** o cliente tem atividades com e sem vínculo a um negócio
- **THEN** o negócio mostra somente as vinculadas a ele

### Requirement: Edição e exclusão de atividade
Somente o autor da atividade ou um administrador SHALL poder editá-la ou excluí-la; a edição usa o controle de versão já
adotado nos demais registros.

#### Scenario: Autor edita
- **WHEN** o autor altera a descrição enviando a versão atual
- **THEN** a alteração é gravada

#### Scenario: Outro usuário comercial tenta excluir
- **WHEN** um usuário comercial que não é o autor nem administrador tenta excluir a atividade
- **THEN** a API responde 403

#### Scenario: Edição concorrente
- **WHEN** a versão enviada difere da gravada
- **THEN** a API recusa com o aviso de conflito padrão

### Requirement: Isolamento por empresa
Atividades SHALL ser visíveis e alteráveis apenas dentro da empresa da sessão.

#### Scenario: Atividade de outra empresa
- **WHEN** um usuário consulta ou altera uma atividade criada em outra empresa
- **THEN** a API responde 404
