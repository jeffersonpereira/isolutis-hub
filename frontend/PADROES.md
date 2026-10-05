# Padrões de Código - Frontend Hub

## 1. Validação de Formulários

Use `validators.ts` e `schemas/entidades.ts` para centralizar regras de validação.

**Exemplo:**

```typescript
import { schema, regras } from "@/ui/validators";

const meuSchema = schema<{ nome: string; email: string }>({
  nome: campo("nome", [
    regras.obrigatorio("Nome"),
    regras.minLength(3, "Nome"),
  ]),
  email: campo("email", [
    regras.obrigatorio("E-mail"),
    regras.email(),
  ]),
});

const resultado = meuSchema.parse(dados);
if (!resultado.sucesso) {
  console.log("Erros:", resultado.erros);
} else {
  console.log("Dados validados:", resultado.dados);
}
```

**Benefícios:**
- Validações reutilizáveis entre features
- Fácil adicionar novas regras
- Tipo-safe com TypeScript

## 2. CRUD Genérico

Use `crud-helper.ts` para reduzir duplicação entre features similar (Clientes, Negócios, Produtos, etc).

**Exemplo (próxima refatoração):**

```typescript
setupCrud({
  recurso: "clientes",
  renderizarLista: (items) => html`<table>...</table>`,
  renderizarFormulario: (item) => ({
    titulo: item ? item.nome : "Novo cliente",
    corpo: html`...`,
    rodape: html`<button data-salvar>Salvar</button>`,
  }),
  aoSalvar: (item, isNovo) => isNovo 
    ? api.clientes.criar(item)
    : api.clientes.atualizar(item.id, item),
  aoSucesso: (item) => console.log("Salvo:", item),
});
```

**Benefícios:**
- Menos código repetido
- Padrão consistente entre features
- Fácil manutenção

## 3. Tratamento de Erros

Use `tentar()` para operações assíncronas com erro automático:

```typescript
const resultado = await tentar(() => api.usuarios.criar(dados));
if (resultado) {
  // Sucesso - erro foi automaticamente mostrado se falhou
  fechar();
}
```

## 4. Estado Global

Dados são armazenados em `estado.ts` (leitura/escrita compartilhada).

**Regra:** Sempre recarregar dados após modificações via `recarregar()`:

```typescript
const ok = await tentar(() => api.clientes.atualizar(id, dados));
if (ok) {
  await recarregar("clientes");
}
```

## 5. Segurança

### Passwords em Formulários
- Use timeout automático (5s) para limpar da DOM
- Exemplo: `backend/src/features/equipe.ts:114-123`

### Validação de Entrada
- Sempre validar no formulário antes de enviar
- Backend valida novamente (defesa em profundidade)

### HTML Template
- Use `html` template para escapar valores automaticamente
- Explicitamente usar `raw()` apenas para HTML controlado

## 6. WebSocket em Tempo Real

Mudanças via WebSocket disparam `recarregar()` automático.
Implementado em `state/realtime.ts`.

## 7. Próximas Refatorações

- [ ] Aplicar `crud-helper` em `clientes.ts`, `negocios.ts`, `orcamentos.ts`
- [ ] Aplicar schemas de validação em todas features
- [ ] Adicionar E2E tests com Playwright
- [ ] Adicionar unit tests para lógica de domínio

## Checklist para Nova Feature

- [ ] Criar schema de validação em `schemas/entidades.ts`
- [ ] Usar `html` template para segurança
- [ ] Registrar vista em `registrarVista()`
- [ ] Registrar ações em `registrarAcao()`
- [ ] Usar `recarregar()` após modificações
- [ ] Tratar erros com `tentar()`
- [ ] Adicionar testes (próxima sprint)
