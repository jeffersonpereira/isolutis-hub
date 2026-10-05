# Padrão de Refatoração - Features

Guia para aplicar o padrão genérico `salvar-helper.ts` + `formulario-helper.ts` em todas as features.

## Objetivo

Eliminar duplicação de código (`salvar`, `validar`, `carregar`, `fechar`) em:
- `clientes.ts`
- `negocios.ts`
- `orcamentos.ts`
- `projetos.ts`
- `tarefas.ts`
- `faturamento.ts`
- `produtos.ts`

## Padrão Atual (Antes)

```typescript
$("[data-salvar]", L)?.addEventListener("click", async (e) => {
  const botao = e.target as HTMLButtonElement;
  const nome = fv(f, "nome");

  // Validação manual
  if (!nome) return void toast("Informe o nome.");

  botao.disabled = true;
  
  // API call
  const ok = await tentar(() =>
    novo
      ? api.clientes.criar({ nome })
      : api.clientes.atualizar(id, { nome, versao })
  );
  
  if (!ok) {
    botao.disabled = false;
    return;
  }
  
  // Recarregar + fechar
  await recarregar("clientes");
  toast("Salvo");
  fechar();
});
```

**Problemas:**
- 150+ linhas duplicadas em cada feature
- Lógica de validação espalhada
- Sem feedback visual (spinner)
- Difícil manutenção

## Padrão Novo (Depois)

```typescript
import { salvarComValidacao } from "@/ui/salvar-helper";

$("[data-salvar]", L)?.addEventListener("click", async () => {
  const botao = e.target as HTMLButtonElement;

  await salvarComValidacao({
    form: f,
    botaoSalvar: botao,
    validar: () => {
      const erros: Record<string, string> = {};
      if (!fv(f, "nome")) erros["nome"] = "Informe o nome.";
      return Object.keys(erros).length ? erros : null;
    },
    operacao: () => tentar(() =>
      novo
        ? api.clientes.criar({ nome: fv(f, "nome") })
        : api.clientes.atualizar(id, { nome: fv(f, "nome"), versao })
    ),
    recarregarRecurso: "clientes",
    fechar,
  });
});
```

**Benefícios:**
- -70 LOC duplicadas
- Spinner automático
- Padrão consistente
- Fácil refatoração

## Como Refatorar uma Feature

### Passo 1: Adicionar importação

```typescript
import { salvarComValidacao } from "@/ui/salvar-helper";
import { melhorarFormulario } from "@/ui/acessibilidade";
```

### Passo 2: Melhorar acessibilidade do formulário

No `montar` da gaveta:

```typescript
montar: (f, fechar, L) => {
  melhorarFormulario(f);
  // resto do código...
}
```

### Passo 3: Extrair validação

```typescript
const validar = () => {
  const erros: Record<string, string> = {};
  
  if (!fv(f, "nome")) erros["nome"] = "Informe o nome.";
  if (!fv(f, "email")) erros["email"] = "Informe o e-mail.";
  // ... mais validações
  
  return Object.keys(erros).length ? erros : null;
};
```

### Passo 4: Extrair operação de salvar

```typescript
const operacao = () => tentar(() =>
  novo
    ? api.recurso.criar({ ...dados })
    : api.recurso.atualizar(id, { ...dados, versao })
);
```

### Passo 5: Usar helper

```typescript
await salvarComValidacao({
  form: f,
  botaoSalvar: botao,
  validar,
  operacao,
  recarregarRecurso: "recurso",
  fechar,
  onSucesso: (resultado) => {
    // Callback especial, ex: mostrar senha gerada
  },
});
```

## Checklist por Feature

### Clientes
- [ ] Importar helper
- [ ] Melhorar acessibilidade do formulário
- [ ] Extrair validação
- [ ] Usar `salvarComValidacao`
- [ ] Testar com Playwright

### Negócios
- [ ] (mesmos passos)
- [ ] Atenção: validação customizada (status, etapa)

### Orcamentos
- [ ] (mesmos passos)
- [ ] Atenção: itens (linhas, validação de soma)

### Projetos
- [ ] (mesmos passos)
- [ ] Atenção: relatório de entrega (complexo)

### Tarefas
- [ ] (mesmos passos)
- [ ] Atenção: drag-and-drop não afeta salvar

### Faturamento
- [ ] (mesmos passos)
- [ ] Atenção: cálculos automáticos

### Produtos
- [ ] (mesmos passos)
- [ ] Atenção: simples, referência

## Exemplo Completo: Clientes

**Antes:** 200+ linhas em `formCliente()`

**Depois:**
```typescript
function formCliente(c?: Cliente): void {
  const novo = !c;
  
  abrirGaveta({
    titulo: c ? c.nome : "Novo cliente",
    corpo: html`...`,
    rodape: html`...`,
    montar: (f, fechar, L) => {
      melhorarFormulario(f);
      
      const validar = () => {
        const erros: Record<string, string> = {};
        if (!fv(f, "nome")) erros["nome"] = "Informe o nome.";
        return Object.keys(erros).length ? erros : null;
      };
      
      const operacao = () => {
        const lido = lerCamposDoParceiro(f, "cliente");
        if (!lido) throw new Error("Validação falhou");
        const corpo = Object.fromEntries(
          Object.entries(lido).filter(([k]) => k !== "tipo_pessoa" && k !== "papeis")
        );
        return tentar(() =>
          novo
            ? api.clientes.criar(corpo)
            : api.clientes.atualizar(c.id, { ...corpo, versao: c.versao })
        );
      };
      
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        await salvarComValidacao({
          form: f,
          botaoSalvar: e.target as HTMLButtonElement,
          validar,
          operacao,
          recarregarRecurso: "clientes",
          fechar,
        });
      });
      
      // Restante (callbacks especiais, delete, novo-negocio)
    },
  });
}
```

**Resultado:** -50 LOC, +100% consistência

## Testing

Após refatorar, rodar E2E para cada feature:

```bash
# Modo UI (ver o que está acontecendo)
npm run test:e2e:ui -- --grep "clientes"

# Ou full
npm run test:e2e
```

## Timeline

```
Dia 1: Clientes + Negocios
Dia 2: Orcamentos + Projetos
Dia 3: Tarefas + Faturamento + Produtos
Dia 4: Review + fixes
Dia 5: E2E full + CI
```

## Referências

- `frontend/src/ui/salvar-helper.ts` — Implementação do helper
- `frontend/src/ui/acessibilidade.ts` — WCAG utilities
- `frontend/src/features/equipe.ts` — Exemplo de refatoração completa
- `e2e/tests/fluxo-critico.spec.ts` — Testes validando padrão

## Commit Message Template

```
refactor: <feature> usando padrão salvarComValidacao

- Usar salvarComValidacao() em lugar de handlers manuais
- Adicionar acessibilidade (labels, aria-*)
- Validação centralizada em função
- -XX LOC duplicado, loading visual automático

Testes: OK (manual / E2E)
```
