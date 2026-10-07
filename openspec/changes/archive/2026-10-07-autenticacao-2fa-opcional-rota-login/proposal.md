## Why

A autenticação em dois fatores deve ser uma escolha do usuário. Hoje o frontend obriga todo admin sem 2FA a configurá-lo antes de usar o sistema (`main.ts`, overlay bloqueante), o que contradiz a própria spec (obrigatório só em produção) e a decisão de produto de que o 2FA é opcional para todos. Além disso, a etapa de código aparece como um bloco injetado no card de login, sem rota própria, e o endpoint `POST /auth/2fa/verificar` não tem proteção contra força bruta: um código de 6 dígitos pode ser testado à vontade durante os 5 minutos do token parcial.

## What Changes

- **BREAKING (comportamento)**: remover a obrigatoriedade de 2FA para administradores, incluindo o overlay `forcarSetup2FA` e a checagem em `main.ts`. Nenhum perfil é forçado a ativar 2FA.
- Remover o aviso de startup sobre admins sem 2FA em `Settings.validar_para_producao()`.
- Nova rota de frontend `/login/2fa` com tela dedicada para informar o código TOTP ou um código de backup, seguindo o padrão do `/convite/:token` (detecção por `location.pathname` no boot + `history.pushState` na transição).
- O `token_temporario` fica apenas em memória no módulo do frontend: nunca na URL nem em `localStorage`/`sessionStorage`. Sem token pendente, acessar `/login/2fa` redireciona para `/login`. Recarregar a página volta ao login.
- "Voltar ao login" passa a cancelar de fato o fluxo: limpa o token em memória e retorna a `/login`.
- Backend: rate limit em `POST /auth/2fa/verificar`, com chave por usuário, reaproveitando `LimitadorDeLogin`.
- Backend: o token parcial é invalidado após 5 erros de código, forçando novo login com senha.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `autenticacao-2fa`: remove o requisito de 2FA obrigatório para admin em produção; declara o 2FA como opcional para todos; adiciona a rota dedicada `/login/2fa` e seu comportamento (token só em memória, redirecionamento sem token, cancelamento); adiciona limite de tentativas e invalidação do token parcial após 5 erros no segundo fator.

## Impact

- **Frontend**: `frontend/src/main.ts` (remove ramo de 2FA obrigatório, passa a detectar `/login/2fa`), `frontend/src/ui/login.ts` (remove `forcarSetup2FA`, substitui `mostrarTela2FA` por tela de rota), possível novo módulo para a tela/rota de 2FA, `frontend/src/styles/login.css`.
- **Backend**: `backend/app/routers/auth_2fa.py` (rate limit e contagem de erros em `/verificar`), `backend/app/ratelimit.py` (reuso ou instância dedicada), `backend/app/config.py` (remove aviso de admin sem 2FA). O token parcial precisa de um identificador para poder ser invalidado (ver design).
- **Spec**: `openspec/specs/autenticacao-2fa/spec.md`.
- **Infra**: nenhuma mudança. O catch-all de SPA em `backend/app/main.py` já serve `index.html` para `/login/2fa`.
- **Testes**: backend (limite e invalidação em `/verificar`), frontend/e2e (rota, redirecionamento sem token, cancelamento, ausência do overlay para admin).
- **Contrato de API**: `POST /auth/2fa/verificar` passa a poder responder `429`. Sem outras mudanças de contrato.
