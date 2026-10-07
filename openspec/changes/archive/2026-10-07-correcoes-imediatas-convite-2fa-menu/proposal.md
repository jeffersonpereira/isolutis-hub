## Why

Três problemas independentes, pequenos e sem dependência de design, precisam ser corrigidos antes das mudanças maiores (multi-empresa, design system, parceiros por papel):

1. **Falha de segurança no aceite de convite.** Quando o e-mail convidado já tem conta, `aceitar_convite` sobrescreve a senha do usuário, reativa a conta e devolve o token de acesso sem checar 2FA nem invalidar sessões antigas. Com usuários passando a pertencer a várias empresas, qualquer pessoa com acesso ao link do convite poderia tomar uma conta existente e contornar o 2FA.
2. **2FA inacessível para quem não é administrador.** A spec `autenticacao-2fa` diz que qualquer usuário pode ativar o 2FA, mas a seção "Segurança" está dentro da tela "Dados da empresa", registrada como `somenteAdmin`. A escolha de usar 2FA é pessoal e hoje só administradores chegam a ela.
3. **Menu lateral estreito e com rolagem destoante.** A barra tem 220px, a rolagem é a nativa do navegador e o limite de altura do `nav` usa um número fixo (`100vh - 380px`) que quebra quando o bloco "Usando agora" cresce.

## What Changes

- **Convite para conta existente:** o aceite deixa de definir senha. `GET /auth/convite/{token}` informa se já existe conta para o e-mail; o front pede login normal (com 2FA, se ativo) e só então chama o aceite autenticado. O servidor confere que o usuário autenticado é o dono do e-mail do convite. Conta nova segue o fluxo atual (define senha).
- **Aceite nunca reativa conta desativada globalmente** nem altera `senha_hash` de conta existente.
- **BREAKING (contrato da API):** `POST /auth/convite/{token}/aceitar` passa a ter dois modos. Conta existente exige `Authorization` e ignora senha; conta nova continua exigindo `senha` e `confirmar_senha`. `ConviteInfo` ganha o campo `conta_existente`.
- **Nova tela "Minha conta"** acessível a todos os usuários, com a seção de 2FA e o botão de trocar senha. A seção "Segurança" sai de "Dados da empresa", que continua exclusiva de administradores.
- **Menu lateral:** largura de 220px para 272px, rolagem fina e harmonizada com o tema (claro e escuro), e `nav` passa a ocupar o espaço restante da barra por layout flex, sem altura calculada à mão. O layout móvel (faixa de abas) permanece como está.
- **Testes backend de convite**, que hoje não existem.

Fora de escopo (ficam nas changes seguintes): tela de escolha de empresa, papéis `financeiro` e `comercial`, topbar, ícones, criação restrita de empresas, remoção de `Usuario.admin`.

## Capabilities

### New Capabilities
- `minha-conta`: tela pessoal acessível a todo usuário autenticado, com preferências de segurança (2FA) e troca de senha.

### Modified Capabilities
- `convite-equipe`: aceite de convite por e-mail que já tem conta passa a exigir autenticação do próprio usuário, sem redefinir senha, sem reativar conta e respeitando o 2FA.
- `autenticacao-2fa`: a configuração de 2FA fica acessível a qualquer usuário, na tela "Minha conta", e deixa de depender do perfil de administrador.
- `scrollable-sidebar-menu`: largura ampliada, barra de rolagem discreta no tema e altura do menu definida por layout flexível.

## Impact

- **Banco:** nova migration `0009` (`0009_aceite_convite_rls.sql`, `_down` e revisão Alembic) com a função `vincular_membro_por_convite`. Sem ela, o aceite não consegue criar a membership com o papel de runtime da API, por causa das políticas RLS de `usuario_empresa`. Deve ser aplicada **antes** do deploy do backend.
- **Backend:** `app/services/convites.py` (`aceitar_convite`, `verificar_convite_publico`), `app/routers/auth.py` (aceite autenticado opcional), `app/schemas/convite.py` (`ConviteInfo.conta_existente`), novos testes em `backend/tests/`. `backend/openapi.json` e `frontend/src/api/schema.d.ts` não são regenerados nesta change (já divergem do backend por motivos anteriores); os tipos de convite do front são escritos à mão.
- **Frontend:** `ui/convite.ts` (fluxo de login para conta existente), `features/empresa.ts` (remove "Segurança"), nova vista `features/conta.ts` registrada em `main.ts`, `styles/layout.css` e `styles/responsive.css`.
- **Segurança:** fecha o vetor de tomada de conta e de contorno do 2FA pelo link de convite.
- **Compatibilidade:** convites já emitidos continuam válidos. O comportamento só muda para e-mails que já têm conta.
- **Dependências novas:** nenhuma.
