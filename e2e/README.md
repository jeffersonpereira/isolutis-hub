# E2E Tests com Playwright

Testes end-to-end que validam fluxos críticos do usuário:
- Login → Criar cliente → Criar negócio
- Validação de formulários
- Loading visual
- Acessibilidade
- Sincronização multi-aba

## Setup

### 1. Instalar dependências
```bash
npm install --save-dev @playwright/test
```

### 2. Rodar testes

**Modo headless (CI/CD):**
```bash
npx playwright test
```

**Modo UI (development):**
```bash
npx playwright test --ui
```

**Debug:**
```bash
npx playwright test --debug
```

### 3. Ver relatório
```bash
npx playwright show-report
```

## Testes Inclusos

### `fluxo-critico.spec.ts`

1. **Criar cliente com validação**
2. **Criar negócio com cliente**
3. **Validação de campos obrigatórios**
4. **Loading visual**
5. **Acessibilidade**
6. **Multi-aba sync**

## CI/CD Integration

```yaml
- name: Rodar E2E tests
  run: npx playwright test
```

## Referências

- [Playwright Docs](https://playwright.dev/)
