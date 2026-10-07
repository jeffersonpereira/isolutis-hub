## Why

Os campos de seleção são `<select>` nativos: com listas longas (instituições financeiras, municípios, parceiros, contas do plano) o usuário não consegue digitar para localizar o item. Na tela de conta bancária isso impede achar a instituição pelo nome ou código.

## What Changes

- Novo componente de UI "combobox pesquisável" (filtro por digitação, navegação por teclado, padrão ARIA combobox + listbox), reutilizável e com o mesmo contrato de formulário dos campos atuais (`name`, valor escolhido lido por `fv`).
- Aplicar primeiro em "Instituição financeira" (conta bancária); depois em município, parceiro e conta do plano de contas no título.
- Busca sem diferenciar acentos/maiúsculas, por código e por nome.

## Capabilities

### New Capabilities
- `combobox-pesquisavel`: seleção de um item de lista por digitação, com teclado, acessibilidade e estados (vazio, sem resultados, desabilitado).

### Modified Capabilities
<!-- nenhuma: o comportamento das telas muda só na forma de escolher o item -->

## Impact

- Frontend: novo `ui/combobox.ts` (+ estilos nos tokens do design system), `ui/campos.ts`, `features/financeiro/contas-bancarias.ts`, depois `parceiros/campos.ts` e `titulos.ts`.
- Sem mudança de API ou de banco.
