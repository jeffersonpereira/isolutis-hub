## Context

O iSolutis Hub é um ERP/CRM multi-tenant (FastAPI + TypeScript vanilla + PostgreSQL) com autenticação JWT + Argon2id, RLS via GUC `empresa_id`, WebSocket via Supabase e geração de documentos com WeasyPrint. A Onda 1 entregou infra (CI/CD, Dockerfile), design system, painel com alertas, PDF de orçamentos e convite de equipe com SMTP configurado.

A Onda 2 introduz quatro capacidades: onboarding, relatórios, 2FA e notificações. Cada uma tem dependências e decisões técnicas próprias.

## Goals / Non-Goals

**Goals:**
- Wizard de onboarding que guia o primeiro acesso sem código adicional em rotas existentes
- DRE e fluxo de caixa calculados diretamente em SQL com exportação PDF e Excel
- TOTP 2FA para todos os usuários, obrigatório para admins em produção
- E-mails de alerta disparados periodicamente sem serviço externo de fila

**Non-Goals:**
- SSO / OAuth externo (SAML, Google Workspace)
- Notificações push no browser (service workers)
- Relatórios customizáveis ou builder de dashboards
- Integração contábil (SPED, NF-e)
- 2FA por SMS

## Decisions

### D1 — Onboarding: flag no banco, não em localStorage

**Decisão:** Adicionar coluna `onboarding_concluido: bool` na tabela `empresas`. O wizard é exibido quando essa flag é `false` e o usuário é o primeiro administrador a fazer login.

**Alternativa descartada:** Verificar em localStorage. Motivo: localStorage não sobrevive a troca de dispositivo/browser; o admin que fez onboarding num dispositivo não o veria repetir em outro, mas outro admin novo na mesma empresa veria o wizard desnecessariamente.

**Consequência:** migração 0007 inclui `ALTER TABLE empresas ADD COLUMN onboarding_concluido boolean NOT NULL DEFAULT false`.

---

### D2 — Relatórios: queries SQL agregadas, sem cache

**Decisão:** DRE e fluxo de caixa são calculados via queries `GROUP BY mes` + CTEs diretamente no endpoint `/relatorios`, sem cache. Para o Excel, usar `openpyxl` gerando bytes em memória (sem arquivo temporário).

**Alternativa descartada:** Materializar os dados em tabelas de agregação atualizadas por trigger. Motivo: complexidade desnecessária para o volume atual; queries SQL agregadas com índice em `data`/`vencimento` são suficientemente rápidas.

**Consequência:** `pyproject.toml` recebe `openpyxl>=3.1`. O endpoint aceita `?formato=pdf|xlsx` e retorna o Content-Type correspondente.

---

### D3 — 2FA: TOTP via pyotp, segredo criptografado

**Decisão:** Usar `pyotp` para gerar/validar TOTP (RFC 6238, compatível com Google Authenticator e Authy). O segredo TOTP é armazenado criptografado em `usuarios.totp_secret` (Fernet com `HUB_SECRET_KEY`). QR code gerado server-side com `qrcode[pil]` e retornado como `data:image/png;base64,...`.

**Alternativa descartada:** Serviço externo (Twilio Verify). Motivo: dependência paga, latência, e o volume inicial não justifica.

**Fluxo de ativação:**
1. `POST /auth/2fa/setup` → retorna `{qr_code, provisioning_uri, backup_codes}`
2. `POST /auth/2fa/confirmar` com código TOTP → ativa 2FA, invalida sessões antigas
3. No login: se `totp_ativo=true`, retorna `{requer_2fa: true}` sem JWT; `POST /auth/2fa/verificar` valida o código e emite JWT completo

**Códigos de backup:** 8 códigos de uso único, armazenados como hashes Argon2id em `totp_backup_codes (usuario_id, codigo_hash, usado_em)`.

---

### D4 — Notificações: APScheduler in-process, sem worker externo

**Decisão:** Usar `APScheduler` (BackgroundScheduler) inicializado no startup do FastAPI para disparar jobs de notificação. Jobs rodam a cada hora e verificam: lançamentos vencendo hoje, orçamentos sem resposta há 15 dias, projetos com entrega amanhã.

**Alternativa descartada:** Celery + Redis. Motivo: overhead de infraestrutura desnecessário; APScheduler in-process é suficiente para o volume inicial e mantém o deploy simples (único container).

**Alternativa descartada:** Endpoint de trigger via cron externo. Motivo: requer orquestrador externo (GitHub Actions cron, cron job no servidor).

**Prevenção de duplicidade:** campo `notificado_em` em `lancamentos_receita` e `orcamentos`; jobs só enviam quando `notificado_em IS NULL` ou `notificado_em < data_limite`.

**Risco de escala:** APScheduler in-process não funciona com múltiplas réplicas (cada instância dispara o mesmo e-mail). Mitigação: usar `SKIP_LOCKED` no SELECT para "lock" do lançamento antes de notificar — garante at-most-once em múltiplas réplicas.

---

### D5 — Migração: única migração 0007 para todos os campos novos

**Decisão:** Agrupar todas as alterações de schema da Onda 2 em uma única migração `0007_onda2.py`: `onboarding_concluido` em `empresas`; `totp_secret`, `totp_ativo` em `usuarios`; tabela `totp_backup_codes`; `notificado_em` em `lancamentos_receita` e `orcamentos`.

**Alternativa:** Uma migração por feature. Descartada por simplicidade de rollback — a Onda 2 entra toda junta ou não entra.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| APScheduler falha silenciosamente se a thread morrer | Adicionar handler de erro com log + alerta no Sentry (ou log estruturado) |
| TOTP clock skew (cliente com relógio adiantado/atrasado) | `pyotp.TOTP.verify(token, valid_window=1)` — aceita ±30s |
| Excel com muitos registros pode usar muita memória | Usar `write_only=True` no openpyxl para streaming; limitar relatório a 12 meses |
| Onboarding pulado por admin técnico que não quer o wizard | Botão "Pular configuração" sempre visível — flag é marcada ao pular também |
| `HUB_SECRET_KEY` rotacionada invalida todos os segredos TOTP | Documentar que rotação de chave requer reset de 2FA de todos os usuários |

## Migration Plan

1. Rodar `alembic upgrade head` (já no CMD do Dockerfile)
2. Deploy sem feature flags — onboarding ativa automaticamente para empresas com `onboarding_concluido = false`
3. Empresas existentes em produção terão `onboarding_concluido = false` após migração → adicionar script de seed que marca todas as empresas existentes como `true` (elas já fizeram onboarding informalmente)
4. Rollback: `alembic downgrade -1` remove as colunas; nenhuma dado crítico é perdido

## Open Questions

- O job de notificação deve ser configurável por empresa (cada admin escolhe quais alertas receber) ou global? — Assumir global por ora, configurável na Onda 3.
- Relatório de fluxo de caixa deve incluir despesas (tabela `lancamentos_despesa`)? — Sim, para ser um fluxo real; precisa confirmar o nome da tabela no schema.
- Backup codes de 2FA: mostrar uma única vez no setup ou permitir regenerar? — Mostrar uma vez com aviso, regeneração destrói os anteriores.
