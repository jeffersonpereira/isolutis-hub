## 1. Assets

- [x] 1.1 Copiar do kit para `frontend/public/`: `horizontal_reverso.svg`, símbolo, `favicon.ico`, `icon.svg` (de `AIME_Tech_app.svg`) e `apple-touch-icon.png` (180); remover `logo.png` e `logo-horizontal.png` antigos
- [x] 1.2 Substituir `backend/app/documents/assets/logo.png` e `logo-horizontal.png` por PNGs AIME para fundo claro (`horizontal_cor`, símbolo) mantendo os nomes usados em `render.py`
- [x] 1.3 Trocar o `<link rel="icon">` de `index.html` por `favicon.ico`, `icon.svg` e `apple-touch-icon`

## 2. Frontend: marca e textos

- [x] 2.1 `index.html`: `<title>` "AIME Tech Hub", `alt`, `src` e dimensões (~200×56) das logos do login e do menu lateral
- [x] 2.2 `ui/convite.ts`, `ui/escolha-empresa.ts`, `ui/onboarding.ts`: nova logo, `alt` e dimensões
- [x] 2.3 `ui/identidade.ts`: `LOGO_PADRAO`, `MARCA_PADRAO`, `alt` padrão e nome "AIME Tech (padrão)" na paleta sugerida
- [x] 2.4 `ui/barra-superior.ts`: título dinâmico `${nome} · AIME Tech Hub`
- [x] 2.5 Textos de UI: `features/{clientes,produtos,projetos,painel}.ts` e mensagem de acesso em `features/equipe.ts` ("AIME Tech Hub")
- [x] 2.6 `domain/orcamento.ts` e `domain/whatsapp.ts`: mensagens citam AIME Tech

## 3. Tema e paleta

- [x] 3.1 `styles/tokens.css`: valores da paleta AIME nos temas claro e escuro (nomes dos tokens mantidos); atualizar o comentário de cabeçalho
- [x] 3.2 `PALETA_PADRAO` em `ui/identidade.ts` → `{ primaria: "#0B2D3B", destaque: "#4F6B8F" }`
- [x] 3.3 `styles/login.css`: fundo petróleo escuro e anel em lilás/champagne (hoje `#111b30` e `#22C3CE`)
- [x] 3.4 Conferir contraste do destaque no tema escuro (lilás) e do índigo sobre branco (≥ 4,5:1) e revisar visualmente telas principais nos dois temas
- [x] 3.5 Atualizar `frontend/docs/DESIGN_SYSTEM_COLORS.md` com a paleta AIME

## 4. Backend

- [x] 4.1 E-mails: `_email_vencimentos.html`, `_email_orcamentos.html`, `services/convites.py`, `services/notificacoes.py` → "AIME Tech Hub"
- [x] 4.2 2FA: `routers/auth_2fa.py` (`issuer_name`) e `services/totp.py` (padrão de `empresa`)
- [x] 4.3 `main.py` e `openapi.json` (título da API); `pyproject.toml` (description)
- [x] 4.4 `documents/render.py`: `PADRAO = Identidade(nome="AIME Tech", subtitulo="Transformando o Futuro")`
- [x] 4.5 `routers/faturamento.py`: arquivo `faturamento-aime-{ano}.csv`
- [x] 4.6 Comentários/docstrings e exemplos de scripts que citam a marca (`domain/projeto.py`, `services/projetos.py`, `scripts/*`), sem tocar migrations nem dados

## 5. Docs

- [x] 5.1 `README.md`, `docs/modulo-financeiro.md`, `docs/banco-de-dados.md` (apenas texto de marca; sem alterar descrições de schema)

## 6. Testes e verificação

- [x] 6.1 Atualizar `ui/identidade.test.ts`, `domain/orcamento.test.ts` e demais testes que assertam textos/paleta antigos; testes do backend que assertam e-mail/CSV/PDF
- [ ] 6.2 Rodar testes do frontend (vitest) e do backend; `grep -ri isolutis` deve restar só em: migrations, fixtures/e2e `@isolutis.com.br`, nomes de pacote/repo e `cd.yml`
- [ ] 6.3 Verificar no navegador: login, convite, escolha de empresa, menu lateral expandido/recolhido, favicon, tema claro/escuro; gerar um PDF de orçamento
