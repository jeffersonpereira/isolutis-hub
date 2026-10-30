# Spec Delta

## ADDED Requirements

### Requirement: Estado vazio oferece o plano padrão
Quando a empresa não tem nenhuma conta, a tela Plano de contas SHALL oferecer, junto da criação manual da primeira
conta, a ação "Importar plano padrão", e SHALL pedir confirmação antes de importar.

#### Scenario: Empresa sem plano vê a opção
- **WHEN** um usuário com permissão `financeiro` abre Plano de contas numa empresa sem contas
- **THEN** a tela mostra "Plano de contas vazio" com as ações "Importar plano padrão" e "Criar a primeira conta"

#### Scenario: Confirmar importa e mostra a árvore
- **WHEN** o usuário aciona "Importar plano padrão" e confirma
- **THEN** o plano padrão é importado
- **AND** a árvore de contas passa a ser exibida, com um aviso de sucesso

#### Scenario: Cancelar não altera nada
- **WHEN** o usuário aciona "Importar plano padrão" e cancela a confirmação
- **THEN** nenhuma conta é criada e a tela continua vazia

#### Scenario: Outra pessoa importou antes
- **WHEN** o usuário confirma a importação e o servidor informa que a empresa já tem plano
- **THEN** a tela recarrega e mostra o plano existente com a mensagem do servidor

#### Scenario: Empresa com plano não vê a opção
- **WHEN** a empresa já tem ao menos uma conta
- **THEN** a ação "Importar plano padrão" não é exibida
