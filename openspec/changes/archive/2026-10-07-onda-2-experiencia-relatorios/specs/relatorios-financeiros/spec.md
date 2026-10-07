## ADDED Requirements

### Requirement: Demonstrativo de Resultado (DRE)
O sistema SHALL calcular e exibir um DRE simplificado agrupado por mês, mostrando receitas, custos e resultado líquido para um período selecionado.

#### Scenario: DRE exibe receitas e custos por mês
- **WHEN** o usuário acessa a tela de Relatórios e seleciona o período
- **THEN** o sistema exibe uma tabela com colunas: Mês, Receitas, Custos, Resultado
- **AND** os valores são calculados a partir dos lançamentos com `status = 'recebido'` (receitas) e `status = 'pago'` (custos) dentro do período

#### Scenario: Período padrão é o ano corrente
- **WHEN** o usuário abre a tela de Relatórios pela primeira vez
- **THEN** o período selecionado é de Janeiro a Dezembro do ano corrente

#### Scenario: Resultado positivo e negativo exibidos com cor semântica
- **WHEN** o resultado de um mês é positivo
- **THEN** o valor é exibido com cor `--ok`
- **WHEN** o resultado de um mês é negativo
- **THEN** o valor é exibido com cor `--bad`

---

### Requirement: Fluxo de Caixa consolidado
O sistema SHALL exibir o fluxo de caixa consolidado (receitas e despesas) por período, com saldo acumulado.

#### Scenario: Fluxo de caixa mostra entradas e saídas
- **WHEN** o usuário seleciona a aba "Fluxo de Caixa" na tela de Relatórios
- **THEN** o sistema exibe por mês: Entradas (receitas recebidas), Saídas (despesas pagas), Saldo do Mês, Saldo Acumulado

#### Scenario: Saldo acumulado negativo é destacado
- **WHEN** o saldo acumulado de algum mês é negativo
- **THEN** o valor é exibido em destaque com cor `--bad`

---

### Requirement: Exportação do relatório
O sistema SHALL permitir exportar o relatório ativo (DRE ou Fluxo de Caixa) em PDF e Excel.

#### Scenario: Exportar como PDF
- **WHEN** o usuário clica em "Exportar PDF"
- **THEN** o sistema gera um PDF formatado A4 com o relatório atual e faz download automático
- **AND** o nome do arquivo segue o padrão `DRE-2024-Acme-Ltda.pdf` ou `FluxoCaixa-2024-Acme-Ltda.pdf`

#### Scenario: Exportar como Excel
- **WHEN** o usuário clica em "Exportar Excel"
- **THEN** o sistema gera um arquivo `.xlsx` com os dados do relatório em formato tabular
- **AND** o arquivo inclui uma aba por relatório (DRE e Fluxo de Caixa)
- **AND** o download inicia automaticamente com o nome `Relatorios-2024-Acme-Ltda.xlsx`

#### Scenario: Exportação respeita o período selecionado
- **WHEN** o usuário altera o período e exporta
- **THEN** o arquivo exportado contém apenas os dados do período selecionado
