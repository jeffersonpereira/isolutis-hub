# listagem-titulos-financeiros Specification

## Purpose
Triagem da lista de títulos financeiros: filtros, atalhos, ordenação, paginação, totais e exportação em CSV, feitos no servidor e isolados por empresa.

## Requirements
### Requirement: Filtros da lista de títulos
A API de títulos SHALL filtrar no servidor por tipo, situação, busca por nome do parceiro, parceiro, conta do plano,
conta bancária, vencimento (de/até), pagamento (de/até), faixa de valor devido e origem (recorrente ou avulso). Filtros
combinados SHALL ser aplicados em conjunto (E lógico).

#### Scenario: Filtros combinados
- **WHEN** o usuário filtra por situação "Aberto" e vencimento até 07/11
- **THEN** só os títulos abertos com vencimento até essa data são listados

#### Scenario: Faixa de valor
- **WHEN** o usuário informa valor devido mínimo de R$ 1.000 e máximo de R$ 2.000
- **THEN** só títulos cujo valor devido (título − desconto + multa + juros) está nessa faixa são listados

#### Scenario: Recorrentes
- **WHEN** o usuário filtra por títulos recorrentes
- **THEN** só os gerados por uma recorrência são listados

### Requirement: Atalhos de triagem
A tela SHALL oferecer os atalhos "Atrasados" (em aberto e com vencimento anterior a hoje) e "Vence nos próximos 7 dias"
(em aberto e com vencimento de hoje a hoje + 6 dias), combináveis com tipo e situação.

#### Scenario: Atrasados
- **WHEN** o usuário aciona "Atrasados"
- **THEN** a lista mostra só títulos abertos com vencimento anterior a hoje

#### Scenario: Próximos 7 dias
- **WHEN** o usuário aciona "Vence nos próximos 7 dias"
- **THEN** a lista mostra só títulos abertos com vencimento de hoje até daqui a 6 dias

### Requirement: Gaveta de filtros avançados
A tela SHALL abrir uma gaveta com os filtros avançados a partir do botão "Filtros", que exibe quantos estão ativos, e
SHALL mostrar cada filtro ativo como chip removível acima da tabela.

#### Scenario: Aplicar filtros
- **WHEN** o usuário preenche filtros na gaveta e aciona "Aplicar"
- **THEN** a lista é recarregada na primeira página e os chips correspondentes aparecem

#### Scenario: Remover um chip
- **WHEN** o usuário remove um chip
- **THEN** só aquele filtro deixa de valer e a lista é recarregada

#### Scenario: Limpar
- **WHEN** o usuário aciona "Limpar"
- **THEN** todos os filtros são removidos e o botão volta a mostrar "Filtros"

### Requirement: Paginação
A lista SHALL ser paginada no servidor, com 25, 50 ou 100 títulos por página (padrão 25), e a resposta SHALL informar o
total de títulos do filtro. A tela SHALL mostrar o intervalo exibido e permitir mudar de página e de tamanho.

#### Scenario: Primeira página
- **WHEN** a empresa tem 130 títulos e o usuário abre a tela
- **THEN** são exibidos os 25 primeiros e o total indicado é 130

#### Scenario: Ordem estável
- **WHEN** títulos têm o mesmo vencimento
- **THEN** a ordem entre eles é estável e nenhum aparece em duas páginas

#### Scenario: Página fora do intervalo
- **WHEN** a página pedida não existe mais após uma exclusão ou um filtro mais estreito
- **THEN** a tela volta para a última página existente

#### Scenario: Mudar o filtro volta à primeira página
- **WHEN** o usuário altera qualquer filtro estando na página 3
- **THEN** a lista volta à página 1

### Requirement: Ordenação
A lista SHALL poder ser ordenada por vencimento, valor devido ou parceiro, em ordem crescente ou decrescente, a partir
do cabeçalho da tabela. A ordenação padrão é por vencimento crescente.

#### Scenario: Ordenar por valor
- **WHEN** o usuário clica no cabeçalho "Valor devido" duas vezes
- **THEN** a lista aparece do maior para o menor valor, em todas as páginas

### Requirement: Totais do filtro
O cabeçalho SHALL mostrar os totais em aberto a receber e a pagar do **filtro completo**, calculados no servidor, e o
número de títulos do filtro, independentemente da página exibida.

#### Scenario: Totais independem da página
- **WHEN** o usuário muda da página 1 para a página 2
- **THEN** os totais do cabeçalho permanecem os mesmos

#### Scenario: Totais seguem o filtro
- **WHEN** o usuário filtra por um parceiro
- **THEN** os totais passam a somar só os títulos abertos desse parceiro

### Requirement: Exportação em CSV
O usuário SHALL poder exportar em CSV todos os títulos do filtro atual, sem paginação e na ordem escolhida. O arquivo
SHALL abrir corretamente em planilhas em português (UTF-8 com BOM, separador `;`, decimal com vírgula, datas
`dd/mm/aaaa`) e SHALL neutralizar campos de texto que comecem como fórmula. A exportação exige a permissão `financeiro`.

#### Scenario: Exportar o filtro
- **WHEN** o usuário filtra por títulos abertos e aciona "Exportar CSV" estando na página 2
- **THEN** o arquivo traz todos os títulos abertos do filtro, não só os da página

#### Scenario: Texto que parece fórmula
- **WHEN** a anotação de um título começa com `=`
- **THEN** o CSV grava o campo com um apóstrofo à frente

#### Scenario: Sem permissão
- **WHEN** um usuário sem a permissão `financeiro` chama a exportação
- **THEN** a API responde 403

### Requirement: Isolamento por empresa
Listagem, totais e exportação SHALL considerar somente títulos da empresa ativa.

#### Scenario: Outra empresa
- **WHEN** existem títulos de outra empresa
- **THEN** eles não entram na lista, nos totais nem no CSV
