## ADDED Requirements

### Requirement: Alternância manual de tema
A interface SHALL oferecer, na barra superior, a escolha entre os temas Sistema, Claro e Escuro, com Sistema como padrão, e a escolha SHALL ter efeito imediato em toda a aplicação.

#### Scenario: Escolher o tema escuro
- **WHEN** o usuário escolhe "Escuro" na alternância de tema
- **THEN** a aplicação inteira passa a usar a paleta escura imediatamente

#### Scenario: Escolher o tema do sistema
- **WHEN** o usuário escolhe "Sistema" e o sistema operacional está em modo escuro
- **THEN** a aplicação usa a paleta escura

#### Scenario: Sistema muda enquanto a aplicação está aberta
- **WHEN** a preferência é "Sistema" e o usuário altera o modo do sistema operacional
- **THEN** a aplicação acompanha a mudança sem recarregar

#### Scenario: Estado atual indicado
- **WHEN** o usuário abre a alternância de tema
- **THEN** a opção em vigor aparece marcada e acessível por leitores de tela

---

### Requirement: Persistência do tema e aplicação sem flash
O sistema SHALL lembrar a escolha de tema entre sessões e SHALL aplicá-la antes da primeira pintura da página, sem exibir momentaneamente o tema errado.

#### Scenario: Escolha lembrada
- **WHEN** o usuário escolhe "Escuro" e recarrega a aplicação
- **THEN** a aplicação abre diretamente no tema escuro

#### Scenario: Sem flash do tema errado
- **WHEN** a página é carregada com a preferência "Escuro"
- **THEN** a primeira pintura já usa a paleta escura

#### Scenario: Armazenamento indisponível
- **WHEN** o navegador não permite gravar preferências
- **THEN** a aplicação funciona normalmente seguindo o tema do sistema
