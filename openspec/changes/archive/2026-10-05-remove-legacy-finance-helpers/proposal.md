## Why

Expense and investment information is now represented by financial titles classified by operation nature. The remaining legacy helper tables no longer serve the intended workflow and retaining them creates a competing data model.

## What Changes

- Remove obsolete `lancamento_receita`, `categorias_despesa`, and `investidores` tables from the database migration path.
- Keep the migration idempotent and aligned with the already-obsolete `despesas` and `investimentos` tables.
- Remove obsolete table-backed backend paths if any remain, while preserving title-based financial workflows.

## Capabilities

### New Capabilities

- `financial-data-model`: defines the database contract for retaining title-based finance without legacy expense/investor helper tables.

### Modified Capabilities

None.

## Impact

The PostgreSQL schema and migration scripts under `backend/migrations`; any remaining backend references to the legacy financial tables. Existing rows in `categorias_despesa` are intentionally removed per the user's explicit instruction. No API behavior for the existing financial control should change.
