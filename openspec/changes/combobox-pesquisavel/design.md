## Context

Telas são HTML por template (`html\`\``) com ações por `data-act` e formulários lidos por `fv(form, name)`. Não há componente de combobox; `ui/paleta.ts` já usa o padrão ARIA combobox/listbox (referência de teclado e foco). Listas atuais são pequenas o suficiente para vir inteiras do servidor.

## Goals / Non-Goals

**Goals:**
- Filtrar por digitação, escolher por mouse/teclado, leitor de tela anunciando resultados.
- Drop-in no lugar do `sel(...)`: um `<input type="hidden" name=...>` guarda o valor, de modo que `fv` e a validação atuais continuam funcionando.

**Non-Goals:**
- Busca assíncrona no servidor (listas continuam carregadas inteiras; pode vir depois).
- Seleção múltipla.

## Decisions

- **Componente próprio, sem biblioteca**: o projeto é vanilla TS com templates; uma dependência nova não se justifica. Alternativa: `<input list>` + `<datalist>` — descartada por permitir texto livre sem valor, estilo não controlável e suporte de acessibilidade inconsistente.
- **Valor em campo oculto + input visível**: mantém o contrato de formulário e a validação "campo obrigatório".
- **Filtro local normalizado** (sem acento, minúsculas) por texto e código; limite de itens renderizados para listas grandes.
- **Estilo pelos tokens do design system** (cores, foco, tema claro/escuro).

## Risks / Trade-offs

- [Regressão de foco/teclado em gaveta/modal] → testes de interação e checagem manual nas gavetas.
- [Texto digitado sem escolher item] → ao sair do campo, restaurar o rótulo do item selecionado ou limpar; nunca enviar texto livre.
