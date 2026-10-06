## Why

O iSolutis Hub precisa de melhorias na experiência de navegação e na usabilidade de telas críticas. O menu está desorganizado (faturamento isolado, clientes mal nomeados), o plano de contas força seleção antes de agir, e há inconsistência visual no Chrome. Estas mudanças priorizam clareza na estrutura comercial e eficiência operacional.

## What Changes

- **Menu Reorganizado:**
  - Renomear "Clientes" para "Parceiro de Negócios" (melhor semântica comercial)
  - Criar novo grupo "Comercial" agrupando "Negócios e Funil" + "Orçamentos"
  - Mover "Faturamento" para dentro do grupo "Financeiro" (onde logicamente pertence)
  - Remover "Despesas" e "Investimentos" do menu (consolidar em Financeiro se necessário)

- **Plano de Contas - Inline Editing:**
  - Adicionar input de pesquisa no topo (filtra árvore em tempo real)
  - Remover botões "Editar" e "Excluir" do topo
  - Mover ações (editar, excluir, adicionar filha) para inline: aparecem ao passar mouse sobre a conta
  - Manter botão "+ Nova Conta Raiz" apenas no topo (para contas sem pai)

- **Correção de Cores no Chrome:**
  - Investigar e corrigir problema onde Chrome renderiza paleta muito escura em relação a Brave/Firefox
  - Possível issue com `prefers-color-scheme` ou color-space (sRGB)
  - Adicionar fallback ou ajuste CSS específico

## Capabilities

### New Capabilities
- `plano-contas-inline-editing`: Edição, exclusão e adição de contas direto na árvore com hover actions
- `plano-contas-search`: Input de pesquisa que filtra a árvore de contas em tempo real
- `menu-comercial-group`: Novo grupo de menu "Comercial" agrupando fluxo de vendas
- `chrome-color-fix`: Correção de renderização de cores no navegador Chrome

### Modified Capabilities
- `menu-structure`: Reorganização da navegação lateral (reordenação, renomeação, agrupamento)
- `plano-contas-view`: Refactor da tela de Plano de Contas (remover seleção, adicionar inline actions)
- `theme-system`: Sistema de temas e tokens de cor (correção cross-browser)

## Impact

**Frontend:**
- `src/state/nucleo.ts`: Atualizar `ORDEM_MENU` e registro de vistas
- `src/features/clientes.ts`: Renomear para "Parceiro de Negócios"
- `src/features/negocios.ts`: Renomear para "Negócios e Funil", adicionar grupo
- `src/features/orcamentos.ts`: Adicionar grupo "Comercial"
- `src/features/faturamento.ts`: Adicionar grupo "Financeiro"
- `src/features/despesas.ts` e `src/features/investimentos.ts`: Remover (se aplicável)
- `src/features/financeiro/plano-contas.ts`: Refactor UI (pesquisa + hover actions, remover seleção)
- `src/styles/financeiro.css`: Adicionar estilos para hover actions na árvore
- `src/styles/tokens.css`: Investigar e corrigir media queries de color-scheme para Chrome

**Backend:**
- Sem mudanças (mudanças são puramente de UI/navegação)

**Breaking Changes:**
- Nenhuma (reordenação de menu não quebra funcionalidade)
