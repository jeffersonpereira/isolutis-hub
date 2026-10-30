## Why

O Hub passa a ser um produto da AIME Tech ("AIME Tech Hub"), mas toda a identidade ainda é da iSolutis: logos nas telas de login, convite, escolha de empresa e onboarding, favicon, título da aba, e-mails, emissor do 2FA, PDFs, textos de interface e a paleta de cores (azul-marinho e turquesa). O kit de identidade da AIME Tech já está pronto (logos SVG/PNG, favicon, ícones e paleta), então a troca pode ser feita de uma vez, mantendo a marca consistente em todos os pontos de contato.

## What Changes

- **Logos e favicon**: telas pré-login (fundo escuro) passam a usar a logo horizontal reverso (símbolo colorido, nome branco); PDFs e fundos claros usam a horizontal colorida. Favicon trocado por `favicon.ico` + `icon.svg` + `apple-touch-icon` do kit, substituindo `<link rel="icon" href="/logo.png">`.
- **Marca no frontend**: `<title>`, `alt` das imagens, fallbacks `LOGO_PADRAO`/`MARCA_PADRAO` (menu lateral e menu recolhido), título dinâmico da aba (`· AIME Tech Hub`), textos de interface que citam "iSolutis" e as mensagens geradas (orçamento por WhatsApp, mensagem de acesso da equipe). As imagens ganham altura compatível com a nova proporção (~3,5:1).
- **Paleta**: a paleta padrão passa a ser a da AIME Tech (petróleo `#0B2D3B`, índigo `#4F6B8F`, lilás `#A7AFC7`, champagne `#D9C8B1`, grafite `#2E3338`, off-white `#F7F6F2`) em `tokens.css` (tema claro e escuro), `PALETA_PADRAO` ("AIME Tech (padrão)"), `login.css` e `DESIGN_SYSTEM_COLORS.md`. Cores semânticas (ok/warn/bad/info) permanecem.
- **Backend**: nome "AIME Tech Hub" nos e-mails (convite, vencimentos, orçamentos), emissor do 2FA, título da API (`main.py`, `openapi.json`), descrição do `pyproject.toml`; identidade padrão dos PDFs (`PADRAO`: nome "AIME Tech", subtítulo "Transformando o Futuro") e logos em `backend/app/documents/assets`; arquivo CSV de faturamento passa a `faturamento-aime-{ano}.csv`.
- **Docs**: `README.md` e `docs/*.md` atualizados.
- Testes afetados atualizados (`identidade.test.ts`, `orcamento.test.ts` e demais que assertam o texto ou a paleta antiga).

**Fora do escopo (não muda):** banco de dados, migrations e dados (a empresa cadastrada mantém o nome do cadastro, editável pela tela de Empresa), fixtures `@isolutis.com.br`, nomes de repositório/pacotes/`cd.yml` (`isolutis-hub*`) e troca de fontes (Montserrat/IBM Plex permanecem).

## Capabilities

### New Capabilities
- `marca-aime-tech`: identidade visual e nominal padrão do produto "AIME Tech Hub" (logos por tipo de fundo, favicon, nome do produto em interface, e-mails, 2FA, API e PDFs, e subtítulo dos documentos).

### Modified Capabilities
- `clean-color-palette`: a paleta primária padrão deixa de ser navy/teal da iSolutis e passa a ser a paleta AIME Tech.

## Impact

- **Frontend (`frontend/`)**: `index.html`; `public/` (novas logos, favicon, ícones); `src/ui/{identidade,convite,escolha-empresa,onboarding,barra-superior}.ts`; `src/features/{clientes,produtos,projetos,painel,equipe}.ts`; `src/domain/{orcamento,whatsapp}.ts`; `src/styles/{tokens,login}.css`; `docs/DESIGN_SYSTEM_COLORS.md`; testes.
- **Backend (`backend/`)**: `app/documents/{render.py,assets/*,templates/_email_*.html}`, `app/services/{convites,notificacoes,totp}.py`, `app/routers/{auth_2fa,faturamento}.py`, `app/main.py`, `openapi.json`, `pyproject.toml`. Sem alteração de schema, migrations ou contrato de API.
- **Comportamento de usuário**: usuários de 2FA já cadastrados não são afetados (o emissor só aparece em novos cadastros); empresas com paleta ou logomarca próprias salvas não mudam.
- **Docs**: `README.md`, `docs/*.md`.
