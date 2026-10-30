# Spec Delta

## Purpose

Garante que todo negócio aberto no funil tenha um próximo passo combinado, com data, para que nenhuma oportunidade
esfrie por esquecimento.

## ADDED Requirements

### Requirement: Próxima ação obrigatória em negócio aberto
Ao criar, editar ou mover um negócio para uma etapa aberta (lead até negociação), o sistema SHALL exigir a próxima ação:
descrição (até 200 caracteres) e data. Datas no passado são aceitas, para registrar ações já atrasadas.

#### Scenario: Criar negócio sem próxima ação
- **WHEN** um negócio é criado na etapa `lead` sem descrição ou sem data da próxima ação
- **THEN** a API responde 422 com "Informe a próxima ação e a data."

#### Scenario: Criar negócio com próxima ação
- **WHEN** um negócio é criado na etapa `proposta` com próxima ação "Enviar proposta revisada" para daqui a 3 dias
- **THEN** o negócio é gravado com essa próxima ação

#### Scenario: Mover para etapa aberta sem próxima ação gravada
- **WHEN** um negócio sem próxima ação gravada é arrastado para outra etapa aberta sem informar a ação
- **THEN** a API responde 422 e o funil pede a próxima ação antes de concluir o movimento

#### Scenario: Mover mantendo a ação existente
- **WHEN** um negócio que já tem próxima ação é movido para outra etapa aberta sem informar uma nova
- **THEN** a ação existente é mantida e o movimento é aceito

### Requirement: Negócio fechado não tem próxima ação
Quando um negócio passa para `ganho` ou `perdido`, o sistema SHALL limpar a próxima ação; ao reabri-lo, a próxima ação
volta a ser exigida.

#### Scenario: Ganhar o negócio
- **WHEN** um negócio com próxima ação é movido para `ganho`
- **THEN** a próxima ação e a data ficam vazias

#### Scenario: Reabrir negócio perdido
- **WHEN** um negócio `perdido` é movido de volta para `negociacao` sem próxima ação
- **THEN** a API responde 422 pedindo a próxima ação

### Requirement: Negócios existentes sem próxima ação
Negócios abertos cadastrados antes desta mudança SHALL continuar válidos sem próxima ação até a próxima gravação, quando
a regra passa a valer.

#### Scenario: Listagem de negócios antigos
- **WHEN** o funil é carregado com negócios abertos antigos sem próxima ação
- **THEN** eles são listados normalmente, com a indicação "sem próxima ação"

### Requirement: Concluir a próxima ação
O sistema SHALL permitir concluir a próxima ação de um negócio aberto numa única operação que registra uma atividade
vinculada ao negócio (tipo e descrição do que foi feito) e define a nova próxima ação, ou move o negócio para `ganho`
ou `perdido`.

#### Scenario: Concluir e agendar a seguinte
- **WHEN** o usuário conclui a ação informando "Ligação: cliente pediu desconto" e a nova ação "Enviar contraproposta"
  para amanhã
- **THEN** uma atividade do tipo `ligacao` é registrada no negócio com data/hora atual
- **AND** a próxima ação do negócio passa a ser "Enviar contraproposta" com a data de amanhã

#### Scenario: Concluir e fechar o negócio
- **WHEN** o usuário conclui a ação e escolhe `perdido` com motivo "Preço"
- **THEN** a atividade é registrada, o negócio vai para `perdido` e a próxima ação fica vazia

#### Scenario: Falha não grava nada pela metade
- **WHEN** a nova próxima ação é inválida
- **THEN** nem a atividade nem a mudança do negócio são gravadas

#### Scenario: Conflito de versão
- **WHEN** o negócio foi alterado por outra pessoa depois de aberto
- **THEN** a operação é recusada com o aviso de conflito padrão e nada é gravado

### Requirement: Próxima ação visível no funil
Cada cartão de negócio aberto no funil SHALL mostrar a próxima ação e sua data, destacando a ação vencida (data anterior
a hoje) e a ausência de ação.

#### Scenario: Ação vencida
- **WHEN** a data da próxima ação é anterior a hoje
- **THEN** o cartão mostra a ação com a cor de alerta `--bad`

#### Scenario: Ação para hoje
- **WHEN** a data da próxima ação é hoje
- **THEN** o cartão mostra a ação com a cor `--warn`

#### Scenario: Sem próxima ação
- **WHEN** um negócio aberto não tem próxima ação
- **THEN** o cartão mostra "Sem próxima ação" com a cor `--bad`
