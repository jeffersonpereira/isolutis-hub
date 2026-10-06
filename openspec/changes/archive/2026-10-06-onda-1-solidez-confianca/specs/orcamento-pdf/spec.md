## ADDED Requirements

### Requirement: Geração de orçamento em PDF
O endpoint de documento de orçamento SHALL retornar um arquivo PDF válido em vez de HTML, mantendo o mesmo conteúdo e estrutura do template atual.

#### Scenario: Download retorna arquivo PDF
- **WHEN** `GET /api/v1/orcamentos/{id}/documento` é chamado
- **THEN** a resposta tem `Content-Type: application/pdf`
- **AND** o header `Content-Disposition` usa extensão `.pdf` (ex: `Orcamento-2024-001-Acme-Ltda.pdf`)
- **AND** o conteúdo é um PDF válido que pode ser aberto por qualquer leitor de PDF

#### Scenario: PDF respeita layout A4
- **WHEN** o PDF é gerado
- **THEN** o conteúdo é formatado para página A4 (210mm × 297mm)
- **AND** as margens respeitam pelo menos 15mm em todos os lados
- **AND** a tabela de itens não é cortada entre páginas

#### Scenario: PDF inclui todos os dados do orçamento
- **WHEN** o PDF é gerado para um orçamento com itens
- **THEN** o documento contém: número do orçamento, data, validade, nome do cliente, lista completa de itens com descrição/quantidade/valor, totais (projeto e mensal), desconto se houver, e observações se houver

#### Scenario: Orçamento com muitos itens pagina corretamente
- **WHEN** o orçamento tem mais itens do que cabem em uma página
- **THEN** o PDF tem múltiplas páginas
- **AND** o cabeçalho com dados do cliente e número repetem em cada página
- **AND** nenhum item é omitido ou truncado

---

### Requirement: Fallback em caso de falha na geração
O sistema SHALL retornar um erro claro se a geração do PDF falhar, sem expor detalhes internos.

#### Scenario: Erro na geração retorna HTTP 500 com mensagem amigável
- **WHEN** a biblioteca de geração de PDF falha
- **THEN** o endpoint retorna HTTP 500
- **AND** o corpo do erro segue o padrão `{"erro": {"codigo": "pdf_indisponivel", "mensagem": "..."}}`
- **AND** nenhum stack trace ou caminho de arquivo é exposto na resposta
