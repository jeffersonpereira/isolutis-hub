## Context

**Isolamento já resolvido.** Cada requisição leva `Authorization` (quem) e `X-Empresa-ID` (qual empresa). `deps.empresa_atual` valida a membership ativa a cada chamada e define `app.empresa_id` na transação; o RLS do Postgres filtra todas as tabelas por `app_empresa_id()`. Nada disso muda.

**Papel já é por empresa**, em `usuario_empresa.papel` (constraint `ck_usuario_empresa_papel`: `admin` ou `membro`). `deps.administrador` consulta a membership. Já `Usuario.admin` é um flag global vestigial: `criar_admin` e `convites` gravam `False`, e `UsuarioLeitura.admin` é preenchido por `set_committed_value` a partir do papel na listagem de equipe.

**Autorização hoje:** só `/financeiro` (router-level), `/parceiros`, onboarding e gestão de usuários exigem `admin`. Os demais routers entram em `main.py` com `Depends(empresa_atual)` apenas, ou seja, qualquer membro acessa clientes, negócios, orçamentos, produtos, projetos, tarefas, despesas, faturamento, painel e relatórios (DRE e fluxo de caixa). O front esconde menus com `somenteAdmin` e lê `eu.admin` (`nucleo.ts`, `main.ts`, `ui/onboarding.ts`, `features/equipe.ts`).

**Front (após `design-system-e-shell`):** `selecionarEmpresa()` escolhe em silêncio (última do `localStorage` ou primeira) e alimenta um `<select id="empresaAtiva">` oculto em `index.html`; o menu do usuário da barra superior (`ui/barra-superior.ts`, `blocoEmpresa()`) espelha esse select e, com 2 ou mais empresas, mostra um seletor que dispara o `change` do oculto; a troca faz `location.reload()`. A navegação é por URL (`state/roteador.ts`, `caminhos.ts`): abrir a rota de uma tela sem permissão já cai no painel e corrige o endereço. A paleta de comandos (`ui/paleta.ts`) e o menu "+ Novo" (`acoesRapidas`) listam telas e ações a partir das vistas registradas. `carregarTudo()` dispara todos os carregadores (`clientes`, `negocios`, `orcamentos`, `produtos`, `projetos`, `tarefas`, `equipe`) com `Promise.all` sem tratamento; o WebSocket também aciona `recarregar(recurso)` para qualquer recurso avisado. `projetos.ts` usa `dados.negocios` (negócios ganhos) e `nomeCliente`/`seletorCliente` usam `dados.clientes` em várias telas.

**Criação de empresa:** `POST /empresas` chama a função SQL `criar_empresa` (SECURITY DEFINER, `EXECUTE` concedido a `hub_runtime`). O front nunca chama essa rota. O script `criar_admin` cria empresa e administrador pela credencial migradora.

## Goals / Non-Goals

**Goals:**
- Escolha explícita da empresa ativa após o login, troca posterior e isolamento por aba.
- Quatro papéis por empresa com matriz de permissões imposta no backend e consumida pelo front.
- Nenhuma rota de negócio sem checagem de permissão, garantido por teste.
- Restringir a criação de empresas ao operador.
- Eliminar `Usuario.admin`.

**Non-Goals:**
- Papéis ou permissões editáveis pela interface (RBAC configurável).
- Reforçar papéis no RLS do banco (o RLS continua só por empresa).
- Topbar, ícones e design system; cadastro completo de empresa; evolução da tela de usuários.
- Perfil super-admin da plataforma pela interface.

## Decisions

### D1. Permissões derivadas do papel, num único mapa no backend

```
 PERMISSOES_POR_PAPEL = {
   admin:      {base, comercial, financeiro, administracao},
   financeiro: {base, financeiro},
   comercial:  {base, comercial},
   membro:     {base},
 }
```

`deps.exige(permissao)` é uma fábrica de dependência: resolve a membership da empresa ativa (reaproveitando `empresa_atual`) e levanta `SemPermissao` se o papel não tiver a permissão. `administrador` passa a ser `exige("administracao")`, mantendo o nome para os usos existentes. O papel é lido da membership a cada requisição, como hoje, então rebaixar alguém vale na hora.

`GET /empresas` passa a devolver, por empresa, `papel` e `permissoes`. O front só decide pela lista de permissões e nunca infere nada a partir do nome do papel, de modo que um papel novo no futuro não exige tocar no front.

**Alternativa descartada:** tabela de permissões no banco, editável por empresa. É um módulo de RBAC inteiro e está fora de escopo; o mapa em código já isola o ponto de mudança.
**Alternativa descartada:** manter `papel == "admin"` espalhado e só somar condições. Cada papel novo exigiria revisar todos os routers.

### D2. Onde cada router se enquadra
As dependências ficam no `include_router` de `main.py` (ou no `APIRouter(dependencies=...)`), seguindo o padrão já usado por `/financeiro` e `/parceiros`:

| Permissão | Routers |
|---|---|
| `base` | `painel`, `tarefas`, `projetos`, `equipe` (lista), `GET /clientes/referencias`, `GET /empresas`, `/auth/*` (inclui o 2FA de Minha conta), `/parceiros/papeis`, `GET /cnpj/{cnpj}` |
| `comercial` | `clientes`, `negocios`, `orcamentos`, `produtos` |
| `financeiro` | `/financeiro/*`, `/parceiros` (hub), `faturamento`, `despesas`, `relatorios` (DRE e fluxo de caixa) |
| `administracao` | `/usuarios`, `/convite*`, `/empresas/ativa` (PATCH, inclui o cadastro completo da empresa), `/onboarding/*` |

O teste de D3 é o que garante que endpoints criados por outras changes (`GET /cnpj/{cnpj}`, atualização completa da empresa) não nasçam sem permissão. `GET /cnpj` fica em `base` por consultar apenas dados públicos e já ter autenticação e limite de taxa próprios.

`ws.py` (tempo real) continua exigindo membership; o conteúdo é só aviso de que um recurso mudou.

### D3. Teste que impede rota sem permissão
Um teste percorre `app.routes` sob `/api/v1` e falha para qualquer rota que não tenha uma dependência `exige(...)` nem esteja numa lista explícita de rotas públicas (`/auth/login`, `/auth/convite/*`, `/auth/2fa/verificar`, `/health` e equivalentes). Assim, um endpoint novo esquecido quebra a suíte em vez de nascer aberto. É a salvaguarda estrutural que o RLS não oferece para papéis.

### D4. Painel por blocos permitidos
`GET /painel` continua em `base`, mas cada bloco de dados (funil e negócios, orçamentos, faturamento e despesas) só é preenchido se o papel tiver a permissão correspondente; os demais saem `null`. O front não desenha bloco ausente. A primeira tarefa é auditar `schemas/painel.py` e `services/painel.py` para mapear bloco a permissão; isso evita que o painel vaze agregados financeiros ou comerciais a um `membro`.

### D5. Lista mínima de clientes em `base`
`GET /clientes/referencias` devolve apenas `id` e `nome`, em `base`. `nomeCliente` e `seletorCliente` passam a usar `dados.referenciasClientes` (carregado para todos). A lista completa `dados.clientes` só é carregada com `comercial`. Sem isso, projetos, tarefas e faturamento mostrariam "—" no lugar do cliente para quem não é comercial.

**Alternativa descartada:** dar `GET /clientes` completo a `financeiro` e `base`. Entregaria telefone, e-mail e observações a quem só precisa do nome.

### D6. Carga de dados do front por permissão
Cada carregador em `nucleo.ts` declara a permissão que exige. `carregarTudo()` e `recarregar()` executam apenas os permitidos para a empresa ativa e usam `Promise.allSettled`, para que uma falha isolada não derrube a inicialização. Avisos do WebSocket para recursos não permitidos são ignorados. `Vista.somenteAdmin` é substituído por `Vista.permissao?: Permissao`, filtrando o menu com `permissoes.includes(...)`.

A permissão também governa as três superfícies de descoberta de telas, hoje independentes: o menu (`renderMenu`), a paleta (`itensAtuais`) e o menu "+ Novo" (`acoesRapidas`) passam a filtrar pela mesma função `vistaPermitida(v)`, e `resolverRotaInicial` usa a mesma função para decidir se a URL pedida cai no painel. Uma única fonte evita a divergência "está no menu mas não abre".

`projetos.ts`, que lê `dados.negocios` para o vínculo com negócio ganho, degrada sem `comercial`: o seletor "Negócio vendido" fica vazio e o aviso de ganhos sem projeto não aparece.

### D7. Escolha de empresa: por aba, sempre visível após o login
Nova tela `ui/escolha-empresa.ts`, montada em `main.ts` entre a autenticação e `iniciarApp`.

```
 token válido ─▶ GET /empresas ─▶ lista vazia ──────────▶ "Sem acesso a nenhuma empresa" + Sair
                                  │
                                  ├─ sessionStorage tem empresa e ela está na lista ─▶ segue (F5 não pergunta)
                                  └─ senão ─▶ tela de escolha (cartões: nome + papel)
                                              pré-seleciona "última usada" (localStorage)
                                              ao escolher: grava em sessionStorage e localStorage ─▶ app
```

- **"Sempre":** a tela aparece após cada login e em cada aba nova (que nasce sem `sessionStorage`). Um recarregamento (F5) na mesma aba mantém a escolha, desde que ela ainda conste na lista devolvida por `/empresas`.
- **Troca:** o cabeçalho do menu do usuário da barra superior (`blocoEmpresa()`) mostra "Empresa · Papel" e a ação "Trocar de empresa", que limpa a escolha da aba e recarrega, reabrindo a tela. O `<select id="empresaAtiva">` oculto de `index.html` e o ouvinte `#empresaDoMenu` são removidos; `blocoEmpresa()` passa a ler o estado (empresa e papel) em vez do DOM.
- **Rota de destino preservada:** a tela de escolha é uma etapa reservada (como login e segundo fator em `navegacao-por-url`); a URL pedida originalmente é resolvida **depois** da escolha, já com as permissões da empresa escolhida. Um link para uma tela que o papel não permite cai no painel.
- **Logout:** limpa `sessionStorage` e `localStorage` (hoje a empresa antiga permanece entre usuários no mesmo navegador).
- **`http.ts`:** `sessaoToken.empresa()` passa a ler `sessionStorage` e `definirEmpresa` grava nos dois armazenamentos, com `try/catch` como o código atual.
- **Perda de acesso durante a sessão:** um 403 vindo de `empresa_atual` limpa a escolha da aba e recarrega, reabrindo a tela.
- O recarregamento na troca é mantido de propósito: garante que `dados.*` não carregue registros de outra empresa.

**Alternativa descartada:** manter `localStorage` como fonte da empresa ativa. Duas abas passam a compartilhar um estado que cada uma já copiou para a memória, e a troca numa aba não reflete na outra.
**Alternativa descartada:** pular a tela quando só há uma empresa. A decisão do projeto é mostrar sempre; fica fácil mudar depois, pois é uma única condição.

### D8. Migração `0010`
Segue o padrão SQL + Alembic + `down` (`0010_papeis_multi_empresa.sql`, `..._down.sql`, `versions/0009_...py`). Ordem das operações:

1. `UPDATE usuario_empresa SET papel = 'comercial' WHERE papel = 'membro'` e o mesmo em `convites` pendentes (emitidos sob a semântica antiga, em que membro tinha acesso comercial).
2. Trocar a constraint para `papel IN ('admin','financeiro','comercial','membro')`.
3. `ALTER TABLE usuarios DROP COLUMN admin` (após conferir que nenhuma view, trigger ou política depende dela).
4. `REVOKE EXECUTE ON FUNCTION criar_empresa(text) FROM hub_runtime`.

O `down` recria a coluna `admin` (default falso), converte `comercial` e `financeiro` em `membro` (perda de informação, documentada no arquivo) e devolve o `GRANT`. As políticas RLS que usam `app_empresa_admin` não mudam, pois `admin` continua sendo o literal `'admin'`.

### D9. API de usuários e convites com `papel`
`UsuarioLeitura` ganha `papel: str | None` (nulo em `/auth/eu`, que não tem empresa) e perde `admin`; `UsuarioCriar` e `UsuarioAtualizar` trocam `admin: bool` por `papel`. Existe um único conjunto de valores válidos (`app/domain/papeis.py`), usado pelos schemas, pelo convite e pelo serviço. As regras existentes se mantêm, reescritas sobre `papel`: não é possível rebaixar nem desativar a si mesmo, e deve sobrar pelo menos um `admin` ativo (`_garantir_algum_admin`). No front, o checkbox "Administrador" vira um select de papel em `equipe.ts` e no convite.

### D10. Criação de empresas fora da aplicação
Remove `POST /empresas`, o schema `EmpresaNova` e o `GRANT` da função SQL. A função permanece no banco (útil à credencial migradora), mas a aplicação não a alcança. `criar_admin` continua sendo o caminho do operador e passa a gravar `papel="admin"` sem tocar em `Usuario.admin`.

## Risks / Trade-offs

- **[Usuários atuais perdem acesso a Faturamento, Despesas e Relatórios]** É a intenção declarada, mas é uma restrição visível. → A migração converte `membro` em `comercial` para preservar o acesso comercial; Faturamento, Despesas e Relatórios passam a exigir `financeiro`. Comunicar antes do deploy e promover manualmente quem precisar.
- **[Front quebra com 403 na carga inicial]** → D6 (carregadores por permissão e `allSettled`) e testes de e2e por papel.
- **[Papel imposto só na aplicação, não no RLS]** Uma falha de rota expõe dados de um papel inferior da própria empresa (não de outra empresa). → D3 impede rotas sem permissão por teste; o isolamento entre empresas continua garantido pelo RLS.
- **[Painel vaza agregados]** → D4, com auditoria dos blocos como primeira tarefa.
- **[Conflito com a lista de acesso básico informada]** Relatórios foi listado como básico, mas são DRE e fluxo de caixa (financeiros). → Tratado como `financeiro`; ver Open Questions.
- **[Remover `Usuario.admin` é irreversível para dados]** O campo é sempre falso hoje. → Conferir dependências no banco antes do `DROP`; `down` recria a coluna.
- **[Tela de escolha a cada aba nova]** Atrito deliberado. → "Última usada" vem pré-selecionada, então o custo é um clique; F5 não pergunta de novo.
- **[Ordem do bootstrap em `main.ts`]** Já existem convite pendente (`correcoes-imediatas-convite-2fa-menu`), login com 2FA e resolução de rota inicial. → A escolha de empresa entra depois da autenticação e do convite pendente e antes de `resolverRotaInicial`; teste e2e cobrindo convite com duas empresas.
- **[Endpoints de outras changes sem permissão]** `GET /cnpj/{cnpj}`, a atualização completa da empresa e rotas novas surgem antes desta change. → O teste D3 falha para qualquer rota sem `exige(...)`; aplicar esta change por último ou adicionar `exige` já nas outras.
- **[Testes existentes assumem `membro` com acesso comercial e `admin` no schema]** → Atualizar os testes e criar fixtures por papel.

## Migration Plan

1. Fazer backup e aplicar `0010` em homologação com dados reais; conferir as contagens de papéis antes e depois.
2. Publicar backend e front juntos (o contrato de `admin`/`papel` quebra entre versões).
3. Orientar os administradores a atribuir `financeiro` a quem opera Faturamento, Despesas e Relatórios.
4. **Rollback:** reverter o deploy e executar o `down` de `0010`; papéis `financeiro` e `comercial` voltam como `membro`.

## Open Questions

Nenhuma. As duas decisões pendentes foram confirmadas pelo usuário em 2026-10-07: relatórios (DRE e fluxo de caixa) em `financeiro`; lista mínima de clientes (`id` e `nome`) em `base`.
