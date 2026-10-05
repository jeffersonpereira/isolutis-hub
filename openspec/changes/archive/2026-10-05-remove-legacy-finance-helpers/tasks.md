## 1. Remove obsolete schema and code references

- [x] 1.1 Update the idempotent SQL migration to include `lancamento_receita`, `categorias_despesa`, and `investidores` with the already-obsolete expense and investment tables, subject to dependency verification.
- [x] 1.2 Search backend and frontend code for remaining queries, routes, or UI that depend on these five tables; remove obsolete paths while preserving title-based finance.

## 2. Apply and verify cleanup

- [x] 2.1 Inspect live database dependencies and confirm `lancamento_receita` is not backing the existing financial control; target only authorized legacy relations.
- [x] 2.2 Apply the migration to the configured database.
- [x] 2.3 Verify that all five legacy tables are absent and `titulo_financeiro` and `plano_contas` remain.
