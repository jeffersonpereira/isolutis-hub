## Context

O 2FA TOTP já existe (change `onda-2`): `POST /auth/login` devolve `{requer_2fa, token_temporario}` para quem tem `totp_ativo`, e `POST /auth/2fa/verificar` troca o token parcial por um JWT completo. Problemas atuais:

- `main.ts` chama `forcarSetup2FA()` para todo admin sem 2FA, em qualquer ambiente. Isso contradiz a decisão de que o 2FA é opcional.
- A etapa do código é um bloco injetado no card de login (`mostrarTela2FA`), sem rota. "Voltar ao login" deixa a Promise sem resolução.
- `/verificar` não tem limite de tentativas. O token parcial vale 5 minutos e o código tem 6 dígitos.
- O token parcial (`requer_2fa=True`, sem `sv`) é lido por `ler_token` como versão 0 e `usuario_atual` o aceita se `usuario.versao_sessao == 0`. Hoje isso não explora o 2FA porque `confirmar_2fa` incrementa `versao_sessao`, mas depende dessa coincidência.

O frontend não tem router. A única rota é `/convite/:token`, detectada por regex em `location.pathname` no boot (`detectarRotaConvite`). O backend já serve `index.html` para qualquer path desconhecido (`_servir_frontend`, catch-all em `main.py`), então `/login/2fa` não exige mudança de infra.

## Goals / Non-Goals

**Goals:**
- 2FA opcional para todos, sem exceção por perfil ou ambiente.
- Rota `/login/2fa` com tela dedicada, sem o token temporário em URL ou storage.
- Limitar tentativas de código e invalidar o token parcial após 5 erros.
- Garantir que o token parcial nunca funcione como token de acesso.

**Non-Goals:**
- Introduzir um router genérico (`history` + `popstate` para todas as telas).
- Persistir contadores de tentativa em banco ou Redis.
- Alterar o fluxo de ativação/desativação do 2FA em Configurações.
- Alterar o formato do JWT de acesso.
- Política de 2FA obrigatório configurável por empresa.

## Decisions

### D1. Remover a obrigatoriedade de 2FA por completo
Apagar `forcarSetup2FA`, seu uso em `main.ts` e o aviso de admin sem 2FA em `Settings.validar_para_producao()`. Sem flag de configuração.
*Alternativa*: manter obrigatório só em produção, como na spec antiga. Rejeitada: a decisão de produto é opcional para todos, e uma flag nunca usada é código morto.

### D2. Rota `/login/2fa` no padrão do `/convite`
No boot, `main.ts` já decide entre convite e fluxo normal. A transição login → 2FA faz `history.pushState({}, "", "/login/2fa")`. Não há `popstate` global: o botão "voltar" do navegador estando em `/login/2fa` é tratado dentro do módulo da tela, que chama o mesmo cancelamento de "Voltar ao login".
*Alternativa*: router completo. Rejeitada: infraestrutura desproporcional para uma rota.

### D3. Token temporário apenas em memória
Um módulo de frontend (`ui/segundo-fator.ts`) guarda `tokenPendente: string | null` em variável de módulo, com `definir`, `consumir` e `limpar`. Nunca vai à URL, a `localStorage` nem a `sessionStorage`. Entrar em `/login/2fa` sem token pendente (acesso direto ou reload) executa `history.replaceState` para `/login` e mostra o login.
*Alternativa*: `sessionStorage`. Rejeitada: expõe um token de 5 min a XSS e sobrevive ao reload, o que o fluxo não precisa.

### D4. Contagem de erros por token parcial, em memória
O token parcial ganha um claim `jti` (UUID). O backend mantém em memória, no módulo do limitador, um contador de falhas por `jti` e um conjunto de `jti` revogados, ambos com expiração alinhada aos 5 minutos do token.
- Cada erro de código (TOTP ou backup) em `/verificar` incrementa o contador do `jti`.
- No 5º erro o `jti` é revogado e a resposta é `401` com mensagem pedindo novo login com senha.
- Token com `jti` revogado é rejeitado como `NaoAutenticado`, mesmo com código correto.
- Sucesso zera o contador e revoga o `jti` (uso único).

*Alternativa*: coluna no banco. Rejeitada: o `LimitadorDeLogin` existente já é em memória e o custo de uma migração não se justifica para uma janela de 5 min.
*Alternativa*: só contar por usuário. Rejeitada: não "invalida o token", apenas freia.

### D5. Rate limit por usuário em `/verificar`
Reaproveitar `LimitadorDeLogin` com uma instância dedicada (`limitador_de_2fa`), chave `2fa|<usuario_id>`, `maximo=10`, janela 300 s. Chamar `verificar(chave)` antes de validar o código, `registrar_falha` em cada erro e `zerar` no sucesso. A chave é por usuário, não por IP, porque o atacante já possui um token parcial válido e pode trocar de IP; o `jti` (D4) cobre a tentativa isolada e o limitador por usuário cobre novos logins repetidos com a senha conhecida. A mensagem de `MuitasTentativas` hoje fala de "login"; torná-la parametrizável sem quebrar o uso atual.

### D6. Token parcial nunca é token de acesso
`ler_token` passa a devolver `None` quando o payload tem `requer_2fa`. `usuario_atual` não muda. Defesa em profundidade: remove a dependência de `versao_sessao != 0`.

### D7. Cancelar de verdade
"Voltar ao login" chama `limpar()` no módulo do token, faz `history.replaceState` para `/login`, remove a tela de 2FA e devolve o foco ao e-mail. O fluxo de `pedirLogin` passa a tratar a ida ao 2FA como uma etapa que pode terminar em sucesso (usuário) ou cancelamento (volta ao formulário), em vez de uma Promise que nunca resolve.

## Risks / Trade-offs

- **[Estado em memória não é compartilhado entre instâncias/serverless]** Em mais de uma instância, o contador por `jti` e o limitador valem por processo, e o atacante pode distribuir tentativas. → Mesma limitação do `limitador_de_login` atual; o TOTP tem janela curta e o token expira em 5 min. Registrar como limitação; migrar os dois limitadores juntos para um store compartilhado se o deploy escalar horizontalmente.
- **[Restart do processo zera contadores e revogações]** → Aceitável: o token parcial expira em 5 min e o usuário volta ao login com senha.
- **[Reload em `/login/2fa` volta ao login]** O usuário perde o progresso e redigita a senha. → Trade-off intencional da decisão D3.
- **[Remoção da exigência para admin reduz a postura de segurança]** → Decisão de produto explícita; o 2FA continua incentivado na tela de Configurações.
- **[`jti` novo no token parcial]** Tokens parciais emitidos antes do deploy não têm `jti`. → Tratar ausência de `jti` como token inválido; vale no máximo 5 min, o usuário refaz o login.

## Migration Plan

1. Deploy único de backend e frontend; não há migração de banco.
2. Usuários com 2FA já ativo não são afetados. Admins sem 2FA deixam de ver o overlay e entram direto.
3. Rollback: reverter o deploy. Não há estado persistido novo.
4. Efeito colateral no deploy: logins em andamento na etapa de código precisam ser refeitos (tokens parciais sem `jti`).

## Open Questions

Nenhuma. Decididos com o usuário: opcional para todos, rota dedicada, token só em memória, invalidação após 5 erros.
