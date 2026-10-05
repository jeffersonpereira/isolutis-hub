# Arquitetura

## Visão geral

```
 Navegador (frontend/)                       Servidor (backend/)                       PostgreSQL
┌──────────────────────────┐   HTTPS/JSON   ┌───────────────────────────┐            ┌───────────────┐
│ views  ─ forms (gaveta)  │ ─────────────► │ routers  (HTTP, validação) │            │ tabelas       │
│ state  (store, nucleo)   │                │   │                        │  SQLAlchemy │ constraints   │
│ api    (cliente tipado)  │ ◄───────────── │ services (regras, UoW)     │ ──────────► │ triggers      │
│ domain (regras de tela)  │   WebSocket    │   │                        │  (async)    │ views         │
│ core   (html seguro...)  │ ◄────────────► │ domain   (regras puras)    │            └───────────────┘
└──────────────────────────┘ presença/avisos│ models   (ORM)             │
                                            │ realtime · documents · db  │
                                            └───────────────────────────┘
```

Separação de responsabilidades: **o navegador só apresenta e coleta**; **toda regra de negócio e todo cálculo agregado
vivem no servidor**; **a integridade final é do banco** (CHECK, FK, UNIQUE, triggers). Cada camada só conhece a de baixo.

## Backend (`backend/app`)

| Pasta | Responsabilidade | Não deve |
|---|---|---|
| `routers/` | Rotas HTTP finas: recebem/validam payload, chamam um serviço, serializam a resposta. | Conter regra de negócio ou SQL. |
| `schemas/` | Contrato da API (Pydantic): entrada (`*Entrada`, `*Atualizar`) e saída (`*Leitura`). Formato snake_case; dinheiro vira número JSON. | Conhecer o ORM além de `from_attributes`. |
| `services/` | Casos de uso e **unidade de trabalho**: carregam, aplicam regras, `commit()` uma vez por operação, traduzem violações em erros de negócio. | Conhecer HTTP/FastAPI. |
| `domain/` | Regras **puras** (sem I/O): totais de orçamento, status "vencido", parcelamento sem perder centavos, progresso de projeto, datas. | Importar SQLAlchemy/FastAPI. |
| `models/` | Mapeamento ORM do schema do DBA. Auditoria e `versao` são do banco; o ORM só lê. | Duplicar regras que o banco garante. |
| `documents/` | Documentos HTML ao cliente (orçamento, plano de entrega) por templates Jinja2 com autoescape. | — |
| `realtime.py` | Sala WebSocket: presença ("Usando agora") e aviso de "recurso X mudou". | — |
| `db.py`, `deps.py`, `security.py`, `errors.py`, `config.py` | Infra: sessão, autenticação, hash/JWT, erros padronizados, configuração por ambiente. | — |
| `scripts/` | Operação: `criar_admin`, `importar_legado`, `exportar_openapi`. | — |

### Decisões

- **Banco é a fonte da verdade da integridade.** O schema (docs/banco-de-dados.md) usa `CHECK` para enums e regras
  ("perdido exige motivo", "recebido exige data"), FKs compostas (negócio e cliente sempre coerentes), triggers de
  auditoria/versão e numeração de orçamento atômica por ano. A API devolve mensagens amigáveis, mas nunca confia só nela.
- **Auditoria transparente.** Cada requisição autenticada executa `set_config('app.usuario_id', …, true)`; o trigger
  `set_audit` preenche `criado_por/atualizado_por/versao`. Nenhum serviço precisa lembrar de carimbar.
- **Concorrência otimista.** O cliente envia a `versao` que leu. O serviço confere (409 com mensagem clara) e o ORM
  repete a checagem no `UPDATE … WHERE versao = :lida` (`version_id_col`), cobrindo a corrida entre a leitura e a gravação.
- **Operações compostas são atômicas no servidor**: aprovar orçamento (orçamento + negócio vira Ganho), gerar
  faturamento em lote (parcelas + mensalidades), repetir despesa/lançamento por N meses, avançar o negócio para "Proposta"
  ao enviar o orçamento. No sistema anterior eram vários gravamentos soltos no navegador.
- **Agregações no SQL.** Painel, resumo mensal de faturamento e resultado (recebido − despesas pagas) são calculados no
  banco; o navegador não baixa todos os registros para somar.
- **Autenticação própria.** E-mail + senha (Argon2id), JWT assinado de curta duração, usuário reconsultado a cada
  requisição (desativar alguém vale na hora), versão de sessão incrementada quando a senha muda (tokens anteriores deixam
  de valer), freio a tentativas de login por e-mail+IP, cabeçalhos de segurança e CSP.
  Troca de senha pelo próprio usuário; redefinição pelo administrador (sem depender de e-mail).
- **Tempo real sem polling.** Depois de cada `commit`, um hook da sessão publica quais recursos mudaram; os clientes
  recarregam só o necessário. A sala vive em memória (instância única); para várias instâncias troque por
  LISTEN/NOTIFY ou Redis sem mudar as rotas.
- **Contrato único.** `python -m app.scripts.exportar_openapi` gera `backend/openapi.json`; o frontend gera os tipos
  TypeScript a partir dele (`npm run gen:api`), então mudança de contrato quebra a compilação do front, não o usuário.

### Erros

Formato único: `{"erro": {"codigo": "...", "mensagem": "...", "detalhes": [...]}}` — `validacao` (422 com campos),
`regra_de_negocio` (422), `conflito` (409), `nao_autenticado` (401), `sem_permissao` (403), `nao_encontrado` (404),
`muitas_tentativas` (429). As mensagens já são para o usuário final, em português.

## Frontend (`frontend/src`)

| Pasta | Responsabilidade |
|---|---|
| `core/` | Utilitários sem estado: `html` (template **seguro por padrão**: tudo é escapado, o que elimina XSS por esquecimento), formatação (R$, datas), parser de números BR, DOM. |
| `api/` | Cliente HTTP único (token, erros, download) e funções tipadas por recurso. `schema.d.ts` é **gerado** do OpenAPI. |
| `state/` | `estado` (usuário, coleções, filtros), `nucleo` (registro de vistas, navegação, render, recarga), `realtime` (WebSocket). |
| `domain/` | Constantes/rótulos e regras de tela (totais ao digitar, texto do WhatsApp). O servidor recalcula e é a verdade. |
| `ui/` | Peças reutilizáveis: gaveta, campos de formulário, toast, login, casca lateral, eventos globais, conflito de edição, gravação padrão. |
| `features/` | Uma funcionalidade por arquivo (vista + formulário + ações): painel, clientes, negócios, orçamentos, projetos, tarefas, faturamento, despesas, produtos, equipe. Cada uma se **registra** (`registrarVista`, `registrarAcao`, `registrarAbertura`) — o núcleo não conhece nenhuma delas. `ponte.ts` permite uma abrir o formulário de outra sem import circular. |
| `styles/` | O CSS do sistema anterior, intacto, dividido por assunto (tokens → base → login → layout → componentes → quadros → gaveta → responsivo). |

Fluxo de uma ação: `data-act="novoCliente"` → `ui/eventos` despacha → a feature abre a gaveta → ao salvar, `gravar()`
chama a API, recarrega os recursos afetados, avisa e fecha. O servidor avisa as outras pessoas pelo WebSocket.

### Identidade visual

O CSS e a marcação (classes) foram preservados; tema claro/escuro (`prefers-color-scheme`), fontes Montserrat / IBM Plex
e a paleta marinho + turquesa continuam definidos em `styles/tokens.css`. Duas regras mortas do CSS antigo (largura do
quadro de tarefas e espessura da borda do cartão, sempre sobrescritas pela cascata) foram removidas para que o código
descreva o que realmente aparece, sem alterar o visual.

## Qualidade

- `pytest` (≈50 testes) contra PostgreSQL real, com o schema criado pelo próprio Alembic; cada teste roda numa transação
  desfeita no fim. Cobrem regras de negócio, permissões, concorrência, escape de HTML nos documentos e o importador.
- `backend/tests_sql/test_schema.sql` (≈110 verificações) valida constraints, triggers, numeração e views direto no banco.
- `vitest` para as regras de tela e utilitários; `eslint` + `tsc --noEmit` estritos (`noUncheckedIndexedAccess`).
- `e2e/` percorre os fluxos reais no navegador (login, arrastar cartões, aprovar orçamento, relatório, tempo real).
- CI: lint + testes + build em cada push.

## Limitações conhecidas

- A presença/tempo real assume **uma instância** da API (ver acima).
- O limitador de tentativas de login também é local ao processo; com várias instâncias, mova-o para armazenamento compartilhado.
- O token de sessão fica no `localStorage` (como o sistema anterior). Mitigações: CSP restritiva e HTML escapado por padrão.
  Para endurecer ainda mais, migre para cookie `HttpOnly` + proteção CSRF.
- Sem recuperação de senha por e-mail (decisão herdada: o administrador redefine).
- Listas carregam todos os registros (adequado para uma equipe pequena); se crescer, adicione paginação nos serviços.
- Migrações devem ser executadas como etapa única do release antes de iniciar as réplicas (`docker compose --profile migrate run --rm migrate`),
  não por cada processo da API.
- `/api/saude` verifica apenas o processo; `/api/prontidao` também valida a conexão com o PostgreSQL e pode ser usado como readiness probe.
