## ADDED Requirements

### Requirement: Logo do produto conforme o fundo
O sistema SHALL exibir a logo da AIME Tech como logo padrão do produto: a versão horizontal reverso (símbolo colorido, nome branco) em telas de fundo escuro (login, convite, escolha de empresa, onboarding e menu lateral) e a versão horizontal colorida em PDFs e e-mails de fundo claro. O símbolo da AIME Tech SHALL ser usado no menu recolhido. Empresas com logomarca própria continuam vendo a sua.

#### Scenario: Tela de login
- **WHEN** um visitante abre a tela de login
- **THEN** a logo horizontal reverso da AIME Tech aparece no topo, sem referência visual à iSolutis

#### Scenario: Telas pré-login relacionadas
- **WHEN** o usuário abre a tela de convite, de escolha de empresa ou o onboarding
- **THEN** a mesma logo da AIME Tech aparece, com altura proporcional (sem deformar ou saltar o layout)

#### Scenario: Empresa com logomarca própria
- **WHEN** a empresa ativa tem logomarca enviada
- **THEN** a interface e os documentos mostram a logomarca da empresa, e a logo da AIME Tech só é usada na ausência dela

### Requirement: Favicon da AIME Tech
O sistema SHALL usar o favicon da AIME Tech (`favicon.ico`, ícone SVG e `apple-touch-icon`) em todas as páginas do Hub.

#### Scenario: Aba do navegador
- **WHEN** o Hub é aberto em qualquer navegador
- **THEN** a aba mostra o ícone da AIME Tech

### Requirement: Nome do produto "AIME Tech Hub"
O sistema SHALL se identificar como "AIME Tech Hub" no título da página e da aba, nos textos de interface, nas mensagens geradas, nos e-mails (assunto, cabeçalho e rodapé), no emissor do código 2FA, no título da API e na documentação. Nenhum texto de produto SHALL citar "iSolutis".

#### Scenario: Título da aba
- **WHEN** o usuário navega por uma tela do Hub
- **THEN** o título da aba termina em "AIME Tech Hub"

#### Scenario: E-mail de convite
- **WHEN** o sistema envia um convite
- **THEN** o assunto e o corpo citam "AIME Tech Hub"

#### Scenario: Cadastro de 2FA
- **WHEN** um usuário configura o 2FA
- **THEN** o aplicativo autenticador mostra o emissor "AIME Tech Hub"

### Requirement: Identidade padrão dos documentos
Quando não houver cadastro da empresa, os PDFs SHALL usar o nome "AIME Tech" e o subtítulo "Transformando o Futuro", com a logo AIME Tech para fundo claro. O arquivo de exportação de faturamento SHALL ser nomeado `faturamento-aime-{ano}.csv`.

#### Scenario: PDF sem cadastro
- **WHEN** um orçamento é gerado em PDF sem identidade de empresa cadastrada
- **THEN** o cabeçalho traz a logo AIME Tech e o rodapé traz "AIME Tech · Transformando o Futuro"

#### Scenario: Exportar faturamento
- **WHEN** o usuário exporta o faturamento de 2026
- **THEN** o arquivo se chama `faturamento-aime-2026.csv`

### Requirement: Dados existentes preservados
A troca de marca MUST NOT alterar banco de dados, migrations, dados cadastrados, paletas ou logomarcas salvas por empresa.

#### Scenario: Empresa já cadastrada
- **WHEN** o Hub é atualizado com a nova marca
- **THEN** o nome, a paleta e a logomarca já salvos de cada empresa permanecem exatamente como estavam
