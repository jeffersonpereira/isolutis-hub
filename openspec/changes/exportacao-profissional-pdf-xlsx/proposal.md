## Why

A exportação em PDF dos Relatórios financeiros (DRE/Fluxo de Caixa) e do Orçamento nunca funcionou em produção: o WeasyPrint, usado para gerar o PDF no servidor, depende de bibliotecas nativas (Pango, Cairo) que não existem no runtime de função Python da Vercel, onde o backend roda hoje. Toda chamada termina em erro genérico ("Não foi possível gerar o PDF"). Além de corrigir essa falha de plataforma, o cliente quer que os documentos exportados (PDF e XLSX) tenham acabamento visual equivalente ao de um sistema de gestão financeira comercial, não apenas uma tabela formatada.

## What Changes

- **Motor de PDF**: troca de WeasyPrint por ReportLab (biblioteca Python pura, sem dependência nativa) em todos os pontos de geração de PDF do backend — Relatórios financeiros e Orçamento.
- **Redesenho visual dos Relatórios (PDF e XLSX)**: cabeçalho com identidade fiscal completa da empresa (logo, nome, CNPJ/CPF, endereço, contato), cards de KPI com os totais do período em destaque, gráfico de barras com a evolução mensal, numeração de página e timestamp de geração no PDF.
- **Redesenho visual do Orçamento (PDF)**: mesmo padrão de cabeçalho fiscal e acabamento dos Relatórios, mantendo o conteúdo atual (itens, totais, desconto, observações, validade).
- **XLSX enriquecido**: cabeçalho fiscal com logo embutido e gráfico nativo do Excel (via `openpyxl.chart`) com a mesma evolução mensal do PDF, mantendo a formatação de cores e totais já existente.
- **Correção de bug lateral**: a tela de Relatórios (não a exportação) exibe sempre R$ 0,00 na coluna "Saldo do Mês" do Fluxo de Caixa por divergência entre a chave `saldo_mes` devolvida pelo backend e `saldo` esperada pelo tipo `FluxoItem` do frontend.

## Capabilities

### New Capabilities

(nenhuma — este change modifica capacidades existentes)

### Modified Capabilities

- `relatorios-financeiros`: a exportação em PDF passa a usar ReportLab (em vez de WeasyPrint) e ganha cabeçalho fiscal completo, cards de KPI, gráfico mensal, numeração de página e timestamp; a exportação em XLSX ganha cabeçalho fiscal/logo e gráfico nativo; a tela de Fluxo de Caixa passa a exibir corretamente o Saldo do Mês.
- `orcamento-pdf`: a geração do PDF passa a usar ReportLab (em vez de WeasyPrint) e o layout é atualizado para o mesmo padrão visual (cabeçalho fiscal completo) adotado nos Relatórios, mantendo o conteúdo e a estrutura de dados do orçamento inalterados.

## Impact

**Backend:**
- `backend/app/documents/relatorio_pdf.py` — reescrito com ReportLab (sai o template Jinja2/HTML/CSS, entra composição programática de página)
- `backend/app/documents/relatorio_xlsx.py` — acrescenta cabeçalho fiscal/logo e gráfico via `openpyxl.chart`
- `backend/app/documents/render.py` — `orcamento_pdf` reescrito com ReportLab; `orcamento_html` e os templates `orcamento.html`/`_orcamento.css` tornam-se obsoletos e são removidos
- `backend/app/documents/templates/_relatorio_financeiro.html` e `.css` — removidos (substituídos pela composição ReportLab)
- `backend/pyproject.toml` — remove `weasyprint`, adiciona `reportlab`
- `backend/Dockerfile` — remove as dependências de sistema do WeasyPrint (`libpango`, `libcairo`, `libgdk-pixbuf`, etc.), hoje necessárias só por ele
- `backend/app/services/empresa.py` / `app/documents/render.py` (`Identidade`) — sem mudança de contrato, mas os campos `documento`, `endereco`, `contato` passam a ser usados também no cabeçalho dos Relatórios (hoje só no Orçamento)

**Frontend:**
- `frontend/src/api/tipos.ts` — campo `saldo` do tipo `FluxoItem` renomeado para `saldo_mes`, alinhando com a resposta real do backend
- `frontend/src/features/relatorios.ts` — ajusta a referência à chave corrigida

**Dependências:**
- Remove `weasyprint>=60`
- Adiciona `reportlab` (versão a definir em design.md)
