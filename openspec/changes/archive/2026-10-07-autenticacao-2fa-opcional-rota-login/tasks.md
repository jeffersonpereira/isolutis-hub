## 1. Backend — token parcial e proteção do segundo fator

- [x] 1.1 Em `backend/app/security.py`, fazer `ler_token` devolver `None` quando o payload contiver `requer_2fa` (token parcial nunca é token de acesso)
- [x] 1.2 Em `backend/app/routers/auth.py`, incluir claim `jti` (UUID) em `_criar_token_parcial`
- [x] 1.3 Em `backend/app/ratelimit.py`, parametrizar a mensagem de `MuitasTentativas` (padrão atual preservado para login) e criar `limitador_de_2fa` (`maximo=10`, janela 300 s)
- [x] 1.4 Em `backend/app/ratelimit.py`, adicionar controle de tentativas por `jti` (contador, conjunto de revogados, expiração de 5 min, limite de 5 erros)
- [x] 1.5 Em `POST /auth/2fa/verificar`: exigir `jti` no token parcial, rejeitar `jti` revogado, aplicar `limitador_de_2fa` com chave `2fa|<usuario_id>` antes de validar o código
- [x] 1.6 Em `POST /auth/2fa/verificar`: registrar falha (limitador e contador do `jti`) em cada código inválido, revogar o `jti` no 5º erro com `NaoAutenticado` pedindo novo login, e zerar/revogar o `jti` no sucesso (uso único)
- [x] 1.7 Em `backend/app/config.py`, remover o aviso de admin sem 2FA de `validar_para_producao()`

## 2. Frontend — remover obrigatoriedade e criar a rota `/login/2fa`

- [x] 2.1 Remover `forcarSetup2FA` de `frontend/src/ui/login.ts` e o ramo `selecao.admin && !usuario.totp_ativo` de `frontend/src/main.ts`, com o import correspondente
- [x] 2.2 Criar módulo do token pendente em memória (`definir`, `obter`, `existe`, `limpar`) sem uso de URL, `localStorage` ou `sessionStorage`
- [x] 2.3 Criar a tela dedicada do segundo fator (código TOTP, alternância para código de backup, estados de carregando, erro e desabilitado) substituindo `mostrarTela2FA` em `login.ts`
- [x] 2.4 Em `login.ts`, ao receber `requer_2fa`, guardar o token em memória e fazer `history.pushState` para `/login/2fa`; tratar a etapa como resolvida com usuário ou cancelada (sem Promise pendente)
- [x] 2.5 Em `main.ts`, detectar `/login/2fa` no boot: sem token pendente, `history.replaceState` para `/login` e exibir o login
- [x] 2.6 Implementar "Voltar ao login" e o botão voltar do navegador em `/login/2fa`: limpar o token, voltar a `/login` e focar o e-mail
- [x] 2.7 Tratar a invalidação do token (401 após 5 erros) e o `429`: limpar o token, voltar a `/login` e exibir mensagem pedindo para entrar novamente ou aguardar
- [x] 2.8 Ajustar `frontend/src/styles/login.css` para a tela do segundo fator (hierarquia, foco, responsividade, acessibilidade do campo de código com `autocomplete="one-time-code"`)
- [x] 2.9 Regenerar ou atualizar os tipos da API (`schema.d.ts`/`tipos.ts`) se o contrato do `/verificar` mudar (resposta `429`)

## 3. Testes

- [ ] 3.1 Backend: `ler_token` rejeita token parcial; `usuario_atual` responde 401 com token parcial mesmo com `versao_sessao == 0`
- [ ] 3.2 Backend: 5 códigos incorretos invalidam o `jti`; código correto depois do 5º erro é rejeitado
- [ ] 3.3 Backend: `jti` é de uso único após sucesso; token parcial sem `jti` é rejeitado
- [ ] 3.4 Backend: `limitador_de_2fa` devolve 429 após o limite por usuário e libera após a janela
- [ ] 3.5 Backend: backup code usado continua inválido; falha de backup code também conta como erro
- [x] 3.6 Frontend/e2e: admin sem 2FA entra sem overlay
- [x] 3.7 Frontend/e2e: login com 2FA leva a `/login/2fa`, URL sem token, código válido entra no painel
- [x] 3.8 Frontend/e2e: acesso direto e reload em `/login/2fa` redirecionam para `/login`
- [x] 3.9 Frontend/e2e: "Voltar ao login" descarta o token e permite novo login

## 4. Validação final

- [ ] 4.1 Rodar lint, type check e testes de backend e frontend
- [x] 4.2 Confirmar manualmente que `/login/2fa` é servido pelo fallback de SPA do backend (`_servir_frontend`) e pelo dev server do Vite
- [x] 4.3 Revisar o diff final (segurança, ausência de token em URL/storage, remoção completa do código de 2FA obrigatório)
