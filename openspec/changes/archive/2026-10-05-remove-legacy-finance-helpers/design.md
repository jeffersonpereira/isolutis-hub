## Context

The finance workflow is centered on the existing financial control, whose operation nature supplies the classification. The old `lancamento_receita`, `despesas`, `investimentos`, `categorias_despesa`, and `investidores` tables represent redundant or obsolete models. The expense/investment tables were already addressed; remaining targets should be removed with an idempotent migration after checking dependencies.

## Goals / Non-Goals

**Goals:**
- Keep the PostgreSQL schema consistent with title-based financial classification.
- Make cleanup safe to reapply and preserve unrelated company and user data.
- Remove obsolete backend references that depend on the removed tables.

**Non-Goals:**
- Change financial title APIs, nature values, or title classification behavior.
- Alter or remove the `titulo_financeiro` table or account plan.

## Decisions

- Use an idempotent SQL migration for the explicitly obsolete relations. Check foreign keys and views first; do not use cascading drops that could remove unapproved objects.
- Drop dependent transaction tables before helper tables. `categorias_despesa` data is intentionally discarded under the user's explicit instruction. Include `lancamento_receita` only after confirming it is separate from, and not the backing table of, the existing financial control.
- Remove or disable application routes that query these tables, while retaining title-based routes. Keeping compatibility tables would preserve a competing financial model.

## Risks / Trade-offs

- Existing consumers or database objects may depend on a target → Search source references and inspect database constraints and views before applying; resolve only dependencies within the approved scope.
- `categorias_despesa` has existing rows → The user explicitly authorized removing this table; document the deletion and avoid touching unrelated tables.
- Environments may have different table presence → Use idempotent drops and verify the final schema after applying.

## Migration Plan

1. Inspect table existence and dependencies, especially whether `lancamento_receita` backs any part of the existing financial control.
2. Update the SQL migration and eliminate remaining code paths that depend on obsolete tables.
3. Apply the migration to the configured database and verify that approved legacy relations are absent while the existing financial control and account plan remain.

Rollback would require restoring a database backup; the obsolete category rows are not recreated because the user requested their removal.

## Open Questions

None.
