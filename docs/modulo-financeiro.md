# Módulo financeiro

Implementa o spec "módulo financeiro" (plano de contas, contas bancárias, parceiros de negócio, contas a pagar e a receber,
fluxo de caixa mensal) seguindo o `plan.md` e as tasks 01 a 07. Código em `backend/app/financeiro/` e
`frontend/src/features/financeiro/`; o resto do sistema não foi alterado (só ligações aditivas, listadas no fim).

## Acesso

Todas as rotas `/api/v1/financeiro/*` e as telas exigem **administrador** (o spec fala em "usuário com acesso ao painel
administrativo"; no sistema, administrador é quem gerencia a Equipe). Para abrir o módulo a todos os membros, troque a
dependência `administrador` por `usuario_atual` em `app/financeiro/rotas.py` e retire `somenteAdmin` das cinco vistas.

## Telas (menu Financeiro)

| Submenu | O que faz | Spec |
|---|---|---|
| Plano de Contas | TreeView (expandir/recolher); Nova conta (filha da selecionada, ou de 1º nível sem seleção), Editar e Excluir atuam na conta selecionada. O código vem sugerido; natureza e nível são herdados do pai. | US01, RN01 |
| Conta Bancária | Lista, modal de cadastro, editar/excluir na linha. Instituição financeira + nome + saldo inicial. | US02, RN02 |
| Parceiro de Negócio | Hub de cadastro: papéis (cliente, fornecedor, funcionário), filtro por papel, busca por nome/CPF/CNPJ, PF/PJ, documento validado, UF → município. | US04 |
| Títulos Financeiros | Lista com filtros (tipo, situação), modal de lançamento (valor, desconto, multa, juros, quitação). Ao escolher a conta do plano só aparecem **analíticas** do tipo certo. | US03, RN03, RN04 |
| Fluxo de Caixa | Mês a mês: entradas e saídas realizadas (quitados) e previstas (abertos), saldo do mês e acumulado. Não estava nas tasks; é a US05. | US05 |

Os "modais" usam a gaveta lateral do sistema (o mesmo componente de todos os formulários) para manter a identidade visual.

## Regras e onde são garantidas

| Regra | Backend | Banco |
|---|---|---|
| RN01 hierarquia de até 3 níveis, códigos `1`, `1.01`, `1.01.001`, únicos por empresa | `regras.codigo_valido`, serviços | `ck_plano_contas_*`, `uq_plano_contas_empresa_codigo`, trigger `tg_plano_contas_regras` |
| RN01 filhas herdam características do pai (natureza, nível) | derivadas em `_validar_conta` | trigger (sobrescreve qualquer valor enviado) |
| RN01 conta sintética nunca recebe lançamento; analítica não tem filhas; nível 3 sempre analítico | serviços (mensagens claras) | trigger + `ck_plano_contas_nivel3_analitico` |
| RN01 um plano por empresa | tabela única por `empresa_id` (FKs compostas impedem misturar empresas) | `fk_*_empresa`, FKs `(id, empresa_id)` |
| RN02 sem contas bancárias iguais na empresa | mensagem amigável | índice único `(empresa_id, instituição, lower(nome))` |
| RN03 título só em conta analítica | `_campos_validados` | trigger `tg_titulo_financeiro_regras` |
| RN04 a pagar → despesa; a receber → receita | filtro na tela + validação no serviço | mesmo trigger |
| Quitação coerente (Q ⇔ data e valor pagos) | serviço normaliza | `ck_titulo_financeiro_quitacao` |
| CPF/CNPJ | dígitos verificadores conferidos | formato (11/14 dígitos) e unicidade por empresa |

Exclusões protegidas: conta do plano com filhas/títulos, conta bancária e parceiro com títulos (mensagem em português; FKs `RESTRICT`).

## Dados de referência (tasks 02 e 03)

```bash
cd backend
python -m app.financeiro.popular                    # fontes oficiais: IBGE (municípios) e BrasilAPI (bancos)
python -m app.financeiro.popular --fonte snapshot   # arquivos versionados em app/financeiro/dados (offline)
```

É idempotente. **Situação da carga entregue:** o ambiente em que isto foi desenvolvido bloqueia `servicodados.ibge.gov.br` e
`brasilapi.com.br`, então rodei com `--fonte snapshot`:

- **Instituições**: 513 (código COMPE/FEBRABAN + nome), do pacote npm `bancos-brasileiros@6.3.58`, espelho da lista do Banco Central.
- **Municípios**: 5.560 de 5.570. O snapshot vem do pacote `estados-cidades@4.1.0`, que **está incompleto** (faltam cerca de dez
  municípios; no DF ele listava regiões administrativas, que troquei por "Brasília", o único município do DF). **Para completar a
  task 02, rode `--fonte oficial` num ambiente com acesso ao IBGE** — ele insere só os que faltam.

A migração cria as tabelas **vazias**; a carga é um passo de implantação (rode também em produção).

## Desvios do plan.md (e por quê)

1. `plano_contas.plano_pai_id` aceita `NULL` (o plano marcava NOT NULL, o que impediria criar a conta de 1º nível).
2. `plano_contas.codigo` foi **acrescentado**: a RN01 exige códigos hierárquicos únicos e o plano não tinha o campo.
3. `titulo_financeiro.plano_conta_id` referencia `plano_contas` (o plano escrevia `plano_conta`, tabela inexistente).
4. `titulo_financeiro.tipo_conta` é **P/R** (pagar/receber); a descrição do plano ("sintética ou analítica") era cópia da outra tabela.
5. `DATETIME` (inexistente no PostgreSQL) virou `date` para emissão, vencimento e pagamento; `TIMESTAMP` virou `timestamptz` (UTC).
6. A migração `0005_multi_tenant` renomeia `companies` para `empresa`, preserva a UUID da iSolutis e atribui cada dado financeiro a `empresa_id`. O contexto vem do cabeçalho `X-Empresa-ID`, validado por membership ativo; não se escolhe mais a empresa mais antiga.
7. Coluna `UF` do município ficou `uf` (o PostgreSQL normaliza identificadores sem aspas).
8. `updated_at` é mantido por trigger; as tabelas novas não usam as colunas de auditoria/versão das demais (seguem o plano à risca).

## Escopo: o que NÃO foi tocado

Nenhuma tabela, rota ou tela existente foi alterada ou removida; Faturamento e Despesas continuam como estavam e **não** foram
integrados ao módulo novo (o spec não pede). Ligações aditivas fora da pasta do módulo: registro do router em `app/main.py`; mapeamento
das novas tabelas em `app/db.py` (para avisar outras sessões em tempo real); agrupamento de submenu em `state/nucleo.ts` (menus sem
grupo renderizam como antes); `styles/financeiro.css`; chaves de filtro em `state/estado.ts`; contrato OpenAPI/tipos regenerados.

## Fora do escopo desta entrega

A **importação de OFX** (`ofx.md`) é outro spec e não faz parte do "módulo financeiro" pedido; não foi implementada. Ela depende
deste módulo (títulos, contas bancárias, plano de contas) e pode ser feita a seguir.

## Testes

- `backend/tests/test_financeiro_regras.py` e `test_financeiro.py` (≈30): regras puras, permissões, hierarquia, RN01–RN04, quitação,
  fluxo de caixa com realizado/previsto/saldo anterior, e o banco recusando violações direto por SQL (inclusive isolamento entre empresas).
- `e2e/financeiro.mjs`: percorre no navegador menu, árvore, contas, parceiro (CNPJ inválido → válido), título (RN04), quitação, fluxo e bloqueio de exclusão.

## Parceiro de negócio como hub (migração 0003)

`parceiro_negocio` é o cadastro único de pessoas e empresas; o que cada uma é para a iSolutis vem de **papéis**
(`papel_parceiro`: cliente, fornecedor, funcionário — extensível por INSERT — e `parceiro_papel`, N:N). A tabela `clientes`
foi **removida**: seus registros foram copiados com o **mesmo id** para `parceiro_negocio` (papel `cliente`) e as FKs
`cliente_id` de negócios, orçamentos, lançamentos de receita, projetos e tarefas passaram a apontar para o parceiro.
Triggers garantem que `cliente_id` só referencie parceiro com papel `cliente` e que o papel não seja retirado enquanto houver vínculos.

- Colunas de cliente incorporadas: segmento, contato, cargo, telefone, email, origem, obs, auditoria e `versao`. `cpf_cnpj` e `municipio_id` passaram a aceitar NULL (cliente legado muitas vezes não tem).
- `cidade` (texto livre) virou `municipio_id` quando o nome é único (com UF, se informada); caso contrário vai para `obs` como `[cidade informada: X]`.
- CPF/CNPJ passa a ser validado (dígitos verificadores) em todo cadastro.
- API: `/api/v1/parceiros` (administradores; filtro `papel`, `busca`) e `/parceiros/papeis`; `/api/v1/clientes` continua como fachada (parceiros com papel cliente) para a equipe comercial.
- **Irreversível:** o `downgrade` da 0003 falha de propósito. Faça backup antes. Se o mesmo CPF/CNPJ existir em `clientes` e em `parceiro_negocio`, a migração aborta sem alterar nada — unifique antes.
