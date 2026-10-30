## MODIFIED Requirements

### Requirement: Paleta de cores primárias dessaturada
A aplicação SHALL definir a paleta padrão da AIME Tech (petróleo, índigo, lilás, champagne, grafite e off-white) via CSS custom properties, mantendo contraste suficiente para leitura nos temas claro e escuro.

Cores específicas (light mode):
- `--navy` / `--accent`: #0B2D3B (petróleo)
- `--teal` / `--teal-mid`: #4F6B8F (índigo)
- `--teal-pale`: tom claro derivado do lilás #A7AFC7
- `--canvas`: #F7F6F2 (off-white)
- Champagne #D9C8B1 e grafite #2E3338 disponíveis para realces e texto de apoio

#### Scenario: Cores primárias aplicadas no header
- **WHEN** usuário visualiza aplicação em light mode
- **THEN** o menu e o botão primário usam o petróleo #0B2D3B e os destaques usam o índigo #4F6B8F

#### Scenario: Cores primárias em dark mode
- **WHEN** usuário ativa dark mode (via preferência do sistema ou seletor)
- **THEN** o destaque usa o lilás #A7AFC7 sobre fundo petróleo escuro, com contraste mínimo de 4,5:1 para texto

#### Scenario: Cores semânticas preservadas
- **WHEN** a interface mostra status de sucesso, alerta, erro ou informação
- **THEN** as cores semânticas (ok, warn, bad, info) permanecem as mesmas de antes da troca de marca
