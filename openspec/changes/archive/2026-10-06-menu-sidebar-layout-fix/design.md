## Context

A barra lateral (`<aside>`) usa flexbox com `height: 100vh` (altura total da viewport). Contém:
1. `.brand` (logo)
2. `nav#nav` (menu de navegação) - **SEM limite de altura**
3. `.online` (presença do usuário) - posicionado com `margin-top: auto`
4. `.sync` (status de sincronização)
5. `.conta` (informações da conta e botões)

Quando o menu expande (ex: grupo Financeiro com 5 itens filhos), o `nav` cresce indefinidamente, empurrando `.online` para fora da viewport, tornando-o invisível.

## Goals / Non-Goals

**Goals:**
- Permitir que o `nav` faça scroll interno quando expandido
- Manter `.online` (Usando agora) sempre visível na sidebar
- Manter `.conta` sempre visível
- Preservar responsividade em mobile
- Não quebrar nenhuma funcionalidade existente

**Non-Goals:**
- Reduzir o tamanho da fonte do menu
- Colapsar itens do menu automaticamente
- Mudar a ordem dos elementos na sidebar
- Implementar virtualization ou lazy-loading do menu

## Decisions

### Decisão 1: Adicionar `max-height` + `overflow: auto` ao `nav`
**Escolha**: Limitar altura do `nav` com `max-height: calc(100vh - X)` onde X é o espaço reservado para brand, sync, online, conta + gaps.

**Rationale**: 
- Simples e sem dependência de JavaScript
- Compatível com todos os navegadores (inclusive Chrome)
- Permite scroll nativo dentro do menu
- Preserva a experiência do usuário

**Alternativas consideradas**:
- `flex: 1` + `overflow: auto`: Mais simples, mas não reserva espaço garantido para elementos abaixo
- Reorganizar layout com grid: Mais complexo, requer mudanças maiores
- Colunas em mobile: Quebra responsividade

### Decisão 2: Usar `flex-shrink: 0` para `.online` e `.conta`
**Escolha**: Adicionar `flex-shrink: 0` a `.online` e `.conta` para garantir que não sejam comprimidos.

**Rationale**:
- Garante que esses elementos sempre têm seu tamanho natural
- Funciona com `flex-direction: column` da aside
- Sem overhead de JavaScript

### Decisão 3: Manter estrutura HTML inalterada
**Escolha**: Solução 100% CSS, sem mudanças no HTML.

**Rationale**:
- Reduz risco
- Não afeta JavaScript ou renderização
- Mais fácil de revisar e debugar

## Risks / Trade-offs

**[Risk]** Cálculo de `max-height` pode ficar desalinhado se gaps ou paddings muderem  
→ **Mitigation**: Documentar a fórmula exata no CSS e revisar se alterar layout da sidebar

**[Risk]** Scroll do menu pode ser confundido com scroll da página em UX  
→ **Mitigation**: Menu tem visual claro com scroll bar nativo, usa espaço separado

**[Trade-off]** Scroll bar visual do menu ocupa ~12px de espaço  
→ **Aceitável**: Melhor que ocultar seção "Usando agora"

## Implementation

### Arquivo a modificar
- `frontend/src/styles/layout.css`

### Mudanças CSS necessárias
1. Calcular espaço disponível para `nav`:
   - Brand: ~100px
   - Gaps: 22px × 3 = 66px
   - Online + Sync + Conta: ~140px
   - **Total reservado**: ~306px
   - **Max-height do nav**: `calc(100vh - 306px)` ou ajustar conforme medições

2. Aplicar a `nav`:
   ```css
   max-height: calc(100vh - 306px);
   overflow-y: auto;
   overflow-x: hidden;
   ```

3. Aplicar a `.online` e `.conta`:
   ```css
   flex-shrink: 0;
   ```

4. Considerar padding/margin da barra lateral ao calcular
