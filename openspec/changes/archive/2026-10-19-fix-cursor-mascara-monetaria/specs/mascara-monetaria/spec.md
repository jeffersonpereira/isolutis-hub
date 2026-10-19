## MODIFIED Requirements

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
