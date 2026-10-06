## Context

O iSolutis Hub usa um sistema de registro de vistas (módulos) que se organizam no menu via:
- **ORDEM_MENU**: Array que define ordem visual dos itens
- **registrarVista()**: Cada módulo registra com `id`, `nome`, e opcionalmente `grupo`
- **renderMenu()**: Agrupa itens por `grupo` em submenus recolhíveis

O Plano de Contas renderiza uma árvore hierárquica com 3 níveis (1 · 1.01 · 1.01.001). Atualmente força seleção de nó antes de permitir edição, o que é ineficiente.

O sistema de cores usa `prefers-color-scheme` media query, mas Chrome renderiza significativamente mais escuro que Brave/Firefox, sugerindo issue de color-space ou detecção incorreta de preferência.

## Goals / Non-Goals

**Goals:**
1. Reorganizar menu para refletir fluxo comercial (novo grupo "Comercial")
2. Melhorar usabilidade do Plano de Contas removendo seleção obrigatória
3. Corrigir renderização de cores no Chrome mantendo compatibilidade com outros navegadores
4. Manter compatibilidade total com mobile (hover actions degradam gracefully em touch)

**Non-Goals:**
- Remover funcionalidades de CRUD do Plano de Contas
- Refatorar sistema de themes globalmente (só corrigir issue Chrome)
- Alterar estrutura de dados ou backend
- Implementar busca fuzzy avançada (exato/substring é suficiente)

## Decisions

### 1. Reorganização de Menu
**Decision:** Atualizar `ORDEM_MENU` e atributos de `grupo` em cada vista, sem criar novos módulos.

**Rationale:** 
- Todas as mudanças cabem em metadados de vista
- Não requer mudanças arquiteturais
- Sistema de grupos já suporta submenu recolhível

**Alternatives Considered:**
- A: Criar novo módulo "funil" separado → Descartado, "Negócios e Funil" é um único módulo
- B: Remover "Despesas" e "Investimentos" completamente vs. mover para Financeiro → Opção A (remover) para limpar UI

**Implementação:**
```typescript
// src/state/nucleo.ts
const ORDEM_MENU = [
  "painel", 
  "parceiro-negocio",      // clientes → parceiro de negócios
  "comercial-negocios",    // novo grupo
  "comercial-orcamentos",  // novo grupo
  "projetos", "tarefas", "produtos",
  "fin-plano", "fin-contas", "fin-bancarias", 
  "fin-parceiros", "fin-titulos", "fin-fluxo", "fin-faturamento",  // faturamento move pra cá
  "equipe"
];

// src/features/clientes.ts
registrarVista({ 
  id: "clientes",           // id não muda (RLS setup)
  nome: "Parceiro de Negócios",  // nome muda
  // grupo removido → aparece no menu principal
  ...
});

// src/features/negocios.ts
registrarVista({ 
  id: "negocios",
  nome: "Negócios e Funil",  // nome muda
  grupo: "Comercial",        // novo grupo
  ...
});
```

### 2. Plano de Contas - Inline Editing + Pesquisa

**Decision:** Renderizar ações (✏️ 🗑️ +) inline ao lado de cada conta, reveladas no hover. Remover seleção de nó. Adicionar input pesquisa.

**Rationale:**
- Hover reveal economiza espaço, não polui tela em repouso
- Inline actions reduzem cliques (não precisa selecionar + clicar botão do topo)
- Pesquisa filtra árvore mantendo hierarquia (não "lineariza")

**Alternatives Considered:**
- A: Context menu (right-click) → Menos discoverable, não mobile-friendly
- B: Sempre visível (não hover) → Tela ocupada, menos elegante
- C: Modal de seleção → Adiciona modal extra (mais cliques)

**Implementação:**
```html
<!-- Padrão atual (problema: força seleção) -->
<li role="treeitem">
  <div class="tree-row" data-act="selecionarConta">
    <span>1 Receita</span> <!-- seleciona nó -->
  </div>
</li>

<!-- Novo padrão (solução: hover actions) -->
<li role="treeitem">
  <div class="tree-row">
    <button class="tree-caret" data-act="alternarNo">›</button>
    <span class="tree-cod">1</span>
    <span class="tree-nome">Receita</span>
    <span class="tree-pills">
      <span class="pill">Sintética</span>
      <span class="pill">Receita</span>
    </span>
    <!-- Ações aparecem no hover -->
    <span class="tree-actions hidden-on-empty">
      <button data-act="editarConta" aria-label="Editar">✏️</button>
      <button data-act="excluirConta" aria-label="Excluir">🗑️</button>
      <button data-act="novaContaFilha" aria-label="Adicionar filha" 
              ${temFilhas ? "" : "disabled"}>+</button>
    </span>
  </div>
</li>
```

**CSS:**
```css
.tree-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.tree-actions {
  display: none;         /* hidden by default */
  margin-left: auto;     /* push to right */
  gap: 4px;
}

.tree-row:hover .tree-actions {
  display: flex;         /* reveal on hover */
}

.tree-row:focus .tree-actions {
  display: flex;         /* reveal on keyboard focus */
}

/* Accessibility: mostrar em high contrast mode */
@media (prefers-forced-colors: active) {
  .tree-actions {
    display: flex !important;
  }
}
```

**Input Pesquisa:**
```html
<div class="head">
  <div>
    <h1>Plano de Contas</h1>
    <input type="search" placeholder="Pesquisar contas..." 
           data-busca="buscaPlano" aria-label="Pesquisar contas por código ou nome">
  </div>
  <div class="tools">
    <!-- Botão "Nova" apenas se nenhuma conta selecionada (sem seleção = primeira cria raiz) -->
    <button class="btn primary" data-act="novaConta">+ Nova Conta Raiz</button>
  </div>
</div>
```

Filtragem em `main.ts` (padrão existente):
```typescript
// Ao digitar no input, refazer render()
// renderMenu() já filtra pela lista de vistas baseado em ui.buscaPlano
```

### 3. Chrome Color Issue

**Decision:** Adicionar fallback explícito em `tokens.css` e investigar se Chrome está forçando dark mode.

**Rationale:**
- `:not([data-theme="light"])` pode não estar sendo respeitado em Chrome
- `prefers-color-scheme` pode ser detectado incorretamente
- Adicionar `color-space: srgb` força rendering consistente

**Alternatives Considered:**
- A: Desabilitar `prefers-color-scheme` completamente → Perde sync com SO
- B: Usar apenas `[data-theme]` → Rompe com preferência do SO
- C: Adicionar media query específica para Chrome → Não existe seletor browser-specific em CSS

**Implementação:**
```css
/* tokens.css - adicionar ao topo */
:root {
  color-space: srgb;  /* Force sRGB color space em todos browsers */
  --navy:#1a2d47; --navy-deep:#0f1b2e; /* ... cores light mode ... */
}

/* Light mode: remover :not() que pode estar falhando em Chrome */
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    /* mesmo conteúdo, sem :not([data-theme="light"]) */
  }
}

/* Dark mode: ser mais específico */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* cores dark mode */ }
}

/* Explicit dark theme: sempre aplicar (sem media query) */
:root[data-theme="dark"] { /* cores dark mode */ }
```

**Investigação necessária:**
1. Verificar se Chrome está detectando `prefers-color-scheme: dark` quando SO está em light
2. Testar com `color-space: srgb` vs. sem
3. Confirmar se issue desaparece após ajuste

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Hover actions em mobile** | Actions não aparecem no touch. Mitigar: adicionar touch handlers se necessário, ou aceitar UX degradada em mobile (80/20 rule) |
| **Pesquisa pode ser lenta em grandes árvores** | Mitigar: implementar debounce (300ms) no input, ou lazy-render results se árvore > 500 nós |
| **Remover "Despesas" rompe links internos** | Mitigar: validar se há links em outros módulos apontando para "despesas"; se houver, fazer redirect em place holder ou documentar breaking change |
| **Chrome color fix pode não funcionar** | Mitigar: pode ser bug específico de versão do Chrome; adicionar issue tracking e testar em próxima versão do Chrome |
| **ORDEM_MENU fica mais longa** | Mitigar: está bem documentada, adicionar comentários explicativos |

## Migration Plan

**Deployment:**
1. Deploy da mudança de menu é instantâneo (metadados em TypeScript)
2. Deploy do Plano de Contas requer refactor da renderização (compatível para trás, sem dados quebrados)
3. Deploy de CSS é backward-compatible (novos estilos não afetam componentes antigos)
4. Nenhum schema de BD muda

**Rollback:**
- Git revert suficiente (nenhuma migração de dados)
- Revert CSS remove apenas hover actions (visual graceful)

**Testing:**
- E2E: Verificar menu renderiza em ordem correta com novos nomes
- E2E: Testar plano de contas em Chrome, Firefox, Brave
- Manual: Confirmar cores Chrome parecem iguais a Brave

## Open Questions

1. **Despesas e Investimentos:** Remover menu ou remover módulo completamente? Há dados dependentes?
2. **Mobile UX para hover actions:** Aceitar degradação de UX em touch, ou implementar long-press fallback?
3. **Performance da pesquisa:** Qual é o tamanho esperado da árvore de contas? (para decidir se precisa debounce)
4. **Chrome color:** Qual versão do Chrome está afetada? Pode ser bug que já foi corrigido?
