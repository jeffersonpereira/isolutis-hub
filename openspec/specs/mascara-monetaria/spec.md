# mascara-monetaria Specification

## Purpose
TBD - created by archiving change mascara-monetaria-inputs. Update Purpose after archive.
## Requirements
### Requirement: Máscara monetária na digitação
Todo campo de entrada de valor em reais do Hub SHALL aplicar uma máscara monetária enquanto o usuário digita: os dígitos digitados entram sempre pela direita como centavos, o campo exibe separador de milhar (`.`) e vírgula decimal (`,`), sempre com duas casas decimais. O campo SHALL ignorar qualquer caractere que não seja dígito, digitado ou colado. O resultado SHALL ser correto tanto quando o valor é atribuído de uma vez (ex.: colar) quanto quando é digitado tecla a tecla, do início ao fim, em sequência — nos dois casos a sequência final de dígitos digitados determina o mesmo valor.

#### Scenario: Digitar um valor
- **WHEN** o usuário digita `150000` num campo monetário vazio
- **THEN** o campo exibe `1.500,00`

#### Scenario: Digitar valor menor que um real
- **WHEN** o usuário digita `5` num campo monetário vazio
- **THEN** o campo exibe `0,05`

#### Scenario: Digitar vários dígitos em sequência, tecla a tecla
- **WHEN** o usuário digita, uma tecla por vez, `1`, `3`, `2`, `2`, `0` num campo monetário vazio (cada tecla dispara seu próprio evento de digitação, como o navegador realmente faz, com o cursor avançando a cada tecla)
- **THEN** o campo exibe `132,20` ao final — o mesmo resultado que atribuir `13220` de uma vez

#### Scenario: Apagar dígitos
- **WHEN** o campo exibe `1.500,00` e o usuário apaga um caractere do final
- **THEN** o campo passa a exibir `150,00`

#### Scenario: Colar um valor com caracteres não numéricos
- **WHEN** o usuário cola `R$ 1.500,00` num campo monetário
- **THEN** o campo exibe `1.500,00`

### Requirement: Valor inicial de campo monetário já mascarado
Ao abrir a edição de um registro com valor já gravado, ou ao preencher um campo monetário a partir de outro dado da tela (ex.: preço de um produto escolhido), o campo SHALL exibir o valor já formatado na mesma máscara, sem exigir que o usuário digite algo primeiro.

#### Scenario: Editar título existente
- **WHEN** o usuário abre a edição de um título cujo valor gravado é `1500.5`
- **THEN** o campo "Valor do título" exibe `1.500,50`

#### Scenario: Campo vazio ou zero
- **WHEN** o valor gravado é nulo, vazio ou zero
- **THEN** o campo monetário é exibido vazio

#### Scenario: Preço herdado ao escolher um produto no orçamento
- **WHEN** o usuário escolhe um produto numa linha de item do orçamento
- **THEN** o campo "Valor unit." daquela linha passa a exibir o preço de referência do produto já mascarado

### Requirement: Campos de quantidade e percentual não recebem a máscara monetária
Campos que representam quantidade (ex.: quantidade de item de orçamento) ou percentual (ex.: participação societária) SHALL NOT receber a máscara monetária, mesmo aceitando apenas valores decimais.

#### Scenario: Quantidade de item do orçamento
- **WHEN** o usuário digita `12` no campo de quantidade de um item do orçamento
- **THEN** o campo exibe `12`, sem separador de milhar nem casas decimais forçadas

#### Scenario: Participação societária
- **WHEN** o usuário digita `40` no campo de participação na empresa
- **THEN** o campo exibe `40`, sem a máscara monetária

### Requirement: Valor enviado ao servidor sem máscara
A máscara monetária SHALL ser apenas de apresentação: o valor enviado ao salvar SHALL ser o número correspondente, sem separador de milhar, ponto ou vírgula formatando a exibição.

#### Scenario: Salvar título com valor mascarado
- **WHEN** o usuário salva um título cujo campo "Valor do título" exibe `1.500,00`
- **THEN** o cadastro é gravado com o valor numérico `1500`

#### Scenario: Cálculo de totais usa o valor numérico, não o texto mascarado
- **WHEN** um orçamento tem um item com "Valor unit." exibindo `250,00` e quantidade `2`
- **THEN** o total do item calculado é `500`, não uma concatenação do texto mascarado
