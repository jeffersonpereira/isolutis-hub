# Design

## Context

- Entidades comerciais usam os mixins `ComAuditoria` (id, carimbos, `versao` com concorrência otimista via trigger
  `set_audit`) e `ComEmpresa` (`empresa_id` com default `app_empresa_id()` e RLS). Migrações são SQL puro em
  `backend/migrations/sql/NNNN_*.sql` (+ `_down.sql`), chamadas por um wrapper Alembic.
- Clientes são `parceiro_negocio` com papel `cliente`; tabelas que apontam para cliente usam o trigger
  `tg_exige_papel_cliente` (ex.: `tarefas`).
- Regras de etapa do negócio vivem em `services/negocios.py::definir_etapa`; o funil move cartões por
  `PATCH /negocios/{id}/etapa`.
- O painel monta alertas por bloco de permissão em `services/painel.py` (`alertas` com `quantidade` + `ids`).
- Rotas comerciais são registradas em `main.py` com `Depends(requer_comercial)`; a matriz de papéis está em
  `domain/papeis.py`.
- Alterações são propagadas às outras abas por `realtime.publicar_alteracao(recursos, empresa_id)`.

## Goals / Non-Goals

**Goals:**
- Tabela própria de atividades, consultável por cliente e por negócio com paginação por cursor.
- Próxima ação como dado do negócio, validada nas mesmas funções que já validam a etapa.
- Operação atômica "concluir ação".

**Non-Goals:**
- Lembrete por e-mail ou notificação push de ação vencida (o alerta no painel basta nesta etapa).
- Integração com e-mail, WhatsApp ou agenda; anexos em atividades.
- Atividades ligadas a orçamento ou projeto.
- Histórico de mudanças de etapa (é o item 3 da avaliação, outra mudança).

## Decisions

### 1. Tabela `atividades` separada, não reaproveitar `tarefas`
`tarefas` é o kanban interno da equipe (coluna, prioridade, checklist) e representa trabalho a fazer. Atividade é um
fato passado e imutável na prática. Misturar os dois poluiria o kanban com centenas de registros concluídos e exigiria
condicionais em todas as telas de tarefa.
Alternativa descartada: `tarefas` com flag `atividade`, mais barata no início, mas acopla dois ciclos de vida diferentes.

Colunas: `tipo` (CHECK nos quatro valores), `ocorrida_em timestamptz`, `descricao text NOT NULL`, `cliente_id` (FK para
`parceiro_negocio`, trigger `tg_exige_papel_cliente`), `negocio_id` (FK nullable, `ON DELETE SET NULL`),
`responsavel_id` (FK `usuarios`). Índices `(empresa_id, cliente_id, ocorrida_em DESC, id DESC)` e
`(empresa_id, negocio_id, ocorrida_em DESC, id DESC) WHERE negocio_id IS NOT NULL`.

A coerência cliente × negócio é garantida por trigger no banco (`tg_atividade_cliente_do_negocio`), além da validação no
serviço, como nas demais regras de integridade do projeto. Excluir um cliente com atividades segue a regra atual de
exclusão de clientes com registros relacionados (bloqueia).

### 2. Próxima ação como duas colunas em `negocios`
`proxima_acao varchar(200)` e `proxima_acao_em date`, com CHECK no banco: ambas preenchidas ou ambas nulas, e nulas
quando a etapa é `ganho`/`perdido`. A obrigatoriedade em etapa aberta **não** vai para o banco: negócios antigos ficam
nulos até serem regravados (ver spec). A regra entra em `definir_etapa`, que já é o ponto único chamado por criar,
atualizar e mover.
Alternativa descartada: guardar a próxima ação como uma atividade "agendada". Daria um só modelo, mas o funil, o painel
e a validação precisariam de subconsultas para achar "a ação pendente" de cada negócio. Uma coluna é mais simples e
indexável.

No `MoverEtapa`, os campos da ação são opcionais: se ausentes, mantém os gravados; se não houver gravados e a etapa de
destino é aberta, recusa com 422. O funil trata esse 422 abrindo o diálogo da próxima ação e reenviando o movimento.

### 3. `POST /negocios/{id}/concluir-acao` atômico
Recebe `versao`, `atividade {tipo, descricao}` e uma de duas saídas: `proxima {acao, data}` ou
`fechar {etapa: ganho|perdido, motivo_perda?}`. Executa numa transação: confere a versão, cria a atividade com
`ocorrida_em = now()`, aplica a nova ação ou a etapa via `definir_etapa` e confirma. Qualquer erro desfaz tudo.
Alternativa descartada: duas chamadas no frontend (criar atividade, depois PUT no negócio), que deixaria uma atividade
órfã se a segunda falhasse por conflito de versão.

### 4. API de atividades
- `GET /atividades?cliente_id=…|negocio_id=…&antes=<cursor>&limite=50`: exatamente um dos dois filtros. O cursor é
  `(ocorrida_em, id)` codificado, o que mantém a ordem estável mesmo com datas repetidas.
- `POST /atividades`, `PUT /atividades/{id}` (com `versao`), `DELETE /atividades/{id}`.
- Autorização de edição e exclusão no serviço: `atividade.criado_por == usuario.id` ou papel `admin`; senão 403.
- O schema de leitura traz `responsavel_nome` e `negocio_titulo` para a linha do tempo não precisar de outras chamadas.
- Tolerância de 5 minutos para `ocorrida_em` no futuro (relógios de cliente adiantados).

### 5. Painel
Dois contadores adicionados ao bloco `comercial` com uma única consulta agregada usando `count(*) FILTER (...)` sobre
negócios em `ETAPAS_ABERTAS`: `negocios_sem_acao` e `acoes_vencidas`. Seguem o formato `{quantidade, ids}` existente.
Os dois conjuntos são disjuntos (sem ação ≠ ação vencida).

### 6. Frontend
- Componente `ui/linha-do-tempo.ts` reutilizado no cliente e no negócio: lista agrupada por dia, ícone por tipo,
  "Carregar anteriores", formulário curto (tipo, data/hora com padrão "agora", descrição).
- Formulário do negócio ganha os campos de próxima ação (obrigatórios quando a etapa é aberta, ocultos quando fechada).
- Cartão do funil mostra a ação e a data relativa ("hoje", "há 3 dias", "em 2 dias") com as cores da spec, e um botão
  "Concluir" que abre o diálogo do item 3.
- Recurso realtime `atividades` publicado nas escritas; `negocios` também é publicado pelo concluir-acao.

## Risks / Trade-offs

- [Clientes externos da API que criam negócios quebram com o 422] → A API é usada só pelo próprio frontend hoje;
  registrar o BREAKING no changelog e no OpenAPI exportado.
- [A equipe percebe a obrigatoriedade como burocracia e preenche "ligar" genérico] → Diálogo curto com sugestões rápidas
  ("Ligar", "Enviar proposta", "Agendar reunião") e data padrão de +2 dias úteis; medir depois pelo alerta de vencidas.
- [Muitos negócios antigos aparecem de uma vez no alerta "sem próxima ação"] → Efeito desejado; o alerta leva ao funil,
  onde cada cartão sem ação fica destacado.
- [Crescimento da tabela de atividades] → Índices compostos com cursor; nenhuma tela lista atividades sem filtro.

## Migration Plan

1. Migração `0012_atividades_proxima_acao.sql`: cria `atividades` (RLS, policies, trigger de auditoria e de papel de
   cliente, trigger de coerência com negócio) e adiciona as colunas e o CHECK em `negocios`. Antes do CHECK, limpa a
   próxima ação de negócios fechados (no-op em bases novas).
2. `0012_atividades_proxima_acao_down.sql`: remove o CHECK, as colunas e a tabela.
3. Deploy normal: migração como etapa do release, depois a imagem nova. A API antiga ignora as colunas novas, então
   aplicar a migração antes do deploy é seguro.
