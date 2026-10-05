## Why

A paleta de cores atual da aplicação iSolutis Hub usa cores altamente saturadas (especialmente o turquesa #22C3CE), causando fadiga visual e desconforto em sessões prolongadas. A falta de harmonia cromática entre cores primárias, neutras e de status prejudica a legibilidade e a experiência do usuário. Uma paleta dessaturada e refinada mantendo a identidade visual da marca (azul-marinho e turquesa) resolve esse problema e moderniza a aparência geral da interface.

## What Changes

- **CSS Custom Properties** (`--navy`, `--teal`, `--gold`, cores de status) dessaturadas em `frontend/src/styles/tokens.css`
- **Cores primárias**: Navy base reduzida de #1B2B4B para #1a2d47, Teal base reduzida de #22C3CE para #3b9ca8
- **Cores neutras**: Background, surface, sunk, line refinadas com tonalidades mais harmoniosas
- **Cores de status** (OK, Warn, Bad, Info): Dessaturadas e mais terrosas para melhor integração visual
- **Modo dark**: Cores ajustadas mantendo contraste e legibilidade
- **Modo light**: Backgrounds e neutros refinados para modo claro
- Todas as cores de componentes que dependem dos tokens CSS serão automaticamente atualizadas

## Capabilities

### New Capabilities
- `clean-color-palette`: Sistema de cores dessaturado e harmoniosa que mantém identidade de marca, reduz fadiga visual e melhora legibilidade em sessões prolongadas

### Modified Capabilities
<!-- Nenhuma, pois é apenas redefinição visual da paleta base -->

## Impact

- **Frontend**: `frontend/src/styles/tokens.css` — arquivo de CSS custom properties será atualizado
- **Design system**: Componentes, layouts e features que usam os tokens afetados (praticamente todos os componentes)
- **Modos**: Light mode e dark mode serão ambos ajustados com coesão cromática
- **Compatibilidade**: Mudança puramente visual, sem alterações em API ou lógica
- **Validação necessária**: Testes visuais em todos os componentes para garantir contraste e harmonia

