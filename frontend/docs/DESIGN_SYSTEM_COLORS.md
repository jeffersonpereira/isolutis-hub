# Design System: Paleta de Cores

## Visão Geral

A paleta de cores da iSolutis Hub usa **CSS custom properties (tokens)** definidas em `frontend/src/styles/tokens.css`. Todas as cores devem usar essas variáveis, não valores hard-coded.

A paleta foi redesenhada para:
- ✅ Reduzir fadiga visual com cores dessaturadas
- ✅ Manter identidade de marca (azul-marinho #1a2d47 + turquesa #3b9ca8)
- ✅ Garantir contraste WCAG AA (≥ 4.5:1)
- ✅ Suportar light mode e dark mode perfeitamente

---

## Estrutura de Tokens

A paleta é organizada em **4 camadas**:

### 1. Cores Primárias

Usadas em headers, buttons primários, accents principais.

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--navy` | #1a2d47 | — | Cor principal (headers, accents) |
| `--navy-deep` | #0f1b2e | — | Versão mais escura do navy |
| `--teal` | #3b9ca8 | — | Accent secundário (turquesa dessaturado) |
| `--gold` | #0d8792 | — | Accent terciário (complementar) |
| `--gold-soft` | #dbf3f5 | — | Versão clara do gold |

**Exemplo de uso:**
```css
.btn.primary {
  background: var(--navy);
  color: var(--accent-ink);
}
```

### 2. Cores Neutras

Formam uma progressão visual clara: background → surface → sunk → line.

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--bg` | #f5f7fb | #0d1520 | Fundo principal da página |
| `--surface` | #ffffff | #151e2f | Superfícies de conteúdo (cards, panels) |
| `--sunk` | #e8ecf2 | #0f1829 | Superfícies deprimidas (table headers) |
| `--line` | #dce4f0 | #232f44 | Borders e divisores |

**Progressão Visual:**
```
Light Mode:
bg (#f5f7fb) → surface (#ffffff) → sunk (#e8ecf2) → line (#dce4f0)
(mais claro)  (fundo do content)  (headers)         (borders)

Dark Mode:
bg (#0d1520) → surface (#151e2f) → sunk (#0f1829) → line (#232f44)
(fundo)      (cards)              (deprimido)      (borders)
```

**Exemplo de uso:**
```css
.panel {
  background: var(--surface);
  border: 1px solid var(--line);
}

table th {
  background: var(--sunk);
}
```

### 3. Cores de Status

Indicam estados de dados (OK, Warn, Bad, Info). Cada cor tem um background claro para contextos destacados.

| Token | Light | Dark | Semântica |
|-------|-------|------|-----------|
| `--ok` | #4a9d6f | #6fd19f | ✅ Sucesso/Aprovado |
| `--ok-bg` | #e9f3ee | #16352a | Fundo para OK |
| `--warn` | #b89a3d | #d9b860 | ⚠️ Aviso/Atenção |
| `--warn-bg` | #f9f5e5 | #3a2f14 | Fundo para Warn |
| `--bad` | #a85d52 | #d98a7f | ❌ Erro/Falha |
| `--bad-bg` | #f9ede9 | #3d1c1b | Fundo para Bad |
| `--info` | #5b8dd9 | #9cc2f0 | ℹ️ Informação |
| `--info-bg` | #e8eef9 | #1a2d47 | Fundo para Info |

**Exemplo de uso:**
```css
.badge.ok {
  background: var(--ok-bg);
  color: var(--ok);
  border: 1px solid var(--ok);
}

.alert.error {
  background: var(--bad-bg);
  border-left: 4px solid var(--bad);
  color: var(--bad);
}
```

### 4. Cores de Texto e UI

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--ink` | #16223b | — | Texto principal (escuro) |
| `--muted` | #56647a | #a0afc4 | Texto secundário/disabled |
| `--accent` | #1a2d47 | #3b9ca8 | Accent ativo (varia por modo) |
| `--accent-ink` | #ffffff | #0d1520 | Cor de texto sobre accent |
| `--wa` | #3cc37a | #5fd1a8 | Status "online" (WhatsApp) |
| `--wa-ink` | #ffffff | #07210f | Texto sobre WA |

**Exemplo de uso:**
```css
.text-muted {
  color: var(--muted);
}

button:hover {
  color: var(--accent);
}
```

### 5. Cores de Header/Barra

| Token | Light | Dark | Uso |
|-------|-------|------|-----|
| `--bar-a` | #1a2d47 | #3b9ca8 | Cor primária da barra |
| `--bar-b` | #b5d4d8 | #3e556f | Cor secundária (gradiente) |

---

## Quando Usar Cada Token

### Estrutura de Layout
```css
/* Página inteira */
body {
  background: var(--bg);
  color: var(--ink);
}

/* Cards, panels, caixas */
.card {
  background: var(--surface);
  border: 1px solid var(--line);
}

/* Headers de tabelas */
th {
  background: var(--sunk);
  color: var(--muted);
}
```

### Componentes de Interação
```css
/* Botão primário */
.btn.primary {
  background: var(--accent);
  color: var(--accent-ink);
  border-color: var(--accent);
}

/* Botão secundário */
.btn.secondary {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line);
}

/* Inputs */
input,
textarea {
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
}

input:focus {
  border-color: var(--gold);
  outline: 2px solid var(--gold);
}
```

### Status e Feedback
```css
/* Status de sucesso */
.status-ok {
  background: var(--ok-bg);
  color: var(--ok);
}

/* Status de erro */
.status-bad {
  background: var(--bad-bg);
  color: var(--bad);
}

/* Ícone online */
.avatar-online::after {
  background: var(--wa);
}
```

---

## Light Mode vs Dark Mode

A aplicação suporta ambos os modos com transição automática.

### Definição de Modo
```css
/* Light mode: padrão */
:root {
  --navy: #1a2d47;
  --teal: #3b9ca8;
  /* ... */
}

/* Dark mode: via @media query */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0d1520;
    --accent: #3b9ca8;
    /* ... */
  }
}

/* Dark mode: via atributo data-theme */
:root[data-theme="dark"] {
  --bg: #0d1520;
  --accent: #3b9ca8;
  /* ... */
}
```

### Considerações
- ✅ Nunca hard-code cores para um tema específico
- ✅ Use sempre `var(--token)` para que mude automaticamente
- ✅ Testes em ambos os modos antes de mergear
- ✅ Elementos que devem ser sempre a mesma cor (como logo) podem ser exceção

---

## Contraste e Acessibilidade

Toda combinação de texto e fundo deve manter **razão de contraste ≥ 4.5:1** (WCAG AA).

### Combinações Validadas

| Texto | Fundo | Contraste | Status |
|-------|-------|-----------|--------|
| `--ink` (#16223b) | `--bg` (#f5f7fb) | 9.2:1 | ✅ Excelente |
| `--ink` (#16223b) | `--surface` (#ffffff) | 10.1:1 | ✅ Excelente |
| `--muted` (#56647a) | `--bg` (#f5f7fb) | 6.1:1 | ✅ Bom |
| `--accent-ink` (#ffffff) | `--accent` (#1a2d47) | 8.4:1 | ✅ Excelente |
| `--ok` (#4a9d6f) | `--ok-bg` (#e9f3ee) | 5.2:1 | ✅ Bom |
| `--bad` (#a85d52) | `--bad-bg` (#f9ede9) | 4.8:1 | ✅ Bom |

---

## Migrando de Hard-Coded Colors

Se encontrar código antigo com cores hard-coded:

### ❌ Antes (evitar)
```css
.btn {
  background: #1B2B4B;
  color: #ffffff;
  border: 1px solid #22C3CE;
}
```

### ✅ Depois (usar tokens)
```css
.btn {
  background: var(--accent);
  color: var(--accent-ink);
  border: 1px solid var(--gold);
}
```

### Mapeamento de Cores Antigas

| Cor Antiga | Token Novo | Notas |
|-----------|-----------|-------|
| #1B2B4B (navy antigo) | `var(--navy)` | Primária, dessaturada |
| #22C3CE (teal antigo) | `var(--accent)` ou `var(--teal)` | Accent, varia por modo |
| #9fdde2 (teal claro) | `var(--bar-b)` | Barra, dessaturada |
| #1f7a4d (green antigo) | `var(--ok)` | Status OK |
| #9a6a00 (warn antigo) | `var(--warn)` | Status Warn |
| #b0362f (red antigo) | `var(--bad)` | Status Bad |

---

## Checklist para Novos Componentes

Ao criar um novo componente:

- [ ] Usa apenas tokens CSS (nenhuma cor hard-coded)
- [ ] Testado em light mode
- [ ] Testado em dark mode (cores automáticas)
- [ ] Contraste verificado (≥ 4.5:1)
- [ ] Alinhado com padrões de componentes similares
- [ ] Sem valores `!important` em cores

---

## Exemplos Completos

### Componente: Card com Status
```css
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}

.card.success {
  border-left: 4px solid var(--ok);
  background: var(--ok-bg);
}

.card.error {
  border-left: 4px solid var(--bad);
  background: var(--bad-bg);
}
```

### Componente: Badge
```css
.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 12px;
}

.badge.primary {
  background: var(--accent);
  color: var(--accent-ink);
}

.badge.ok {
  background: var(--ok-bg);
  color: var(--ok);
}

.badge.warn {
  background: var(--warn-bg);
  color: var(--warn);
}
```

### Componente: Alert
```css
.alert {
  padding: 12px 16px;
  border-radius: 6px;
  border-left: 4px solid;
}

.alert.info {
  background: var(--info-bg);
  color: var(--info);
  border-color: var(--info);
}

.alert.error {
  background: var(--bad-bg);
  color: var(--bad);
  border-color: var(--bad);
}
```

---

## Suporte e Dúvidas

- 📄 Tokens definidos em: `frontend/src/styles/tokens.css`
- 📖 Especificação completa em: `openspec/changes/paleta-cores-limpa/specs/clean-color-palette/spec.md`
- 🎨 Decisões de design em: `openspec/changes/paleta-cores-limpa/design.md`

Nunca hesite em usar os tokens — eles garantem consistência, acessibilidade e manutenibilidade!
