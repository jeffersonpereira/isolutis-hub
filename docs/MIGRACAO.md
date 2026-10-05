# Migrando os dados do sistema anterior

O sistema anterior guardava cada área em `hub_<área>(id, dados jsonb, …)` no Supabase. O importador
(`backend/app/scripts/importar_legado.py`) lê essas tabelas e grava no schema relacional, **limpando** o que o novo banco
(mais estrito) não aceita. O mapeamento campo a campo está em [`banco-de-dados.md`](banco-de-dados.md#9-mapeamento-do-legado).

## Passo a passo

1. **Banco novo**: `alembic upgrade head` em `backend/` (cria as tabelas, triggers e views).
2. **Simule**: não grava nada e mostra o relatório de avisos.
   ```bash
   cd backend
   python -m app.scripts.importar_legado --origem-url "postgresql://usuario:senha@host:5432/postgres" --simular
   # ou, a partir de arquivos exportados (hub_clientes.json etc.: lista de {id, dados, criado_em, atualizado_em, atualizado_por}):
   python -m app.scripts.importar_legado --json-dir ./export --simular
   ```
3. **Revise os avisos** (cliente sem CNPJ válido, negócio "perdido" sem motivo, projeto com entrega antes do início,
   responsável que não corresponde a nenhum usuário…) e corrija na origem se quiser.
4. **Importe** (mesmo comando, sem `--simular`). É idempotente: o mapa id antigo → id novo fica em `legado_ids`, e uma
   segunda execução só traz o que faltar. Datas e autores originais são preservados.
5. **Senhas**: as senhas do Supabase Auth não migram. Os usuários chegam **sem senha**; o administrador (criado com
   `criar_admin`) define a de cada pessoa na aba **Equipe**.
6. Depois de validar tudo, remova o mapa temporário com uma migração (`DROP TABLE legado_ids`).

## O que é ajustado automaticamente

| Situação no legado | Resultado |
|---|---|
| CNPJ com máscara | só dígitos |
| CNPJ que não tem 14 dígitos / repetido | vira `NULL`, o texto original vai para as observações do cliente (e o aviso é registrado) |
| Origem fora da lista | `Outro` (+ texto original nas observações) |
| Negócio `perdido` sem motivo | motivo `Sem resposta` |
| Registro cujo cliente não existe mais | não migra (aviso) |
| Orçamento/lançamento/projeto ligado a negócio de **outro** cliente | vínculo removido (aviso) |
| Dois projetos no mesmo negócio | só o primeiro mantém o vínculo (aviso) |
| Orçamento com status `vencido` gravado | `enviado` (vencido passou a ser derivado) |
| `recebido`/`pago` sem data | usa o vencimento / a data do lançamento |
| Tarefa concluída sem data de conclusão | usa a data da última alteração |
| Parcelas "3/12" só no texto da descrição | agrupadas numa série (`grupo_id`, `parcela`, `total_parcelas`) |
| Despesa com categoria nova | cria a categoria |
| Investidor/responsável em texto livre | casa com usuário por nome/primeiro nome; senão fica em branco (aviso) / cria investidor |

## Depois da migração

- Aponte o novo front/API para o mesmo domínio que a equipe já usa e desligue o antigo (a chave `sb_publishable_…`
  que estava no `index.html` antigo e a Edge Function `hub-admin` deixam de ser necessárias; revogue a chave secreta que
  a função usava).
- O código do sistema anterior (`index.html`, `supabase*.sql`, funções) continua disponível no histórico do Git.

> Desde a migração 0003 o importador grava `hub_clientes` em `parceiro_negocio` com o papel `cliente` (CPF/CNPJ validado; cidade → município quando possível). Veja `docs/banco-de-dados.md`.
