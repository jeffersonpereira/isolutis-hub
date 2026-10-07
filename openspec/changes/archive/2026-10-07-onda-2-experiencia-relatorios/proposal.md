## Why

Com a Onda 1 o sistema ganhou base técnica sólida (CI/CD, design system, PDF, convites). Agora faltam as capacidades que fazem o produto ser **percebido como completo** por quem avalia comprar: o usuário precisa conseguir começar a usar sem atrito, precisar ver seus números de negócio consolidados e confiar que a plataforma é segura. Sem onboarding, relatórios e autenticação forte, o sistema não passa de um MVP interno — não de um produto comercializável.

## What Changes

- **Onboarding wizard**: fluxo guiado de primeiro acesso que configura a empresa, cadastra produtos/serviços iniciais e mostra o estado inicial do painel — substituindo a tela vazia que nenhum cliente novo sabe o que fazer
- **Relatórios financeiros**: DRE simplificado (receitas − custos = resultado) e fluxo de caixa consolidado por período, com exportação para PDF e Excel — capacidade ausente que todo decisor de negócio exige antes de comprometer com um sistema
- **Autenticação 2FA**: suporte a TOTP (Google Authenticator / Authy) para qualquer usuário, obrigatório para administradores em modo produção — requisito de segurança mencionado por clientes enterprise e necessário para conformidade
- **Notificações proativas por e-mail**: envio automático de alertas para eventos críticos (lançamento vencendo hoje, orçamento sem resposta há X dias, projeto atrasado) usando a infra SMTP já implementada na Onda 1 — fecha o ciclo entre o painel de alertas e ação real do usuário

## Capabilities

### New Capabilities

- `onboarding-wizard`: Fluxo de setup inicial guiado após o primeiro login de uma empresa nova, cobrindo perfil da empresa, primeiros produtos/serviços e tour pelo painel
- `relatorios-financeiros`: Tela de relatórios com DRE (Demonstrativo de Resultado) e fluxo de caixa por período, com exportação para PDF (WeasyPrint) e Excel (openpyxl)
- `autenticacao-2fa`: Configuração e verificação de segundo fator via TOTP; endpoint de setup, QR code, verificação e desativação; campo obrigatório para produção
- `notificacoes-email`: Jobs de notificação periódica (agendados via APScheduler ou cron HTTP) disparando e-mails de alerta para vencimentos próximos, orçamentos parados e projetos atrasados

### Modified Capabilities

- `faturamento-status-visual`: Adicionar campo `notificado_em` ao schema de lançamento para rastrear quando um alerta por e-mail foi enviado (evitar spam de notificações repetidas)

## Impact

**Backend:**
- `backend/app/routers/`: novos routers para `onboarding.py`, `relatorios.py`, `auth_2fa.py` (sub-router de auth)
- `backend/app/services/`: `onboarding.py`, `relatorios.py`, `notificacoes.py`, `totp.py`
- `backend/app/documents/`: novos templates para DRE e fluxo de caixa (PDF + função Excel)
- `backend/migrations/`: migração 0007 (campo `totp_secret` e `totp_ativo` em `usuarios`; campo `notificado_em` em `lancamentos_receita`)
- `backend/pyproject.toml`: adicionar `openpyxl>=3.1`, `pyotp>=2.9`, `qrcode[pil]>=7.4`, `apscheduler>=3.10` (ou endpoint de trigger externo)

**Frontend:**
- `frontend/src/ui/onboarding.ts`: wizard multi-step com steps de empresa, produtos e tour
- `frontend/src/features/relatorios.ts`: nova vista de relatórios com seletor de período e botões de exportação
- `frontend/src/features/configuracoes.ts` (ou `perfil.ts`): seção para ativar/desativar 2FA com QR code

**OpenSpec specs existentes impactadas:**
- `faturamento-status-visual`: delta spec com novo campo `notificado_em`
