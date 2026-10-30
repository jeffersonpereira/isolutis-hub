## Context

O backend (FastAPI) roda como função Python na Vercel (`backend/.vercel/project.json`), sem acesso a `apt-get` ou a um passo de build customizado — só o que `pip install` resolve em puro Python ou com wheels manylinux que não exijam bibliotecas de sistema ausentes no runtime. O WeasyPrint (`backend/app/documents/relatorio_pdf.py` e `render.py::orcamento_pdf`) depende de Pango/Cairo/GDK-Pixbuf via `cffi`, que não existem nesse ambiente. Dois testes de controle confirmaram: nem o PDF de Relatórios nem o de Orçamento jamais funcionaram em produção, apesar de o `Dockerfile` do projeto instalar essas libs — indício de que o Dockerfile corresponde a um caminho de deploy que não é o usado hoje (Vercel).

O XLSX (`openpyxl`, puro Python) já funciona tecnicamente; o pedido aqui é de acabamento visual equivalente ao do PDF.

## Goals / Non-Goals

**Goals:**
- Gerar o PDF de Relatórios e de Orçamento inteiramente em Python puro, sem depender de bibliotecas nativas de sistema, para funcionar no runtime da Vercel.
- Elevar o padrão visual de ambos os PDFs e do XLSX ao nível "ERP financeiro": cabeçalho fiscal completo, cards de KPI, gráfico mensal, numeração de página e timestamp (os dois últimos só fazem sentido no PDF).
- Corrigir o bug de exibição do Saldo do Mês na tela de Relatórios (`saldo_mes` vs `saldo`).

**Non-Goals:**
- Redesenho do conteúdo/estrutura de dados do Orçamento (itens, desconto, totais) — só o acabamento visual e o motor de geração mudam.
- Migrar a hospedagem do backend para fora da Vercel (alternativa descartada por aumentar o escopo de infraestrutura sem necessidade, já que o ReportLab resolve o problema sem trocar de plataforma).
- Internacionalização ou suporte a outros moeda/locale além de pt-BR/BRL.
- Qualquer mudança no fluxo de e-mail/notificações — nenhum dos PDFs é hoje enviado por e-mail, só baixado sob demanda.

## Decisions

### D1 — Motor de PDF: ReportLab vs alternativas

**Escolhido: ReportLab** (`platypus` para o layout de página + `reportlab.graphics.charts` para o gráfico de barras).

| Critério | ReportLab | xhtml2pdf | Imprimir via navegador (HTML + `window.print()`) |
|---|---|---|---|
| Dependência nativa | Nenhuma | Nenhuma (usa ReportLab por baixo) | Nenhuma |
| Download automático de 1 clique | Sim | Sim | Não (abre aba, usuário salva) |
| Suporte a CSS/flexbox | N/A (API própria) | Parcial, propenso a bugs de layout | Total |
| Controle fino de layout (cards, gráfico, paginação) | Alto, mas verboso | Baixo | Alto, mas depende do motor de impressão do navegador |

`xhtml2pdf` reaproveitaria os templates Jinja2/CSS atuais, mas seu suporte a CSS é notoriamente limitado (sem flexbox/grid confiável), o que compromete justamente os cards de KPI e o layout "ERP" pedido. A opção de imprimir via navegador foi descartada porque muda a UX de "baixa o PDF" para "abre e salva manualmente" — decisão de produto já tomada ao escolher reescrever em ReportLab em vez disso.

### D2 — Gráfico mensal no PDF: `reportlab.graphics.charts.barcharts`

Gráfico de barras simples (receitas/custos ou entradas/saídas por mês) desenhado como `Drawing` e inserido como *flowable* no documento `platypus`. Sem dependência de imagem rasterizada (evita custo de renderização e mantém o PDF leve). Paridade visual com o gráfico do XLSX não é pixel-perfect (motores diferentes), mas ambos comunicam a mesma tendência mensal.

### D3 — Gráfico nativo no XLSX: `openpyxl.chart.BarChart`

`openpyxl` já tem suporte embutido a gráficos nativos do Excel (sem rasterizar nada, o gráfico fica editável pelo usuário no arquivo baixado). Usa as mesmas colunas de dados já escritas na planilha (`_escrever_cabecalho`/linhas de dados existentes), ancorando o gráfico ao lado da tabela.

### D4 — Estrutura de código: função de composição compartilhada

Criar um módulo auxiliar (`backend/app/documents/reportlab_base.py` ou equivalente) com os elementos reutilizáveis entre Relatórios e Orçamento: cabeçalho fiscal (logo + identidade), rodapé com numeração de página/timestamp, estilos de cor/tipografia. Evita duplicar a lógica de desenhar o cabeçalho em dois arquivos (`relatorio_pdf.py` e `render.py`), já que o padrão visual agora é o mesmo nos dois documentos.

### D5 — Templates HTML/CSS removidos ou mantidos?

**Removidos** (`_relatorio_financeiro.html`, `_relatorio_financeiro.css`, `orcamento.html`, `_orcamento.css`): como o ReportLab não consome HTML/CSS, esses arquivos ficam mortos. Mantê-los "por precaução" criaria confusão sobre qual é a fonte real do layout. `orcamento_html()` (usada hoje só internamente por `orcamento_pdf`) também é removida — nada mais a consome após a migração (confirmado: nenhum outro ponto do código chama `orcamento_html` diretamente).

### D6 — Correção do bug `saldo_mes`/`saldo`

Corrigir no tipo (`FluxoItem.saldo` → `saldo_mes`) em vez de renomear no backend: o backend já usa `saldo_mes` de forma consistente em `calcular_fluxo_caixa`, no XLSX e no cabeçalho do PDF; o frontend é o único lugar com o nome divergente.

## Risks / Trade-offs

- **[Risco] Fidelidade visual do gráfico ReportLab é mais limitada que CSS/SVG customizado** → Mitigação: gráfico de barras simples (sem gradientes/animação), suficiente para comunicar tendência mensal; não é o elemento central do documento.
- **[Risco] Reescrever o layout do Orçamento em ReportLab pode introduzir regressão sutil em paginação de itens** (hoje resolvida via CSS `page-break-inside: avoid` e `thead` repetido) → Mitigação: usar `platypus.Table` com `repeatRows=1` (cabeçalho repete automaticamente) e testar manualmente com um orçamento de muitos itens antes de considerar a tarefa concluída.
- **[Risco] Remover o Dockerfile das dependências do WeasyPrint pode afetar algum ambiente que ainda use o caminho Docker** → Mitigação: confirmar com o usuário se o Dockerfile está em uso antes de alterar (tratado como tarefa de verificação, não de remoção automática às cegas).
- **[Trade-off] Perda do templating HTML/CSS (mais familiar para ajustes rápidos de estilo) em troca de eliminar a dependência nativa** → Aceito: é a condição para o PDF funcionar na Vercel; não há meio-termo que preserve HTML/CSS sem reintroduzir uma lib com dependência nativa ou mudar a hospedagem.

## Migration Plan

1. Implementar o módulo compartilhado de composição ReportLab (cabeçalho fiscal, rodapé com paginação/timestamp).
2. Reescrever `relatorio_pdf.py` (DRE e Fluxo de Caixa) sobre o módulo compartilhado, com cards de KPI e gráfico.
3. Reescrever `orcamento_pdf` em `render.py` sobre o mesmo módulo, preservando o conteúdo atual do orçamento.
4. Enriquecer `relatorio_xlsx.py` com cabeçalho fiscal/logo e gráfico nativo.
5. Corrigir `FluxoItem.saldo` → `saldo_mes` no frontend.
6. Remover `weasyprint` do `pyproject.toml`, adicionar `reportlab`; remover templates HTML/CSS mortos.
7. Validar manualmente: DRE, Fluxo de Caixa e Orçamento (caso com poucos itens e caso com muitos itens, para testar paginação) gerando PDF e XLSX reais em ambiente com os dados de uma empresa de teste.
8. Deploy e confirmação em produção (ambiente Vercel) — o teste que importa de fato, já que o bug nunca reproduziu localmente.

Sem necessidade de rollback de dados (não há migração de banco); rollback é reverter o deploy caso o ReportLab apresente algum problema inesperado em produção.

## Open Questions

- O `Dockerfile` do backend (que instala as libs do WeasyPrint) está em uso em algum ambiente além da Vercel? Se não estiver, ele deveria ser removido ou simplificado no mesmo change — a ser confirmado antes de tocar nele.
