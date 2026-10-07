## 1. Convite: aceite seguro no backend

- [x] 1.1 Em `schemas/convite.py`, tornar `senha` e `confirmar_senha` opcionais em `AceitarConviteEntrada` e adicionar `conta_existente: bool` a `ConviteInfo`
- [x] 1.2 Em `services/convites.py`, fazer `verificar_convite_publico` informar `conta_existente` pelo e-mail do convite
- [x] 1.3 Em `services/convites.py`, reescrever `aceitar_convite` com dois modos: conta nova (cria usuário com a senha, exigindo senha e confirmação) e conta existente (exige usuário autenticado dono do e-mail, não altera `senha_hash`, não reativa `Usuario.ativo`, cria ou reativa a membership com o papel do convite)
- [x] 1.4 Em `aceitar_convite`, ler o convite com `FOR UPDATE` para que aceites simultâneos do mesmo token resultem em um único sucesso
- [x] 1.5 Em `routers/auth.py`, resolver o usuário autenticado de forma opcional (Bearer sem `auto_error`) e repassá-lo ao serviço; manter a checagem "As senhas não conferem." só no modo conta nova
- [x] 1.6 Não regenerar `backend/openapi.json` nem `frontend/src/api/schema.d.ts`: ambos já divergem do backend por motivos anteriores a esta change (o `openapi.json` versionado é de outro projeto e o `UsuarioLeitura` gerado expõe `versao_sessao`, não `versao`), e regenerá-los traria ~14 mil linhas sem relação com o convite. Os tipos de convite do front são escritos à mão em `api/tipos.ts` (tarefa 3.1). Regeneração do contrato fica como limpeza separada

## 2. Convite: testes do backend

- [x] 2.1 Criar `backend/tests/test_convites.py` com os cenários de conta nova: aceite cria usuário e membership com o papel do convite, marca `usado_em`, rejeita senhas diferentes, token expirado e token já usado
- [x] 2.2 Cobrir conta existente: sem autenticação retorna 401 e nada muda (senha, `ativo`, memberships, convite pendente); autenticado como outro usuário retorna 403; autenticado como o dono cria a membership sem alterar `senha_hash`
- [x] 2.3 Cobrir conta desativada (aceite recusado, conta continua desativada), reconvite de membership removida (reativada com o novo papel) e `conta_existente` em `GET /auth/convite/{token}`
- [x] 2.4 Cobrir que o aceite de conta existente não contorna o 2FA: a única forma de obter o Bearer exigido continua sendo `/auth/login` seguido de `/auth/2fa/verificar` quando `totp_ativo`
- [x] 2.5 Cobrir o reuso do mesmo token (um sucesso, o segundo recebe "já utilizado"). Concorrência real não é testável nesta suíte (uma única conexão em transação externa); a serialização fica a cargo do `FOR UPDATE` do serviço

## 3. Convite: fluxo no frontend

- [x] 3.1 Em `api/tipos.ts` e `api/endpoints.ts`, refletir `conta_existente` e o corpo opcional de `aceitar`
- [x] 3.2 Em `ui/convite.ts`, quando `conta_existente` for verdadeiro, exibir o convite com o aviso "Entre com <e-mail> para aceitar", sem campos de senha, e um botão "Entrar" que grava o token em `sessionStorage` (`hub.convite.pendente`) e navega para `/`
- [x] 3.3 Em `main.ts` (`principal()`), após obter o usuário e antes de `selecionarEmpresa()`, concluir o convite pendente: chamar o aceite autenticado, limpar a pendência em qualquer desfecho e avisar com toast o sucesso ou o motivo da recusa
- [x] 3.4 Garantir que o logout e o aceite concluído limpem `hub.convite.pendente`
- [x] 3.5 Teste unitário (vitest) da leitura e limpeza da pendência de convite

## 4. Minha conta e 2FA para todos

- [x] 4.1 Criar `features/conta.ts` com a vista `conta` ("Minha conta", sem `somenteAdmin`), movendo de `empresa.ts` o estado, a seção de 2FA e as ações `verificarStatus2fa`, `ativar2fa` e `desativar2fa`
- [x] 4.2 Na vista "Minha conta", consultar o estado do 2FA ao abrir (`api.auth.eu()`), sem botão intermediário "Verificar status", e oferecer o acesso a "Trocar senha" reutilizando `trocarSenha` de `ui/login.ts`
- [x] 4.3 Remover a seção "Segurança" e os imports de 2FA de `features/empresa.ts`, mantendo a vista restrita a administradores
- [x] 4.4 Importar `@/features/conta` em `main.ts` e confirmar a posição do item no menu para todos os papéis
- [x] 4.5 Atualizar `e2e/tests/login-2fa.spec.ts` se algum passo depender da antiga localização do 2FA e adicionar caso de membro não administrador ativando o 2FA

## 5. Menu lateral

- [x] 5.1 Em `styles/layout.css`, alterar a coluna da barra de `220px` para `272px` em `.app`
- [x] 5.2 Em `styles/layout.css`, trocar o `max-height: calc(100vh - 380px)` de `nav` por `flex: 1 1 auto; min-height: 0`, mantendo `.online` e `.conta` com `flex-shrink: 0`
- [x] 5.3 Aplicar rolagem fina ao `nav` (`scrollbar-width: thin`, `scrollbar-color` e `::-webkit-scrollbar`) usando variáveis de `tokens.css`; criar tokens para a cor do trilho e do polegar nos temas claro e escuro, se não existirem
- [x] 5.4 Em `styles/responsive.css`, confirmar que a faixa horizontal de abas (até 860px) não é afetada pelo `flex` e pela largura nova, ajustando se necessário
- [x] 5.5 Verificar visualmente no navegador: desktop com grupos expandidos, bloco "Usando agora" crescendo, tema escuro, Firefox e Chromium, e celular

## 6. Validação final

- [ ] 6.1 Rodar a suíte backend (`pytest`) e confirmar que os testes novos e os existentes passam
- [x] 6.2 Rodar `npm run typecheck`, `npm run lint` e `npm test` no frontend. Typecheck limpo; arquivos alterados sem erro de lint; testes novos passam (6/6) e o e2e de 2FA passa (8/8 no Chromium). Falhas anteriores a esta change, em arquivos não tocados: 6 erros de lint em `ui/formulario-helper.ts` e `ui/salvar-helper.ts`, e 1 teste em `ui/validators.test.ts` ("deve rejeitar NaN ou Infinity")
- [ ] 6.3 Executar manualmente o fluxo completo de convite para conta existente com 2FA ativo (login, código, aceite, nova empresa disponível no seletor)
- [x] 6.4 Revisar o diff final quanto a segurança, regressões e complexidade desnecessária

## 7. Migração 0009 do RLS do aceite

- [x] 7.1 Criar `migrations/sql/0009_aceite_convite_rls.sql`, o `_down` e `migrations/versions/0009_aceite_convite_rls.py` (função `vincular_membro_por_convite`, `EXECUTE` só para `hub_runtime`)
- [x] 7.2 Fazer `aceitar_convite` chamar a função em vez de inserir em `usuario_empresa` e marcar `usado_em`
- [x] 7.3 Criar `migrations/sql/0009-validacao-aceite-convite.sql` (estado do banco e teste de comportamento como `hub_runtime`, desfeito ao final)
- [x] 7.4 Validar a sintaxe SQL e plpgsql dos três scripts com `pglast` (sem banco)
- [x] 7.5 Conferir a revisão atual do banco remoto (esperado: `0008`) e aplicar `alembic upgrade head` com a credencial migradora. Feito na Neon: `0008` → `0009`
- [x] 7.6 Rodar `0009-validacao-aceite-convite.sql` no banco remoto e confirmar todas as linhas `[OK]`. Parte 1 conferida pelo `neondb_owner`; Parte 2 pela conexão `hub_runtime` (o owner não pode assumir esse papel). 4/4 `[OK]`, nada gravado
- [ ] 7.7 Publicar o backend e o front só depois de 7.5 e 7.6
