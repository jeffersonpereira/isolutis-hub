# Spec Delta

## ADDED Requirements

### Requirement: Estado da listagem na URL
Telas com listagem filtrável e paginada SHALL guardar filtros, ordenação e página na query string da URL, omitindo os
valores padrão, e SHALL restaurá-los ao abrir ou recarregar a URL. Valores inválidos SHALL ser ignorados.

#### Scenario: Recarregar mantém o filtro
- **WHEN** o usuário está em `/fin-titulos?status=A&pag=2` e recarrega a página
- **THEN** a lista reaparece filtrada por títulos abertos, na página 2

#### Scenario: Alterar filtro não empilha histórico
- **WHEN** o usuário altera um filtro
- **THEN** a URL é atualizada sem criar nova entrada no histórico

#### Scenario: Mudar de página cria entrada
- **WHEN** o usuário vai da página 1 para a 2 e aciona Voltar
- **THEN** a página 1 é exibida, com os mesmos filtros

#### Scenario: Parâmetro inválido
- **WHEN** a URL traz `pag=abc` ou uma situação desconhecida
- **THEN** o valor é ignorado e o padrão é usado
