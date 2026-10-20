## 1. Dependências e limpeza de plataforma

- [x] 1.1 Adicionar `reportlab` em `backend/pyproject.toml`
- [x] 1.2 Remover `weasyprint>=60` de `backend/pyproject.toml`
- [x] 1.3 Confirmar com o usuário se `backend/Dockerfile` está em uso em algum ambiente (pergunta registrada em design.md); se não estiver, remover as dependências de sistema do WeasyPrint (`libpango-1.0-0`, `libpangoft2-1.0-0`, `libpangocairo-1.0-0`, `libcairo2`, `libgdk-pixbuf2.0-0`, `shared-mime-info`) do `Dockerfile` — confirmado: não está em uso, removido
- [x] 1.4 Reinstalar dependências no `.venv` local e confirmar `import reportlab` funcionando

## 2. Módulo compartilhado de composição ReportLab

- [x] 2.1 Criar `backend/app/documents/reportlab_base.py` com: estilos de cor/tipografia (paleta já usada no XLSX: `NAVY #1B2B4B`, `TEAL #22C3CE`, `--ok`/`--bad`), função de cabeçalho fiscal (logo + nome + documento + endereço + contato a partir de `Identidade`), função de rodapé com número de página e timestamp de geração (via `canvasmaker` customizado no `SimpleDocTemplate`, técnica equivalente a `onFirstPage`/`onLaterPages` para numeração total de páginas)
- [x] 2.2 Criar função utilitária de card de KPI (rótulo + valor + cor condicional positivo/negativo) reutilizável entre DRE e Fluxo de Caixa
- [x] 2.3 Criar função utilitária de gráfico de barras mensal (`reportlab.graphics.charts.barcharts.VerticalBarChart`) parametrizada por categorias (meses) e duas séries de valores

## 3. Relatórios financeiros — PDF (DRE e Fluxo de Caixa)

- [x] 3.1 Reescrever `backend/app/documents/relatorio_pdf.py`: função `relatorio_pdf(dados, tipo, empresa_nome, ano, logo, rodape)` passa a montar um `SimpleDocTemplate` com `platypus` em vez de `weasyprint.HTML(...).write_pdf()`
- [x] 3.2 Montar o cabeçalho fiscal (usando o módulo compartilhado) com os dados reais de `Identidade` (hoje só `nome`/`logo`/`rodape` chegam à função — expandir a assinatura para receber `documento`, `endereco`, `contato` também, ou passar o objeto `Identidade` inteiro) — assinatura mudou para `relatorio_pdf(dados, tipo, empresa: Identidade, ano)`
- [x] 3.3 Adicionar os cards de KPI: Receita/Custo/Resultado Total para o DRE; Entradas/Saídas Totais e Saldo Acumulado final para o Fluxo de Caixa
- [x] 3.4 Adicionar o gráfico de barras mensal (Receitas vs Custos no DRE; Entradas vs Saídas no Fluxo de Caixa)
- [x] 3.5 Montar a tabela mensal com `platypus.Table`, mantendo cores semânticas (`positivo`/`negativo`) nas células de resultado/saldo, igual ao comportamento atual
- [x] 3.6 Atualizar `backend/app/routers/relatorios.py` para passar os dados adicionais necessários (identidade completa) na chamada a `relatorio_pdf`
- [x] 3.7 Remover `backend/app/documents/templates/_relatorio_financeiro.html` e `_relatorio_financeiro.css`

## 4. Relatórios financeiros — XLSX

- [x] 4.1 Em `backend/app/documents/relatorio_xlsx.py`, adicionar cabeçalho fiscal: logo embutido via `openpyxl.drawing.image.Image` (a partir do data URL/bytes já disponíveis em `Identidade.logo`) e dados fiscais em linhas acima do título existente — logo inválido (passa a assinatura mas não é imagem decodificável) degrada para sem-logo, não derruba a exportação
- [x] 4.2 Adicionar gráfico nativo (`openpyxl.chart.BarChart`) na aba DRE, usando as colunas Receitas/Custos já escritas
- [x] 4.3 Adicionar gráfico nativo na aba Fluxo de Caixa, usando as colunas Entradas/Saídas já escritas
- [x] 4.4 Atualizar a assinatura de `relatorio_xlsx(...)` e o router (`relatorios.py`) para passar a identidade completa da empresa (hoje só `empresa_nome` chega à função)

## 5. Orçamento — PDF

- [x] 5.1 Reescrever `orcamento_pdf` em `backend/app/documents/render.py` usando ReportLab e o módulo compartilhado de cabeçalho/rodapé (sem numeração de página/timestamp, que são exclusivos dos Relatórios conforme design.md) — rodapé próprio (`_CanvasOrcamento`) repete "Orçamento Nº X · Cliente" em cada página, sem contagem de páginas/timestamp
- [x] 5.2 Montar a tabela de itens com `platypus.Table(..., repeatRows=1)` para repetir o cabeçalho da tabela em cada página automaticamente
- [x] 5.3 Manter todo o conteúdo atual: número do orçamento, data, validade, cliente (nome, contato, cargo, CPF/CNPJ), itens (descrição, mensal, qtd, valor unitário, subtotal), desconto, totais (projeto e mensal), observações
- [x] 5.4 Remover `orcamento_html`, `backend/app/documents/templates/orcamento.html` e `_orcamento.css` (confirmado: não há outro consumidor de `orcamento_html`)
- [x] 5.5 Testar manualmente com um orçamento de poucos itens e um com itens suficientes para forçar quebra de página — testado com 32 itens (3 páginas) e com 1 item, sem logo/obs/desconto
- [x] 5.6 (adicional, descoberto durante a implementação) Escapar nome/contato/CNPJ do cliente e da empresa antes de montar `Paragraph` do ReportLab — ele interpreta um subconjunto de XML e quebra com `<`/`&` não escapados; corrigido com `reportlab_base.esc()`. Também corrigido `test_empresa.py::test_documento_usa_a_identidade_da_empresa`, que chamava a função HTML removida
- [x] 5.7 (adicional, descoberto durante a implementação) Logomarca corrompida (passa a validação de assinatura no upload, mas não é uma imagem válida) não deve derrubar a geração do PDF — `cabecalho_fiscal` degrada para texto sem logo em vez de lançar exceção

## 6. Correção do bug "Saldo do Mês" (tela de Relatórios)

- [x] 6.1 Em `frontend/src/api/tipos.ts`: renomear `FluxoItem.saldo` para `saldo_mes`
- [x] 6.2 Em `frontend/src/features/relatorios.ts`: atualizar as referências de `row.saldo` para `row.saldo_mes` na tabela de Fluxo de Caixa
- [x] 6.3 Verificar visualmente a tela de Relatórios → aba Fluxo de Caixa → coluna "Saldo do Mês" exibindo os valores corretos (não mais R$ 0,00 fixo) — **não executado como teste em navegador**: ambiente local não tem PostgreSQL/Docker disponível (limitação já conhecida, ver memória do projeto), então não há como logar e carregar dados reais. Verificado estaticamente: `npx tsc --noEmit` limpo e a chave `saldo_mes` agora é idêntica nos dois lados (backend em `calcular_fluxo_caixa`, frontend em `FluxoItem` e no template). Recomendo confirmar visualmente quando o backend estiver acessível.

## 7. Validação

- [x] 7.1 Rodar testes de backend existentes relacionados a relatórios e orçamento (`pytest` nos arquivos cobrindo `calcular_dre`, `calcular_fluxo_caixa`, orçamentos) e confirmar que nada relacionado a geração de documentos quebrou — não há testes automatizados dedicados a `relatorio_pdf`/`relatorio_xlsx`/`orcamento_pdf` neste repositório (confirmado por busca); os que existem e tocam a área (`test_comercial.py`, `test_escopo_api.py`, `test_parceiros.py`) exigem PostgreSQL, indisponível nesta máquina (ver memória do projeto). Roda limpo: coleta completa de 314 testes sem erro de import (nenhuma referência órfã a `orcamento_html`/assinaturas antigas) e os testes puros (`--noconftest`), incluindo o `test_empresa.py` atualizado; as falhas observadas em `test_permissoes_rotas.py` e `test_usuario_schemas.py` são de ambiente (versão do FastAPI/Pydantic instalada vs. esperada por este venv, que estava com várias dependências faltando antes desta sessão) e não têm relação com esta mudança. `ruff check` e `mypy app --ignore-missing-imports` (comando exato do CI) sem nenhum erro nos arquivos tocados por esta mudança
- [x] 7.2 Gerar manualmente, em ambiente local: PDF do DRE, PDF do Fluxo de Caixa, XLSX do DRE+Fluxo, PDF de um orçamento — abrir todos os arquivos e confirmar que abrem sem erro e exibem os dados corretos — gerados via script com dados de exemplo (incluindo casos extremos: sem dados, sem logo, logo inválido, orçamento com 32 itens forçando paginação); todos produziram PDF/XLSX válidos (cabeçalho `%PDF`/estrutura `.xlsx` íntegra). Não abri os arquivos visualmente em um leitor de PDF/Excel — validação ficou nos bytes e na estrutura
- [ ] 7.3 Deploy em produção (Vercel) e repetir a validação do passo 7.2 diretamente em produção — é o ambiente onde o bug original ocorria e nunca foi reproduzido localmente — **não executado**: requer decisão do usuário sobre quando/como fazer o deploy
- [ ] 7.4 Confirmar com o usuário que o padrão visual (cabeçalho fiscal, KPIs, gráfico, paginação) atende à expectativa de "relatório profissional" — **pendente**: depende do usuário ver os documentos gerados
