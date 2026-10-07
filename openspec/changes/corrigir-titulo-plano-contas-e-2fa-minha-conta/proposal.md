## Why

Dois defeitos relatados em uso: (1) no lançamento de título financeiro o campo "Conta do plano de contas" não lista contas; (2) na tela "Minha conta" a ativação do 2FA não funciona. Ambos bloqueiam fluxos básicos e ainda não foram reproduzidos, então a change começa por diagnóstico guiado por evidência (não por suposição).

## What Changes

- Reproduzir e corrigir a falta de contas no lançamento de título: contas carregadas pela natureza do título (a pagar → despesa `D`; a receber → receita `R`), somente analíticas.
- Garantir feedback explícito quando a lista não puder ser carregada ou estiver vazia (erro vs. vazio), em vez de um select silenciosamente vazio.
- Reproduzir e corrigir a ativação do 2FA em "Minha conta" (setup → QR → confirmação → estado "Ativado"), inclusive a continuidade da sessão após a troca de token.
- Tornar o setup idempotente na UI (evitar invalidar o QR/backup codes por clique duplo) e exibir mensagem de erro útil.
- Testes de regressão (backend e front) cobrindo os dois fluxos.

## Capabilities

### New Capabilities
- `titulos-financeiros`: regras de seleção da conta do plano de contas no lançamento de título (natureza × tipo, somente analíticas, estados de carregamento/vazio/erro).

### Modified Capabilities
- `minha-conta`: acrescenta requisitos de robustez da ativação do 2FA (sessão preservada, setup idempotente, erro claro).

## Impact

- Frontend: `features/financeiro/titulos.ts`, `features/financeiro/api.ts`, `features/conta.ts`, `ui/login.ts`.
- Backend: `app/financeiro/servicos.py` / listagem do plano (se a causa for dado/herança de natureza), `app/routers/auth_2fa.py`, `app/security.py` (token emitido na confirmação).
- Possível migração de dados corretiva se contas filhas existentes tiverem natureza inconsistente.
- Sem mudança de contrato público de API prevista.
