## 1. Migração de banco — Onda 2

- [x] 1.1 Criar `backend/migrations/versions/0007_onda2.py` com: `ALTER TABLE empresas ADD COLUMN onboarding_concluido boolean NOT NULL DEFAULT false`
- [x] 1.2 Adicionar à migração: `ALTER TABLE usuarios ADD COLUMN totp_secret text, ADD COLUMN totp_ativo boolean NOT NULL DEFAULT false`
- [x] 1.3 Adicionar à migração: `CREATE TABLE totp_backup_codes (id serial PRIMARY KEY, usuario_id int NOT NULL REFERENCES usuarios(id), codigo_hash text NOT NULL, usado_em timestamptz)`
- [x] 1.4 Adicionar à migração: `ALTER TABLE lancamentos_receita ADD COLUMN notificado_em timestamptz`, `ALTER TABLE orcamentos ADD COLUMN notificado_em timestamptz`
- [x] 1.5 Adicionar script de seed na migração: marcar `onboarding_concluido = true` para todas as empresas existentes (não forçar wizard em produção)

## 2. Onboarding Wizard — Backend

- [x] 2.1 Adicionar campo `onboarding_concluido: bool` ao modelo ORM `Empresa` em `backend/app/models/tenant.py`
- [x] 2.2 Criar `backend/app/routers/onboarding.py` com `GET /onboarding/status` (retorna `{concluido: bool}`) e `POST /onboarding/concluir` (marca `onboarding_concluido = true`)
- [x] 2.3 O endpoint `POST /onboarding/concluir` deve ser restrito a administradores e aceitar payload com `produtos: list[{nome, preco}]` (opcional) para criar produtos iniciais
- [x] 2.4 Registrar o router em `backend/app/main.py`

## 3. Onboarding Wizard — Frontend

- [x] 3.1 Criar `frontend/src/ui/onboarding.ts` com wizard de 3 etapas: Perfil da Empresa, Produtos/Serviços, Tour
- [x] 3.2 Etapa 1: formulário com campo "Nome comercial" (obrigatório) e "Segmento" (opcional) — chama `PATCH /empresas/{id}` com os dados
- [x] 3.3 Etapa 2: formulário para até 5 produtos com nome e preço, com botão "Pular esta etapa"
- [x] 3.4 Etapa 3: tour com tooltips sobre Clientes, Funil, Faturamento e Projetos — botão "Começar a usar" chama `POST /onboarding/concluir`
- [x] 3.5 Em `frontend/src/main.ts`: após login, se o usuário é admin e `onboarding_concluido = false`, redirecionar para o wizard antes do painel

## 4. Relatórios Financeiros — Backend

- [x] 4.1 Adicionar `"openpyxl>=3.1"` ao `backend/pyproject.toml`
- [x] 4.2 Criar `backend/app/services/relatorios.py` com função `calcular_dre(db, empresa_id, ano) -> list[{mes, receitas, custos, resultado}]` usando query GROUP BY mês
- [x] 4.3 Criar função `calcular_fluxo_caixa(db, empresa_id, ano) -> list[{mes, entradas, saidas, saldo_mes, saldo_acumulado}]`
- [x] 4.4 Criar `backend/app/documents/relatorio_pdf.py` com função `relatorio_pdf(dados, tipo, empresa) -> bytes` usando WeasyPrint
- [x] 4.5 Criar template HTML/CSS para o relatório em `backend/app/documents/templates/_relatorio.html` e `_relatorio.css` com layout A4 limpo e tabela formatada
- [x] 4.6 Criar função `relatorio_xlsx(dados, tipo, empresa) -> bytes` usando openpyxl com `write_only=True`
- [x] 4.7 Criar `backend/app/routers/relatorios.py` com `GET /relatorios/dre?ano=&formato=json|pdf|xlsx` e `GET /relatorios/fluxo-caixa?ano=&formato=json|pdf|xlsx`
- [x] 4.8 Registrar o router em `backend/app/main.py`

## 5. Relatórios Financeiros — Frontend

- [x] 5.1 Criar `frontend/src/features/relatorios.ts` como nova vista registrada com `registrarVista({ id: "relatorios", nome: "Relatórios", ... })`
- [x] 5.2 Implementar seletor de ano (padrão: ano corrente) e abas DRE / Fluxo de Caixa
- [x] 5.3 Renderizar tabela do DRE com colunas Mês / Receitas / Custos / Resultado, aplicando `color: var(--ok)` para resultado positivo e `color: var(--bad)` para negativo
- [x] 5.4 Renderizar tabela de Fluxo de Caixa com colunas Mês / Entradas / Saídas / Saldo do Mês / Saldo Acumulado, destacando saldo negativo com `color: var(--bad)`
- [x] 5.5 Adicionar botões "Exportar PDF" e "Exportar Excel" que chamam os endpoints com `formato=pdf` e `formato=xlsx` e disparam download via Blob
- [x] 5.6 Adicionar "Relatórios" ao menu de navegação principal (sidebar)

## 6. Autenticação 2FA — Backend

- [x] 6.1 Adicionar `"pyotp>=2.9"` e `"qrcode[pil]>=7.4"` ao `backend/pyproject.toml`
- [x] 6.2 Criar `backend/app/services/totp.py` com: `gerar_segredo()`, `gerar_qr_code(segredo, email) -> str (base64 PNG)`, `verificar_codigo(segredo, codigo, janela=1) -> bool`
- [x] 6.3 Criar `backend/app/routers/auth_2fa.py` (sub-router de `/auth`) com endpoints: `POST /auth/2fa/setup`, `POST /auth/2fa/confirmar`, `POST /auth/2fa/verificar`, `DELETE /auth/2fa` (desativar)
- [x] 6.4 Em `POST /auth/2fa/setup`: gerar segredo, criptografar com Fernet(`HUB_SECRET_KEY`), salvar em `usuario.totp_secret` (sem ativar ainda), retornar `{qr_code, provisioning_uri, backup_codes}`
- [x] 6.5 Em `POST /auth/2fa/confirmar`: validar o código TOTP, ativar `totp_ativo = true`, salvar hashes Argon2id dos backup codes em `totp_backup_codes`
- [x] 6.6 Atualizar endpoint `POST /auth/login` em `routers/auth.py`: se `usuario.totp_ativo = true`, retornar `{requer_2fa: true, token_temporario}` sem JWT de acesso
- [x] 6.7 Em `POST /auth/2fa/verificar`: validar código TOTP ou backup code; se válido, emitir JWT de acesso completo
- [x] 6.8 Em `DELETE /auth/2fa`: exigir código TOTP atual, desativar 2FA, apagar `totp_secret` e backup codes
- [x] 6.9 Adicionar validação em `Settings.validar_para_producao()`: logar aviso se admin sem 2FA existir (não bloquear startup, apenas alertar)

## 7. Autenticação 2FA — Frontend

- [x] 7.1 Em `frontend/src/ui/login.ts`: detectar resposta `{requer_2fa: true}` no login e exibir tela de inserção do código TOTP
- [x] 7.2 Na tela de segundo fator: campo para código de 6 dígitos, link "Usar código de backup" que troca para input de backup code, botão "Verificar"
- [x] 7.3 Criar seção "Segurança" na tela de configurações/perfil com: status do 2FA, botão "Ativar 2FA" (mostra QR code + backup codes) ou "Desativar 2FA"
- [x] 7.4 Na tela de setup: exibir QR code (img com src `data:image/png;base64,...`), campo para confirmar código do app, lista dos 8 backup codes com botão "Copiei, continuar"

## 8. Notificações por E-mail — Backend

- [x] 8.1 Adicionar `"apscheduler>=3.10"` ao `backend/pyproject.toml`
- [x] 8.2 Criar `backend/app/services/notificacoes.py` com função `enviar_alertas_vencimentos(db)`: busca lançamentos com `vencimento = today` e `status != 'recebido'` e `notificado_em IS NULL`, agrupa por empresa, envia e-mail consolidado
- [x] 8.3 Criar função `enviar_alertas_orcamentos(db)`: busca orçamentos com `status = 'enviado'` e `data < today - 7` e `notificado_em IS NULL`, agrupa por empresa, envia e-mail
- [x] 8.4 Implementar envio via smtplib reutilizando a função auxiliar já criada em `services/convites.py`; após envio bem-sucedido, atualizar `notificado_em = now()`; em caso de falha SMTP, logar erro e NÃO atualizar `notificado_em`
- [x] 8.5 Criar `backend/app/scheduler.py` com `BackgroundScheduler` do APScheduler; registrar os dois jobs com `trigger='interval', hours=1`
- [x] 8.6 Em `backend/app/main.py`, no evento `startup`, iniciar o scheduler; no evento `shutdown`, parar o scheduler
- [x] 8.7 Criar templates de e-mail HTML para: (a) lançamentos vencendo hoje, (b) orçamentos sem resposta — usar Jinja2 inline ou arquivo em `documents/templates/`
- [x] 8.8 Adicionar campo `notificado_em` aos schemas Pydantic de `LancamentoReceita` e `Orcamento` (campo interno, não exposto em listagens públicas)

## 9. Campo notificado_em — Faturamento (delta spec)

- [x] 9.1 Adicionar `notificado_em: datetime | None` ao modelo ORM `LancamentoReceita` em `backend/app/models/tenant.py`
- [x] 9.2 Adicionar `notificado_em: datetime | None` ao modelo ORM `Orcamento`
- [x] 9.3 Verificar que o campo NÃO é exposto nos endpoints de listagem de lançamentos e orçamentos (campo interno)
