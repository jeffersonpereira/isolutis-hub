## Context

A aplicação iSolutis Hub usa CSS custom properties (tokens) definidos em `frontend/src/styles/tokens.css` para gerenciar cores em toda a interface. O design system suporta dois temas: light mode (padrão) e dark mode (`@media (prefers-color-scheme: dark)` e `[data-theme="dark"]`).

A paleta atual apresenta cores primárias altamente saturadas (Navy #1B2B4B, Teal #22C3CE) que combinadas com cores de status também saturadas (OK #1f7a4d, Warn #9a6a00) criam fadiga visual. As cores neutras (backgrounds, surfaces, borders) não formam uma progressão harmoniosa.

## Goals / Non-Goals

**Goals:**
- Reduzir saturação de cores primárias, neutras e de status mantendo reconhecibilidade da marca
- Criar progressão harmoniosa entre backgrounds, surfaces e borders
- Otimizar contraste e legibilidade em light e dark modes
- Manter identidade visual (azul-marinho e turquesa como cores principais)
- Aplicar paleta em todas as camadas (componentes, layouts, features)

**Non-Goals:**
- Alterar estructura ou layout de componentes
- Mudar semântica de cores (verde continua sendo OK, vermelho continua sendo Bad)
- Suporte a temas adicionais além de light/dark
- Criar novo design system — apenas refinar a paleta existente

## Decisions

### 1. Estratégia de Dessaturação
**Decisão:** Reduzir saturação em espaço HSL mantendo luminosidade percebida e aumentando levemente a luminância.

**Rationale:** Saturação alta causa fadiga visual sem perder reconhecibilidade. Aumentar luminância ligeiramente melhora contraste e legibilidade.

**Alternativas consideradas:**
- Reduzir apenas em dark mode: Descartado, problema afeta ambos modos
- Mudar para paleta completamente nova: Descartado, perde identidade de marca

### 2. Estrutura de Camadas de Cor
**Decisão:** Manter 4 camadas: (1) Primárias (Navy, Teal), (2) Neutras (BG, Surface, Sunk, Line), (3) Status (OK, Warn, Bad, Info), (4) Accent/Gold.

**Rationale:** Estrutura clara reduz complexidade e facilita manutenção. Cada camada tem propósito específico.

### 3. Paleta Específica (Light Mode)
```css
/* Primárias */
--navy: #1a2d47;              /* de #1B2B4B */
--navy-deep: #0f1b2e;          /* de #111b30 */
--teal: #3b9ca8;               /* de #22C3CE — dessaturação significativa */
--gold: #0d8792;               /* de #0d8792 — mantém, complementa teal */
--gold-soft: #dbf3f5;          /* de #dbf3f5 — mantém */

/* Neutras */
--bg: #f5f7fb;                 /* de #eef1f6 — mais clean */
--surface: #ffffff;            /* mantém branco */
--sunk: #e8ecf2;               /* de #e5eaf1 — ligeiramente mais claro */
--line: #dce4f0;               /* de #d3dbe6 — menos agressivo */

/* Texto e UI */
--ink: #16223b;                /* de #16223b — mantém */
--muted: #56647a;              /* de #56647a — mantém */
--accent: #1a2d47;             /* de #1B2B4B — alinhado com navy */
--accent-ink: #ffffff;         /* mantém branco */

/* Barra (header) */
--bar-a: #1a2d47;              /* de #1B2B4B */
--bar-b: #b5d4d8;              /* de #9fdde2 — dessaturado */

/* Status */
--ok: #4a9d6f;                 /* de #1f7a4d — dessaturado, mais herbal */
--ok-bg: #e9f3ee;              /* de #e1f2e8 — mais claro */
--warn: #b89a3d;               /* de #9a6a00 — dessaturado, mais âmbar */
--warn-bg: #f9f5e5;            /* de #fbefd2 — mais claro */
--bad: #a85d52;                /* de #b0362f — dessaturado, mais terracota */
--bad-bg: #f9ede9;             /* de #f9e1df — mais claro */
--info: #5b8dd9;               /* de #2d5b94 — dessaturado, mais suave */
--info-bg: #e8eef9;            /* de #e1ebf7 — mais claro */
--wa: #3cc37a;                 /* de #128c4a — dessaturado */
--wa-ink: #ffffff;             /* mantém branco */
```

### 4. Paleta Específica (Dark Mode)
```css
/* Primárias */
--bg: #0d1520;                 /* de #0e1729 — mais refinado */
--surface: #151e2f;            /* de #16223b — ligeiramente mais claro */
--sunk: #0f1829;               /* de #111c32 — mais refinado */
--line: #232f44;               /* de #2a3a57 — menos agressivo */

/* Texto */
--ink: #e8edf4;                /* mantém, suave */
--muted: #a0afc4;              /* mantém */

/* Accent */
--accent: #3b9ca8;             /* de #22C3CE — dessaturado */
--accent-ink: #0d1520;         /* de #0e1729 */
--gold: #5bb8c2;               /* de #4fd3dc — dessaturado */
--gold-soft: #123a44;          /* mantém */

/* Barra */
--bar-a: #3b9ca8;              /* de #22C3CE */
--bar-b: #3e556f;              /* de #33506e — ligeiramente mais claro */

/* Status */
--ok: #6fd19f;                 /* de #6fd19f — mantém (já dessaturado) */
--ok-bg: #16352a;              /* mantém */
--warn: #d9b860;               /* de #f0c569 — dessaturado */
--warn-bg: #3a2f14;            /* mantém */
--bad: #d98a7f;                /* de #f19189 — dessaturado */
--bad-bg: #3d1c1b;             /* mantém */
--info: #9cc2f0;               /* mantém (já dessaturado) */
--info-bg: #1a2d47;            /* mantém */
--wa: #5fd1a8;                 /* de #3cc37a — dessaturado */
--wa-ink: #07210f;             /* mantém */
```

### 5. Validação de Contraste
**Decisão:** Verificar WCAG AA (4.5:1 para texto) em todas as combinações críticas (text on background, text on surface, etc).

**Rationale:** Paleta dessaturada pode reduzir contraste — validação garante acessibilidade.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Alteração visual perceptível** poderia desconfortar usuários acostumados com paleta anterior | Deploy gradualmente; coletar feedback; rollback disponível se necessário |
| **Perda de reconhecibilidade da marca** (turquesa muito dessaturado) | Validar que azul-marinho e turquesa dessaturados ainda são reconhecíveis; testar com stakeholders de marca |
| **Validação visual complexa** — cores afetam todos os componentes | Criar checklist de componentes para validação; automatizar testes de contraste onde possível |
| **Dark mode pode ficar muito escuro** com backgrounds refinados | Validar que backgrounds dark não causam fadiga; testar em luminosidade ambiente vária |
| **Implementação incompleta** — alguns componentes antigos podem ter hard-coded colors | Audit de código para hard-coded colors; substituir por tokens CSS |

## Migration Plan

1. **Preparação** (validação prévia):
   - Audit de componentes CSS para encontrar cores hard-coded
   - Captura de screenshots da paleta atual para comparação

2. **Atualização**:
   - Atualizar `frontend/src/styles/tokens.css` com nova paleta
   - Verificar que SCSS/CSS em `base.css`, `components.css`, `layout.css`, etc. usam tokens

3. **Validação Visual**:
   - Testar light mode e dark mode em navegadores (Chrome, Firefox, Safari)
   - Validar cada seção: dashboard, parceiros, negócios, financeiro, etc.
   - Validar componentes comuns: buttons, inputs, headers, cards, tables
   - Verificar modo responsivo (mobile, tablet)

4. **Teste de Contraste**:
   - Rodar verificador WCAG em páginas críticas
   - Garantir p95 contraste ≥ 4.5:1

5. **Rollback** (se necessário):
   - Reverter `tokens.css` para commit anterior
   - Limpar cache do navegador
   - Re-testar

6. **Deploy**:
   - Fazer commit com nova paleta
   - Deploy para staging
   - Validação final com stakeholders
   - Deploy para produção (sem downtime — apenas atualização CSS)

## Open Questions

- Logo da marca será re-estilizada? (Atualmente PNG — sem mudança necessária)
- Há componentes antigos com hard-coded colors que precisam audit?
- Comunicação com usuários sobre mudança visual — necessária?
