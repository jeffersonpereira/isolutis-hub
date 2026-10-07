## Context

- `titulos.ts` já filtra `plano.filter(tipo_conta==="A")` e por `natureza` (`P`→`D`, `R`→`R`). Pelo código a lógica está correta; a causa real é desconhecida (hipóteses: nenhuma analítica da natureza certa; natureza dos filhos inconsistente em dados antigos; falha silenciosa de `plano.listar()` por `X-Empresa-ID`).
- 2FA: `/auth/2fa/setup` grava `totp_secret` antes da confirmação (cada chamada troca o segredo); `/confirmar` incrementa `versao_sessao` e devolve novo JWT via `criar_token(usuario.id, versao)`; o front chama `sessaoToken.definir()` e depois `render()`. Causa do defeito ainda não reproduzida.

## Goals / Non-Goals

**Goals:**
- Causa-raiz comprovada (log/Rede/console) antes de cada correção.
- Estados explícitos no select de conta: carregando, vazio (com dica), erro (com repetir).
- Ativação do 2FA concluindo e mantendo o usuário logado na empresa ativa.

**Non-Goals:**
- Redesenhar o plano de contas ou o fluxo de 2FA no login.
- Combobox pesquisável (change `combobox-pesquisavel`).

## Decisions

- **Diagnóstico primeiro**: tarefas 1.x reproduzem com backend + front rodando e registram a causa no próprio tasks.md. Alternativa descartada: corrigir por suposição.
- **Natureza é verdade do backend**: se houver dados inconsistentes, corrige-se com migração idempotente (filha herda a natureza da raiz) e a validação existente em `servicos.py` passa a ser coberta por teste; o front não "adivinha" natureza.
- **Erro ≠ vazio**: falha em `tentar()` mostra estado de erro com ação de repetir; lista vazia mostra a dica já existente.
- **Setup 2FA idempotente na UI**: desabilitar o botão "Ativar 2FA" enquanto o fluxo está aberto; backend mantém o contrato atual.

## Risks / Trade-offs

- [Causa pode estar em ambiente/dados e não em código] → registrar evidência; se for dado, entregar migração e script de verificação.
- [Mudar token na confirmação afeta sessão] → teste e2e: ativar 2FA e navegar para outra tela sem novo login.

## Open Questions

- Sintoma exato do 2FA (QR não aparece / código recusado / volta a "Desativado")? Será confirmado na reprodução.
