## Why

O iSolutis Hub está prestes a ser comercializado, mas apresenta lacunas que comprometem a confiança do produto: a infraestrutura de deploy é totalmente manual, a identidade visual tem inconsistências internas, fluxos críticos (orçamentos, vencimentos, entrada de novos membros) carecem de acabamento profissional. Esta onda endereça tudo que precisa estar sólido antes do primeiro cliente pagar.

## What Changes

- **CI/CD pipeline** com GitHub Actions: lint, type-check, testes e build automatizados a cada push; deploy contínuo quando tudo passa.
- **Identidade visual coerente**: fontes hospedadas localmente (sem Google Fonts), nomes de módulos alinhados ao vocabulário do usuário, tokens tipográficos e de sombra padronizados, tokens de cor renomeados para eliminar nomenclatura enganosa (`--gold` → `--teal-mid`).
- **Painel com performance real**: queries de funil e orçamentos reescritas como agregações no banco (eliminando carregamento de todas as linhas em memória), skeleton de loading na carga inicial, e zona de alertas ativos (vencimentos, orçamentos sem resposta, projetos atrasados).
- **Faturamento com sinalização de vencimentos**: hierarquia visual clara entre lançamentos recebidos, previstos, que vencem hoje e vencidos — sem alteração de backend.
- **Orçamentos em PDF**: o documento de orçamento, hoje entregue em `.html`, passa a ser gerado como `.pdf` real com CSS de impressão ajustado para A4.
- **Convite de equipe por e-mail**: substituição do fluxo manual (admin cria usuário com senha inicial e a repassa fora do sistema) por um link de convite com expiração onde o novo membro define sua própria senha.

## Capabilities

### New Capabilities

- `ci-cd-pipeline`: pipeline de integração e entrega contínua via GitHub Actions
- `design-system-tokens`: sistema de tokens CSS unificado (tipografia, sombras, cores) e fontes locais
- `module-naming`: nomes de módulos no menu alinhados ao vocabulário do usuário final
- `painel-performance`: queries agregadas no banco para o painel + skeleton de loading
- `painel-alertas`: zona de alertas ativos no painel (vencimentos, orçamentos parados, projetos atrasados)
- `faturamento-status-visual`: sinalização visual por estado de vencimento nos lançamentos de receita
- `orcamento-pdf`: geração de orçamento em PDF com CSS de impressão para A4
- `convite-equipe`: fluxo de convite por e-mail para novos membros da equipe

### Modified Capabilities

- `theme-system`: os tokens de cor ganham novos nomes semânticos; mudança de nomes de variáveis afeta todo CSS que os usa

## Impact

**Backend:**
- `backend/app/services/painel.py` — reescrita das queries de funil e orçamentos
- `backend/app/routers/orcamentos.py` — endpoint `/documento` passa a retornar PDF
- `backend/app/routers/equipe.py` — novos endpoints de convite (`POST /convite`, `POST /convite/{token}/aceitar`)
- `backend/app/models/` — nova tabela `convites` (token, email, empresa_id, expira_em, usado_em)
- Nova dependência Python: `weasyprint` ou `playwright` para geração de PDF

**Frontend:**
- `frontend/src/styles/tokens.css` — novos tokens de tipografia, sombra e renomeação de cores
- `frontend/src/styles/*.css` — atualização de todos os usos dos tokens renomeados
- `frontend/src/features/*.ts` — `nome:` atualizado nos `registrarVista` afetados
- `frontend/src/features/painel.ts` — skeleton + zona de alertas
- `frontend/src/features/faturamento.ts` — lógica de status visual por vencimento
- `frontend/src/features/equipe.ts` — UI de convite
- Nova tela pública de aceite de convite (rota `/convite/:token`)
- `frontend/public/fonts/` — arquivos `.woff2` das fontes (Montserrat, IBM Plex Sans, IBM Plex Mono)

**Infra:**
- `.github/workflows/ci.yml` — novo arquivo
- `backend/Dockerfile` — adicionar `HEALTHCHECK`
- `backend/migrations/` — nova migração para tabela `convites`
