## Why

O modelo de dados já permite que um usuário pertença a várias empresas, cada uma com um papel (`usuario_empresa`), e que o isolamento seja feito por `X-Empresa-ID` + RLS. A experiência e a autorização, porém, não acompanham:

- **A empresa ativa é escolhida em silêncio** (a última lembrada no `localStorage` ou a primeira da lista). Não há etapa explícita após o login, e a troca é um `<select>` oculto quando há uma empresa só.
- **Só existem os papéis `admin` e `membro`**, e **a maioria dos routers não exige papel nenhum**: clientes, negócios, orçamentos, produtos, projetos, tarefas, despesas, faturamento, painel e relatórios (DRE e fluxo de caixa) aceitam qualquer membro da empresa. O front apenas esconde alguns menus (`somenteAdmin`).
- **Qualquer usuário logado pode criar uma empresa** (`POST /empresas` e a função SQL `criar_empresa`, liberada ao papel de runtime). A criação deve ser restrita ao operador da plataforma.
- **`Usuario.admin` é um flag global vestigial** (sempre falso), enquanto a autorização real usa `usuario_empresa.papel`. Os dois coexistem na API e no schema.

Esta change fecha essas lacunas antes dos cadastros de usuários e de parceiros por papel, que dependem de um modelo de papéis confiável.

## What Changes

- **Tela "Em qual empresa quer trabalhar?"** exibida sempre após o login (inclusive com uma única empresa). Cada cartão mostra o nome da empresa e o papel do usuário nela. Se não houver nenhuma empresa ativa, a tela explica que a conta não tem acesso e oferece sair.
- **Troca de empresa** a qualquer momento, pelo bloco de conta da barra lateral (nome e papel da empresa ativa sempre visíveis), reabrindo a escolha. A troca recarrega a aplicação para que nenhum dado em memória vaze entre empresas.
- **Escolha por aba:** a empresa ativa passa a viver em `sessionStorage`; `localStorage` guarda só a "última usada", como sugestão pré-selecionada na tela de escolha. O logout limpa os dois.
- **Quatro papéis por empresa:** `admin`, `financeiro`, `comercial` e `membro`, com a matriz de permissões abaixo. A autorização passa a usar `exige(permissao)` em vez de `papel == "admin"`.
- **Autorização aplicada no backend** a todos os routers conforme a matriz, e consumida pelo front (menu, carga de dados, painel).
- **Criação de empresas restrita ao operador:** remove `POST /empresas` e revoga a execução de `criar_empresa` do papel de runtime. A criação continua pelo script `criar_admin`, que usa a credencial migradora.
- **`Usuario.admin` removido** do banco, do modelo e da API. Onde a API devolvia `admin: bool`, passa a devolver `papel`.
- **Migração de dados:** as memberships com papel `membro` existentes viram `comercial`, para que ninguém perca o acesso comercial que já usa; `admin` permanece. Novos `membro` nascem com acesso básico.
- **BREAKING (API):** `admin: bool` sai de `UsuarioLeitura`, `UsuarioCriar` e `UsuarioAtualizar` e entra `papel`; o papel do convite aceita os quatro valores; `POST /empresas` deixa de existir; rotas comerciais e financeiras passam a responder 403 a papéis sem permissão.
- **BREAKING (comportamento):** Faturamento, Despesas e Relatórios (DRE e fluxo de caixa) deixam de abrir para quem não é `admin` ou `financeiro`.

### Matriz de permissões

| Permissão | O que cobre | admin | financeiro | comercial | membro |
|---|---|:-:|:-:|:-:|:-:|
| `base` | painel (só os blocos permitidos), tarefas, projetos, lista de responsáveis (`/equipe`), lista mínima de clientes (id e nome), Minha conta, seleção de empresa | ✓ | ✓ | ✓ | ✓ |
| `comercial` | clientes (cadastro completo), negócios, orçamentos, produtos | ✓ | | ✓ | |
| `financeiro` | módulo `/financeiro`, hub de parceiros (fornecedores), faturamento, despesas, relatórios DRE e fluxo de caixa | ✓ | ✓ | | |
| `administracao` | usuários, convites, dados da empresa, onboarding | ✓ | | | |

Esta matriz parte das respostas dadas (Faturamento e Despesas só para `admin` e `financeiro`; `membro` básico). Dois pontos foram **inferidos** e precisam de confirmação: relatórios (DRE e fluxo de caixa) ficam em `financeiro`, e a lista mínima de clientes (id e nome) fica em `base` para que nomes e seletores continuem funcionando em projetos, tarefas e faturamento.

Fora de escopo: topbar, ícones e design system; cadastro completo de empresa; evolução da tela de usuários; parceiros por papel; papéis editáveis por empresa (RBAC configurável); política de 2FA obrigatório.

## Capabilities

### New Capabilities
- `selecao-empresa`: escolha obrigatória e explícita da empresa ativa após o login, troca posterior, persistência por aba e limpeza no logout.
- `papeis-permissoes`: papéis `admin`, `financeiro`, `comercial` e `membro` por empresa, matriz de permissões imposta no backend e refletida no front.
- `provisionamento-de-empresas`: empresas só são criadas pelo operador da plataforma, nunca por usuários da aplicação.

### Modified Capabilities
- `convite-equipe`: o convite passa a aceitar os quatro papéis, e o papel escolhido é o aplicado na membership.

## Impact

- **Banco:** nova migration `0010` (SQL + revisão Alembic + `down`): troca a constraint `ck_usuario_empresa_papel` para os quatro valores, converte `membro` em `comercial`, remove `usuarios.admin`, revoga `EXECUTE` de `criar_empresa` para `hub_runtime`. As políticas RLS que usam `app_empresa_admin` continuam válidas, pois `admin` segue sendo o valor literal `'admin'`.
- **Backend:** `deps.py` (`exige(permissao)`, mapa papel→permissões), `main.py` (dependências por router), todos os routers de `app/routers/` e `app/financeiro/rotas.py`, `routers/equipe.py` (remove `POST /empresas`; `GET /empresas` devolve `papel` e `permissoes`), `routers/painel.py` e `services/painel.py` (blocos por permissão), `routers/clientes.py` (lista mínima), `schemas/usuario.py` e `schemas/convite.py`, `services/usuarios.py` e `services/convites.py`, `models/usuario.py`, `scripts/criar_admin.py`. `openapi.json` e `schema.d.ts` regenerados.
- **Frontend:** `main.ts` (fluxo de login, escolha e troca), `api/http.ts` (empresa por aba), nova tela de escolha, `state/nucleo.ts` (`somenteAdmin` vira permissão, carregadores por permissão e tolerantes a erro), `state/estado.ts`, helpers `nomeCliente` e `seletorCliente`, `features/equipe.ts` e `ui/convite.ts` (seleção de papel), `features/painel.ts`, `index.html` e `styles/layout.css` (bloco de empresa ativa).
- **Testes:** os testes existentes que usam `papel="membro"` esperando acesso comercial ou `admin` no schema precisam ser atualizados; novos testes de matriz de permissões, de isolamento entre empresas e de escolha de empresa.
- **Dependência de ordem:** deve ser aplicada **depois** de `correcoes-imediatas-convite-2fa-menu`, que também altera o fluxo de convite e o bootstrap de `main.ts`.
- **Dependências novas:** nenhuma.
