# Supabase Database Design

Patterns for designing clean, performant, and maintainable Postgres schemas in Supabase. Every table should be queryable through PostgREST and protectable with RLS.

---

## Table Naming Conventions

- Use `snake_case` for all identifiers (tables, columns, indexes, constraints)
- Table names are **plural**: `invoices`, `line_items`, `users`
- Junction tables: `user_roles`, `project_members` (entity_relationship)
- Prefix audit/system tables: `audit_logs`, `system_settings`

---

## Required Columns

Every table MUST have these columns:

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

### Multi-Tenant Tables

Every tenant-scoped table MUST include:

```sql
tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
```

And a composite index:

```sql
CREATE INDEX idx_<table>_tenant_id ON <table>(tenant_id);
```

---

## Column Types

| Use Case | Type | NOT This |
|---|---|---|
| Identifiers | `UUID` | `SERIAL`, `BIGINT` |
| Money/currency | `NUMERIC(12,2)` | `FLOAT`, `DOUBLE PRECISION` |
| Timestamps | `TIMESTAMPTZ` | `TIMESTAMP` (without tz) |
| Short strings | `TEXT` with `CHECK(length(col) <= N)` | `VARCHAR(N)` |
| Long text | `TEXT` | — |
| Enums | `TEXT` with `CHECK` constraint | Postgres `ENUM` type (hard to migrate) |
| Structured data | `JSONB` | `JSON`, `TEXT` |
| Booleans | `BOOLEAN NOT NULL DEFAULT false` | `INTEGER` |
| IP addresses | `INET` | `TEXT` |

### Why TEXT + CHECK Over VARCHAR

```sql
-- YES — easy to change the constraint later
name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 255)

-- AVOID — changing VARCHAR length requires ALTER COLUMN
name VARCHAR(255) NOT NULL
```

### Why TEXT + CHECK Over ENUM

```sql
-- YES — easy to add new values
status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'sent', 'paid', 'cancelled'))

-- AVOID — adding values to ENUM requires ALTER TYPE
CREATE TYPE invoice_status AS ENUM ('draft', 'sent', 'paid', 'cancelled');
```

---

## Foreign Keys

Every foreign key MUST specify `ON DELETE` behavior explicitly:

```sql
-- Parent owns children — delete cascades
customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE

-- Reference should not be deleted while referenced
category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT

-- Optional reference — set to null if parent deleted
assigned_to UUID REFERENCES users(id) ON DELETE SET NULL
```

### Foreign Key Rules

1. Always specify `ON DELETE` — never rely on the default (`NO ACTION`)
2. Use `CASCADE` when the child has no meaning without the parent
3. Use `RESTRICT` when deletion should be prevented
4. Use `SET NULL` for optional associations
5. Always index foreign key columns (Postgres does NOT auto-index them)

---

## Indexes

### Index Rules

1. **Always** index foreign key columns
2. **Always** index columns used in `WHERE` clauses
3. **Always** index columns used in `ORDER BY` with `LIMIT`
4. Use partial indexes for common filtered queries
5. Use GIN indexes for JSONB and full-text search

```sql
-- Foreign key index
CREATE INDEX idx_invoices_customer_id ON invoices(customer_id);

-- Composite index for common query pattern
CREATE INDEX idx_invoices_tenant_status ON invoices(tenant_id, status);

-- Partial index for active records
CREATE INDEX idx_invoices_unpaid ON invoices(tenant_id, created_at)
    WHERE status NOT IN ('paid', 'cancelled');

-- GIN index for JSONB queries
CREATE INDEX idx_invoices_metadata ON invoices USING GIN(metadata);
```

---

## JSONB Usage

Use JSONB for truly dynamic/schemaless data. Do NOT use it to avoid schema design.

### Good JSONB Use Cases

- User preferences/settings
- External system metadata (varies per integration)
- Form builder field definitions
- Audit log context

### Bad JSONB Use Cases

- Core business fields that are queried/filtered frequently
- Replacing proper relational modeling
- Storing arrays that should be junction tables

```sql
-- YES — truly dynamic metadata
metadata JSONB NOT NULL DEFAULT '{}'::jsonb

-- NO — this should be separate columns or a related table
data JSONB  -- contains { "name": "...", "email": "...", "status": "..." }
```

---

## Views

Use views to simplify complex queries and provide clean PostgREST interfaces:

```sql
CREATE OR REPLACE VIEW invoice_summaries AS
SELECT
    i.id,
    i.tenant_id,
    i.status,
    i.created_at,
    c.name AS customer_name,
    COUNT(li.id) AS line_item_count,
    COALESCE(SUM(li.quantity * li.unit_price), 0) AS total
FROM invoices i
JOIN customers c ON c.id = i.customer_id
LEFT JOIN line_items li ON li.invoice_id = i.id
GROUP BY i.id, c.name;
```

### View Rules

- Views are read-only through PostgREST by default
- Name views descriptively: `invoice_summaries`, `active_users`
- Add `security_invoker = true` for RLS-aware views (Postgres 15+)

---

## Migrations

Every schema change goes through a numbered migration file.

### Migration File Naming

```
supabase/migrations/
  20260211000001_create_tenants.sql
  20260211000002_create_users.sql
  20260211000003_create_invoices.sql
```

### Migration Rules

1. Migrations are **append-only** — never edit a deployed migration
2. Each migration handles ONE logical change
3. Include both the change and necessary indexes/constraints
4. Always add RLS policies in the same migration that creates the table
5. Use `IF NOT EXISTS` for idempotent index/constraint creation

---

## Updated-At Trigger

Create a reusable trigger function and apply to every table:

```sql
-- Create once
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to each table
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```
