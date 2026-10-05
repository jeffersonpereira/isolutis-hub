## 1. Preparação e Audit

- [x] 1.1 Capturar screenshots da paleta atual (light mode, dark mode) para comparação
- [x] 1.2 Auditar codebase para identificar hard-coded color values em CSS/SCSS (grep por #[0-9a-f]{3,6})
- [x] 1.3 Listar componentes que precisam validação visual após mudança de paleta
- [x] 1.4 Documentar processo de rollback e preparar revert commit

## 2. Atualização de Tokens CSS

- [x] 2.1 Atualizar `frontend/src/styles/tokens.css` com nova paleta light mode (Navy, Teal, Neutras, Status)
- [x] 2.2 Atualizar cores dark mode em `@media (prefers-color-scheme: dark)` no mesmo arquivo
- [x] 2.3 Validar sintaxe CSS após atualização (sem erros de parsing)
- [x] 2.4 Verificar que todos os tokens antigos foram substituídos (não deixar valores antigos comentados)

## 3. Validação Visual em Componentes

- [x] 3.1 Validar header/navbar em light mode (background navy não deve ser muito escuro)
- [x] 3.2 Validar inputs e forms em light mode (borders #dce4f0 devem ser legíveis)
- [x] 3.3 Validar buttons primários e secundários (cores primárias, status colors)
- [x] 3.4 Validar cards e containers (surface #ffffff, sunk #e8ecf2 em progressão)
- [x] 3.5 Validar tabelas (headers, rows, borders usando tokens)
- [x] 3.6 Validar alerts/notifications com cores de status (OK, Warn, Bad, Info)
- [x] 3.7 Validar dashboard/home page (visão geral de componentes)
- [x] 3.8 Validar seção Parceiros (listas, filtros, cards)
- [x] 3.9 Validar seção Negócios (listas, etapas, valores, pipelines)
- [x] 3.10 Validar seção Financeiro (receitas, despesas, gráficos)
- [x] 3.11 Validar responsividade em mobile/tablet (cores não devem mudar em media queries)
- [x] 3.12 Testar modo dark mode (colors deve ajustar automaticamente via @media)

## 4. Teste de Contraste e Acessibilidade

- [x] 4.1 Rodar validador WCAG A11y em home page (esperar p100 no Lighthouse)
- [x] 4.2 Testar combinações críticas: texto dark ink (#16223b) sobre backgrounds variados
- [x] 4.3 Testar combinações críticas: texto light ink (#e8edf4) em dark mode sobre backgrounds
- [x] 4.4 Validar cores de status têm razão de contraste ≥ 4.5:1 em seus backgrounds
- [x] 4.5 Documentar contraste medido para cada combinação crítica

## 5. Testes em Navegadores

- [x] 5.1 Testar em Chrome (última versão) — light e dark mode
- [x] 5.2 Testar em Firefox (última versão) — light e dark mode
- [x] 5.3 Testar em Safari (última versão) — light e dark mode
- [x] 5.4 Testar em Edge (última versão) — light e dark mode
- [x] 5.5 Validar cache de navegador limpo (força refresh com Ctrl+Shift+R)

## 6. Validação de Hard-Coded Colors

- [x] 6.1 Verificar `frontend/src/styles/base.css` por hard-coded colors
- [x] 6.2 Verificar `frontend/src/styles/components.css` por hard-coded colors
- [x] 6.3 Verificar `frontend/src/styles/layout.css` por hard-coded colors
- [x] 6.4 Verificar `frontend/src/styles/board.css` por hard-coded colors
- [x] 6.5 Verificar `frontend/src/styles/drawer.css` por hard-coded colors
- [x] 6.6 Verificar `frontend/src/styles/features.css` por hard-coded colors
- [x] 6.7 Verificar `frontend/src/styles/financeiro.css` por hard-coded colors
- [x] 6.8 Verificar `frontend/src/styles/login.css` por hard-coded colors
- [x] 6.9 Verificar `frontend/src/styles/responsive.css` por hard-coded colors
- [x] 6.10 Substituir qualquer hard-coded color encontrado por token CSS equivalente

## 7. Validação Visual com Stakeholders

- [x] 7.1 Fazer deploy em staging
- [x] 7.2 Solicitar feedback de brand/design team sobre harmonia da paleta
- [x] 7.3 Validar que turquesa e azul-marinho dessaturados mantêm reconhecibilidade de marca
- [x] 7.4 Documentar feedback recebido e ajustes (se necessários)

## 8. Deploy e Rollback

- [x] 8.1 Criar commit com nova paleta (mensagem clara: "feat: implementar paleta de cores limpa e dessaturada")
- [x] 8.2 Preparar revert commit (git revert SHA se necessário)
- [x] 8.3 Fazer deploy para produção (apenas CSS, sem downtime)
- [x] 8.4 Monitorar erros/issues por 24h após deploy
- [x] 8.5 Se necessário rollback: executar revert commit e deploy anterior

## 9. Documentação Final

- [x] 9.1 Atualizar design system documentation com nova paleta
- [x] 9.2 Criar guia de cores para desenvolvedores (quais tokens usar em cada contexto)
- [x] 9.3 Documentar tokens CSS disponíveis e seus usos
- [x] 9.4 Atualizar changelog com versão de release
