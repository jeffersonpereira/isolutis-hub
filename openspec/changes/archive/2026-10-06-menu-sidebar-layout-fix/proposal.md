## Why

A seção "Usando agora" (que mostra presença do usuário e informações da conta) desaparece da tela quando o menu lateral expande com vários itens. O `#nav` não tem limite de altura e cresce indefinidamente, empurrando o `.online` para fora da viewport, tornando impossível visualizar a presença de quem está usando o Hub.

## What Changes

- Adicionar `max-height` + `overflow: auto` ao elemento `#nav` para conter o crescimento do menu e permitir scroll interno
- Reorganizar o layout da `<aside>` para garantir que `.online` (Usando agora) e `.conta` (dados da conta) permaneçam visíveis e fixos no final da sidebar, mesmo quando o menu expande

## Capabilities

### New Capabilities
- `scrollable-sidebar-menu`: Menu lateral com scroll próprio quando itens expandem, mantendo seção de presença sempre visível

### Modified Capabilities
<!-- Nenhuma mudança em capabilities existentes - apenas layout/CSS -->

## Impact

- **Arquivo alterado**: `frontend/src/styles/layout.css` (adição de `max-height` e `overflow: auto` ao `nav`)
- **Afeta**: Sidebar lateral, menu de navegação, seção "Usando agora"
- **Compatibilidade**: Totalmente compatível, afeta apenas CSS/layout sem mudanças no JavaScript ou API
