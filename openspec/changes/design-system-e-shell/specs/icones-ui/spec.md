## ADDED Requirements

### Requirement: Ícones embutidos e sem dependência externa
A aplicação SHALL fornecer um conjunto de ícones SVG embutido no próprio código, carregado uma única vez, e SHALL NOT depender de serviços externos nem de pacote de ícones em tempo de execução.

#### Scenario: Ícones sem requisição externa
- **WHEN** a aplicação é carregada
- **THEN** nenhum ícone é obtido de domínio externo
- **AND** os ícones usados na tela estão disponíveis a partir de um único conjunto embutido

#### Scenario: Nome de ícone inexistente
- **WHEN** o código pede um ícone que não existe no conjunto
- **THEN** a interface continua funcionando sem ícone e sem erro visível ao usuário

---

### Requirement: Acessibilidade dos ícones
Ícones decorativos SHALL ser ocultados de tecnologias assistivas, e todo botão que tenha somente um ícone SHALL ter nome acessível.

#### Scenario: Ícone decorativo ao lado de texto
- **WHEN** um ícone acompanha um texto, como num item de menu
- **THEN** o ícone é ocultado das tecnologias assistivas e o texto fornece o nome

#### Scenario: Botão somente com ícone
- **WHEN** um botão exibe apenas um ícone, como o de recolher a barra lateral ou o de tema
- **THEN** o botão tem nome acessível e dica com esse nome

#### Scenario: Ícone que carrega sentido sozinho
- **WHEN** um ícone transmite informação sem texto ao lado, como um estado
- **THEN** ele tem papel de imagem e rótulo acessível

---

### Requirement: Atribuição de licença dos ícones
O conjunto de ícones SHALL registrar, no próprio arquivo, a origem dos traçados e a licença que exige atribuição.

#### Scenario: Atribuição presente
- **WHEN** o arquivo de ícones é inspecionado
- **THEN** seu cabeçalho cita a origem dos traçados e a licença ISC
