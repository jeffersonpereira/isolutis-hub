## ADDED Requirements

### Requirement: Cabeçalho fiscal no relatório exportado
O relatório exportado (PDF e XLSX) SHALL exibir um cabeçalho com a identidade fiscal da empresa: logomarca (quando cadastrada), nome, documento (CNPJ ou CPF), endereço e contato (quando cadastrados).

#### Scenario: Cabeçalho completo quando os dados estão cadastrados
- **WHEN** a empresa tem logomarca, CNPJ/CPF, endereço e contato cadastrados
- **AND** o usuário exporta o relatório em PDF ou Excel
- **THEN** o cabeçalho do documento exibe a logomarca, o nome da empresa, o documento formatado, o endereço e o contato

#### Scenario: Cabeçalho sem logomarca ou dados opcionais
- **WHEN** a empresa não tem logomarca cadastrada, ou não tem CNPJ/CPF, endereço ou contato cadastrados
- **THEN** o cabeçalho exibe apenas os dados disponíveis, sem espaços em branco ou campos vazios visíveis

### Requirement: Resumo de indicadores no PDF exportado
O PDF exportado SHALL exibir, em destaque logo após o cabeçalho, um resumo com os totais do período: para o DRE, Receita Total, Custo Total e Resultado; para o Fluxo de Caixa, Entradas Totais, Saídas Totais e Saldo Acumulado final.

#### Scenario: Resumo do DRE
- **WHEN** o usuário exporta o DRE em PDF
- **THEN** o documento exibe três indicadores em destaque: Receita Total, Custo Total e Resultado do período, somados a partir dos meses exibidos na tabela

#### Scenario: Resumo do Fluxo de Caixa
- **WHEN** o usuário exporta o Fluxo de Caixa em PDF
- **THEN** o documento exibe três indicadores em destaque: Entradas Totais, Saídas Totais e Saldo Acumulado do último mês do período

#### Scenario: Indicador negativo é destacado
- **WHEN** um indicador do resumo (Resultado ou Saldo Acumulado) é negativo
- **THEN** ele é exibido com a cor semântica `--bad`

### Requirement: Gráfico de evolução mensal no relatório exportado
O relatório exportado (PDF e XLSX) SHALL incluir um gráfico de barras com a evolução mensal dos valores do período, usando os mesmos dados exibidos na tabela.

#### Scenario: Gráfico no PDF
- **WHEN** o usuário exporta o DRE ou o Fluxo de Caixa em PDF
- **THEN** o documento inclui um gráfico de barras com um mês por categoria, mostrando as duas séries principais (Receitas/Custos no DRE, Entradas/Saídas no Fluxo de Caixa)

#### Scenario: Gráfico no XLSX
- **WHEN** o usuário exporta o DRE ou o Fluxo de Caixa em Excel
- **THEN** a aba correspondente inclui um gráfico de barras nativo do Excel (editável pelo usuário), construído a partir das colunas de dados já presentes na planilha

#### Scenario: Relatório sem lançamentos no período
- **WHEN** não há nenhum lançamento no período selecionado
- **THEN** o PDF e o XLSX são gerados normalmente, com o gráfico omitido ou vazio (sem erro)

### Requirement: Paginação e rodapé informativo no PDF exportado
O PDF exportado SHALL exibir, no rodapé de cada página, o número da página atual e o total de páginas, além da data e hora de geração do documento.

#### Scenario: Relatório de uma página
- **WHEN** o relatório exportado em PDF cabe em uma página
- **THEN** o rodapé exibe "Página 1 de 1" e o timestamp de geração

#### Scenario: Relatório com múltiplas páginas
- **WHEN** o relatório exportado em PDF ocupa mais de uma página
- **THEN** cada página exibe seu número e o total de páginas (ex: "Página 2 de 3")
- **AND** o cabeçalho da tabela se repete em cada página
