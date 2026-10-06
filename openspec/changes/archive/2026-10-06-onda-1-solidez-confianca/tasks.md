## 1. CI/CD Pipeline

- [x] 1.1 Criar `.github/workflows/ci.yml` com jobs: lint-backend (ruff + mypy), lint-frontend (eslint + tsc), test-backend (pytest), test-frontend (vitest)
- [x] 1.2 Configurar jobs para rodar em paralelo onde possível e em sequência onde há dependência
- [x] 1.3 Adicionar `HEALTHCHECK` no `Dockerfile`: `CMD curl -f http://localhost:8000/api/saude || exit 1`
- [x] 1.4 Atualizar `CMD` no `Dockerfile` para executar `alembic upgrade head` antes de iniciar `uvicorn`
- [x] 1.5 Criar `.github/workflows/cd.yml` com job de build Docker + push para registry + deploy, disparado apenas em push para `main`
- [x] 1.6 Documentar no `README` todos os secrets GitHub necessários (`HUB_SECRET_KEY`, `DOCKER_REGISTRY`, credenciais de deploy)
- [ ] 1.7 Validar que o pipeline passa do zero num branch de teste antes de habilitar proteção de branch

## 2. Identidade Visual — Tokens e Fontes

- [x] 2.1 Baixar arquivos `.woff2` de Montserrat 600, IBM Plex Sans 400 e 500, IBM Plex Mono 400 e salvar em `frontend/public/fonts/`
- [x] 2.2 Substituir imports do Google Fonts por `@font-face` locais em `base.css` com `font-display: swap`
- [x] 2.3 Adicionar tokens de escala tipográfica em `tokens.css`: `--text-2xs` até `--text-xl`
- [x] 2.4 Substituir todos os `font-size` com valor numérico literal nos arquivos CSS pelos tokens `--text-*` correspondentes
- [x] 2.5 Adicionar tokens de sombra em `tokens.css`: `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- [x] 2.6 Substituir o `box-shadow` hardcoded do `.drawer` por `var(--shadow-lg)`
- [x] 2.7 Renomear `--gold` → `--teal-mid` e `--gold-soft` → `--teal-pale` em `tokens.css` (light e dark)
- [x] 2.8 Executar find-replace em todos os arquivos CSS substituindo `var(--gold)` → `var(--teal-mid)` e `var(--gold-soft)` → `var(--teal-pale)`
- [ ] 2.9 Smoke test visual: abrir as 12 telas do sistema e confirmar que nenhuma cor quebrou após a renomeação

## 3. Nomes de Módulos

- [x] 3.1 Em `frontend/src/features/clientes.ts`: alterar `nome:` de `"Parceiro de Negócios"` para `"Clientes"`
- [x] 3.2 Em `frontend/src/features/negocios.ts`: alterar `nome:` de `"Negócios e Funil"` para `"Funil de Vendas"`
- [x] 3.3 Em `frontend/src/features/financeiro/parceiros.ts`: alterar `nome:` de `"Parceiro de Negócio"` para `"Fornecedores"`
- [x] 3.4 Verificar que todos os `id:` permanecem inalterados e a navegação por `localStorage` continua funcionando

## 4. Faturamento — Sinalização Visual de Vencimentos

- [x] 4.1 Em `frontend/src/features/faturamento.ts`: implementar função `statusVencimento(vencimento, status)` que retorna `{ rotulo, classe }` com base na comparação com `hoje()`
- [x] 4.2 Substituir a pill de status estática na listagem de faturamento pela pill dinâmica usando `statusVencimento()`
- [x] 4.3 Aplicar `background: var(--bad-bg)` na linha da tabela quando status for `"vencido"`
- [ ] 4.4 Testar os 4 estados: recebido, previsto futuro, vence hoje, vencido

## 5. Painel — Performance e Skeleton

- [x] 5.1 Em `backend/app/services/painel.py`: reescrever a query de funil usando `SELECT etapa, COUNT(*), SUM(valor), SUM(mensal) FROM negocios WHERE etapa IN (...) GROUP BY etapa`
- [x] 5.2 Reescrever a query de orçamentos aguardando com `WHERE status = 'enviado'` diretamente no banco (remover `svc_orcamentos.listar()` sem filtro)
- [x] 5.3 Atualizar o schema `Painel` em `backend/app/schemas/painel.py` para refletir os novos campos de resposta das queries agregadas
- [x] 5.4 Em `frontend/src/features/painel.ts`: adicionar função `vistaSkeleton()` que retorna HTML com blocos `.skeleton` nas áreas de KPIs e gráfico
- [x] 5.5 Exibir `vistaSkeleton()` durante `carregarTudo()` e substituir pelos dados reais ao concluir
- [x] 5.6 Corrigir o token de cor no `loading.css`: substituir `--bg-hover` (inexistente) por `--sunk`

## 6. Painel — Zona de Alertas

- [x] 6.1 Em `backend/app/services/painel.py`: adicionar query de lançamentos vencidos há mais de 3 dias (`vencimento < hoje - 3 AND status != 'recebido'`)
- [x] 6.2 Adicionar query de orçamentos sem resposta há mais de 15 dias (`status = 'enviado' AND data < hoje - 15`)
- [x] 6.3 Adicionar query de projetos com entrega atrasada (`entrega < hoje` com pelo menos uma etapa não concluída)
- [x] 6.4 Adicionar campos `alertas` ao schema `Painel`: `{ lancamentos_vencidos, orcamentos_parados, projetos_atrasados }` (cada um com `quantidade` e `ids` dos afetados)
- [x] 6.5 Em `frontend/src/features/painel.ts`: implementar componente de zona de alertas que só renderiza quando algum contador > 0
- [x] 6.6 Estilizar cada alerta com a cor semântica correta (`--bad` para vencidos/atrasados, `--warn` para orçamentos parados)
- [x] 6.7 Fazer cada alerta clicável e navegar para o módulo correspondente via `data-go`

## 7. Orçamentos — Geração de PDF

- [x] 7.1 Adicionar `weasyprint>=60` às dependências em `backend/pyproject.toml`
- [x] 7.2 Instalar `weasyprint` e dependências do sistema no `Dockerfile` (libpango, libcairo, etc.)
- [x] 7.3 Criar função `orcamento_pdf(orc, cliente) -> bytes` em `backend/app/documents/render.py` usando `weasyprint.HTML(string=html_content).write_pdf()`
- [x] 7.4 Adicionar CSS de impressão ao template de orçamento: `@page { size: A4; margin: 15mm }`, `page-break-inside: avoid` na tabela de itens, `thead` repetindo em cada página
- [x] 7.5 Atualizar `GET /orcamentos/{id}/documento` em `routers/orcamentos.py` para retornar `Response(pdf_bytes, media_type="application/pdf", headers={...})`
- [x] 7.6 Atualizar o header `Content-Disposition` para usar extensão `.pdf`
- [x] 7.7 Adicionar tratamento de erro: capturar exceções do WeasyPrint e retornar `ErroApp` com código `"pdf_indisponivel"`
- [ ] 7.8 Testar com um orçamento real: verificar layout A4, quebra de página com muitos itens, nome do arquivo gerado

## 8. Convite de Equipe

- [x] 8.1 Criar migração `0006_convites.py` com tabela `convites (id, token uuid UNIQUE, email citext, empresa_id FK, papel text, criado_por FK, expira_em timestamptz, usado_em timestamptz)`
- [x] 8.2 Criar `backend/app/schemas/convite.py` com schemas `ConviteEntrada` (nome, email, papel) e `ConviteLeitura`
- [x] 8.3 Criar `backend/app/services/convites.py` com funções: `criar_convite()`, `listar_pendentes()`, `cancelar_convite()`, `aceitar_convite(token, senha)`
- [x] 8.4 Em `criar_convite()`: verificar e-mail já membro, invalidar convite anterior pendente para o mesmo e-mail, gerar token UUID, calcular `expira_em = now() + 72h`
- [x] 8.5 Integrar envio de e-mail em `criar_convite()` usando SMTP configurado via `HUB_SMTP_*` em `config.py`
- [x] 8.6 Adicionar validação de `HUB_SMTP_HOST` em `Settings.validar_para_producao()`
- [x] 8.7 Criar rota `POST /equipe/convite` (admin) e `GET /equipe/convites` (admin) em `routers/equipe.py`
- [x] 8.8 Criar rota pública `POST /auth/convite/{token}/aceitar` em `routers/auth.py` (sem autenticação)
- [x] 8.9 Em `frontend/src/features/equipe.ts`: adicionar seção "Convites pendentes" na tela de equipe com lista e botão "Cancelar"
- [x] 8.10 Adicionar botão "Convidar membro" que abre gaveta com formulário de convite (nome, e-mail, papel)
- [x] 8.11 Criar tela pública `/convite/:token` em `frontend/src/ui/login.ts` (ou arquivo separado) com formulário de definição de senha
- [x] 8.12 Tratar estados: token válido (formulário), expirado (mensagem + contato admin), já usado (mensagem + link login)
- [ ] 8.13 Testar fluxo completo: admin convida → e-mail chega → link abre tela → membro define senha → login automático → painel
