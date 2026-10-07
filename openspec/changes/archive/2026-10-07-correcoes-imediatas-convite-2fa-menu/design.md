## Context

**Convite.** `services/convites.aceitar_convite` aceita um token público e, se o e-mail já tem `Usuario`, executa `senha_hash = gerar_hash(senha)` e `ativo = True`. O router devolve `criar_token(...)` direto, sem passar pela checagem de `totp_ativo` que existe em `/auth/login`, e sem alterar `versao_sessao`. O token do convite não aparece em `ConviteLeitura`; sai apenas por e-mail. Mesmo assim, quem lê a caixa de entrada do convidado toma a conta e contorna o 2FA. Não há nenhum teste backend de convite.

**2FA.** Os endpoints `/auth/2fa/*` só exigem usuário logado. O bloqueio está no front: `fluxoAtivar2FA` e `fluxoDesativar2FA` são chamados de `features/empresa.ts`, vista registrada com `somenteAdmin: true`.

**Menu.** `aside` fica numa coluna de `220px` (`.app` em `layout.css`). `nav` usa `max-height: calc(100vh - 380px)` com `overflow-y: auto`. No móvel (`responsive.css`, `max-width: 860px`) a barra vira uma faixa horizontal e `nav` vira `flex-direction: row`.

**Fluxo de login no front.** `pedirLogin` opera sobre elementos do `index.html` (`#login`, `#lgEntrar`). A etapa de 2FA empurra `/login/2fa` na história e, ao concluir, faz `replaceState` para `/`. A página de convite (`ui/convite.ts`) monta o próprio DOM e roda fora de `principal()`.

## Goals / Non-Goals

**Goals:**
- Impedir que o aceite de convite altere credenciais ou contorne 2FA de uma conta existente.
- Permitir que qualquer usuário configure o próprio 2FA.
- Menu mais largo, com rolagem discreta e sem altura calculada à mão.
- Cobrir o fluxo de convite com testes.

**Non-Goals:**
- Tela de escolha de empresa, papéis novos, topbar, ícones e design system (changes seguintes).
- Política de 2FA obrigatório por empresa.
- Remover `Usuario.admin` e restringir `POST /empresas` (change de multi-empresa).
- Alterar a emissão, a expiração ou o envio de convites.

## Decisions

### D1. Aceite em dois modos, decidido pelo servidor
`aceitar_convite` procura o `Usuario` pelo e-mail do convite:

```
 conta NÃO existe  → cria Usuario com senha do corpo (comportamento atual)
 conta existe      → exige usuário autenticado (Bearer) cujo id == dono do e-mail;
                     NÃO toca em senha_hash; NÃO altera Usuario.ativo; só cria/ativa a membership
```

Regras no modo "conta existe":
- Sem `Authorization` válido: `NaoAutenticado` com mensagem pedindo para entrar com a conta do convite.
- Autenticado como outro usuário: `SemPermissao` ("Este convite é para outro e-mail").
- `Usuario.ativo` falso: `RegraDeNegocio`, sem reativar.
- Membership existente (inativa ou com outro papel): reativada com o papel do convite, o que preserva o caso de reconvidar alguém removido da equipe.
- Resposta: `TokenSaida` com token para a mesma `versao_sessao`, mantendo o contrato de resposta.

`senha` e `confirmar_senha` passam a ser opcionais no schema; a obrigatoriedade para conta nova é validada no serviço (a mensagem "As senhas não conferem." continua no router).

**Alternativa descartada:** manter o aceite público e apenas bloquear quando o usuário existir. Impediria a feature de várias empresas, que precisa justamente de convite para quem já tem conta.
**Alternativa descartada:** exigir a senha atual da conta existente no corpo do aceite. Não aplica o 2FA, que só o `/login` aplica.

### D2. `conta_existente` em `ConviteInfo`
`verificar_convite_publico` informa `conta_existente: bool`. Quem tem o token já conhece o e-mail do convite (ele aparece na resposta), portanto o campo não amplia o que o portador do link já sabe. A rota continua sem listar nem confirmar e-mails a quem não tem o token.

### D3. No front, o login normal conclui o aceite
Reaproveitar `pedirLogin` dentro da página de convite não funciona: ele depende do DOM do `index.html` e o fluxo de 2FA troca a URL para `/`. Em vez disso:

```
 /convite/:token (conta_existente = true)
   └─ mostra "Entre com <email> para aceitar" + botão "Entrar"
        └─ grava token em sessionStorage ("hub.convite.pendente") e vai para "/"
             └─ login normal (+ 2FA, se ativo)           ← fluxo existente, sem alteração
                  └─ principal(): antes de selecionarEmpresa(), se há convite pendente:
                       POST aceitar (Bearer) → limpa pendência → toast
                       erro 403/4xx → limpa pendência e avisa o motivo
```

O token pendente usa `sessionStorage` (some ao fechar a aba) e é removido em qualquer desfecho. Se já houver sessão ativa do próprio dono do e-mail, `principal()` aceita direto.

**Alternativa descartada:** ligar `ui/convite.ts` ao DOM de login e ao 2FA. Duplicaria a lógica de login e de 2FA, e hoje já existem duas fontes.

### D4. Concorrência no aceite
O `SELECT` do convite no aceite usa `FOR UPDATE`, para que dois aceites simultâneos do mesmo token não criem duas memberships nem dois usuários. Correção barata e local; sem mudança de schema.

### D7. Membership do aceite por função SECURITY DEFINER (migração 0009)
`usuario_empresa` tem `FORCE ROW LEVEL SECURITY` e as políticas de INSERT e UPDATE exigem `empresa_id = app_empresa_id()` e `app_empresa_admin(...)`. O aceite é público (sem empresa ativa) e quem aceita ainda não é administrador, então, como `hub_runtime` (sem BYPASSRLS), o INSERT/UPDATE direto seria recusado. Os testes não revelam isso porque conectam como superusuário.

Nova função `vincular_membro_por_convite(p_convite_id, p_usuario_id)`, no padrão de `criar_empresa` (`SECURITY DEFINER`, `search_path` fixo, `row_security = off`, `EXECUTE` só para `hub_runtime`). Ela bloqueia o convite (`FOR UPDATE`), confere que o convite pertence a um usuário **ativo** com aquele e-mail, que está pendente e dentro do prazo, cria ou reativa a membership com o papel do convite (`ON CONFLICT ... DO UPDATE`) e marca `usado_em`, tudo na mesma transação. O serviço deixa de inserir em `usuario_empresa` e de marcar `usado_em` e passa a chamar a função.

**Alternativa descartada:** políticas RLS que permitam o INSERT quando existir convite válido. A ordem de flush do ORM entre `convites` e `usuario_empresa` não é garantida, e a política poderia ver o convite já consumido.
**Alternativa descartada:** dar ao aceite o papel migrador. Contraria a regra do projeto de nunca usar a credencial migradora na API.

### D5. "Minha conta" como vista própria, sem `somenteAdmin`
Nova vista `conta` (`features/conta.ts`), com a seção de 2FA movida de `empresa.ts` (lógica de status, ativar e desativar) e o acesso à troca de senha (reutiliza `trocarSenha` de `ui/login.ts`). Aparece para todos. `empresa.ts` fica só com os dados da empresa. O backend não muda: os endpoints de 2FA já aceitam qualquer logado. A vista fica no menu como item de primeiro nível; o agrupamento definitivo vem com a change de configurações.

**Alternativa descartada:** manter "Segurança" em "Dados da empresa" e apenas remover o `somenteAdmin`. Exporia a edição do nome da empresa a quem não é admin e continuaria semanticamente errado.

### D6. Menu: largura e rolagem por CSS, altura por flex
- `.app` passa a `grid-template-columns: 272px minmax(0, 1fr)`.
- `aside` já é coluna flex com `height: 100vh`; `nav` recebe `flex: 1 1 auto; min-height: 0` e perde o `max-height` calculado. `.online` e `.conta` mantêm `flex-shrink: 0` e `margin-top: auto`, garantindo que continuem visíveis.
- Rolagem fina: `scrollbar-width: thin` e `scrollbar-color` com tokens do tema, mais `::-webkit-scrollbar` equivalente. A cor sai de variáveis de `tokens.css`, para valer no tema claro e no escuro.
- Móvel: o bloco de `max-width: 860px` redefine `nav` em linha; `flex` e `min-height` não devem afetar a faixa horizontal, o que é verificado manualmente.

## Risks / Trade-offs

- **[Backend novo sem a migration]** O serviço chama `vincular_membro_por_convite`; sem a `0009` no banco, o aceite falha. → Aplicar a `0009` **antes** do deploy do backend. A função é só adição (não altera tabelas), então o backend antigo continua funcionando com ela presente.
- **[Credencial do banco remoto]** As variáveis do Neon são do tipo Secret na Vercel e não podem ser lidas pelo CLI. → A migração é aplicada por quem tem a credencial migradora; `0009-validacao-aceite-convite.sql` confere o resultado sem gravar nada.
- **[Mudança no contrato do aceite]** Clientes antigos que enviam senha para conta existente passam a falhar com 401. → O único cliente é o próprio front, alterado na mesma change; `openapi.json` e `schema.d.ts` são regenerados.
- **[Convite aceito por quem não é o dono da conta]** Fica protegido pela comparação de id com o e-mail do convite. → Teste dedicado.
- **[Token de convite em `sessionStorage`]** É um segredo de uso único com expiração de 72 h. → Vive apenas na aba, é apagado em qualquer desfecho e só vale para o e-mail dono do convite.
- **[Nova empresa não vira a ativa após o aceite]** O usuário continua na empresa escolhida antes e recebe um aviso. → A tela de escolha de empresa chega na change seguinte; até lá o seletor da barra lateral permite trocar.
- **[Rolagem do menu no Safari e no Firefox]** `scrollbar-width` e `::-webkit-scrollbar` têm suporte diferente. → Aplicar os dois e conferir em Chromium e Firefox; sem suporte, o navegador cai na barra nativa, que é aceitável.
- **[Conta global desativada e membership ativa]** Um usuário com `ativo = false` não entra mesmo com membership válida (já é barrado em `usuario_atual`). → O aceite apenas deixa de reativar; reativação passa a ser decisão explícita fora deste fluxo.

## Migration Plan

1. Conferir a revisão atual do banco remoto (`SELECT version_num FROM alembic_version;`), que deve ser `0008`.
2. Aplicar `alembic upgrade head` com a credencial migradora (`HUB_MIGRATION_DATABASE_URL`).
3. Rodar `migrations/sql/0009-validacao-aceite-convite.sql` (a Parte 2 se desfaz sozinha).
4. Só então publicar o backend e o front.
5. **Rollback:** `alembic downgrade 0008` remove a função; o backend novo deixaria de aceitar convites até voltar a versão anterior.

## Open Questions

- Após aceitar o convite de outra empresa, vale já deixá-la como empresa ativa? Exigiria devolver o `empresa_id` no aceite. Adiado para a change de seleção de empresa.
