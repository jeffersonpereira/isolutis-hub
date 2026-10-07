## 1. Componente

- [ ] 1.1 Criar `ui/combobox.ts` (render + montagem de eventos; input visível + campo oculto com o valor)
- [ ] 1.2 Filtro normalizado (acento/caixa) por rótulo e código, com limite de itens
- [ ] 1.3 Teclado (setas, Enter, Esc, Tab) e ARIA (combobox, listbox, aria-activedescendant)
- [ ] 1.4 Estilos pelos tokens do design system (claro/escuro, foco, vazio)
- [ ] 1.5 Testes unitários do filtro e das interações principais

## 2. Adoção

- [ ] 2.1 Substituir o select de instituição em `contas-bancarias.ts` (incluindo edição com valor atual)
- [ ] 2.2 Aplicar em município e parceiro (`parceiros/campos.ts`, `titulos.ts`)
- [ ] 2.3 Aplicar na conta do plano de contas do título (respeitando o filtro por natureza)

## 3. Validação

- [ ] 3.1 Verificar manualmente em gaveta/modal, teclado e tema escuro; rodar testes do front e revisar o diff
