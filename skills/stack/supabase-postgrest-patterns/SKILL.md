# Supabase PostgREST Patterns

Patterns for querying Supabase effectively through the PostgREST API. Use resource embedding to avoid N+1 queries, type all responses, handle errors explicitly, and paginate everything.

---

## Select With Specific Columns

Never use `select('*')` in production. Select only the columns you need.

```typescript
// YES — specific columns
const { data, error } = await supabase
  .from("invoices")
  .select("id, status, created_at, customer:customers(id, name)")
  .eq("tenant_id", tenantId);

// NO — fetches everything, including large JSONB columns
const { data, error } = await supabase
  .from("invoices")
  .select("*");
```

---

## Resource Embedding (Joins)

Use PostgREST resource embedding to fetch related data in a single query. This avoids N+1 problems.

```typescript
// ONE query fetches invoices with their customer and line items
const { data, error } = await supabase
  .from("invoices")
  .select(`
    id,
    status,
    created_at,
    customer:customers (
      id,
      name,
      email
    ),
    line_items (
      id,
      description,
      quantity,
      unit_price
    )
  `)
  .eq("tenant_id", tenantId)
  .order("created_at", { ascending: false });
```

### Embedding Rules

1. Use foreign key relationships for automatic embedding
2. Rename embedded resources with `alias:table_name(columns)` syntax
3. Nest embeddings for multi-level relationships
4. Use `!inner` for INNER JOIN behavior: `customer:customers!inner(name)`

---

## Filtering

```typescript
// Equality
.eq("status", "paid")

// Not equal
.neq("status", "cancelled")

// Greater than / less than
.gt("total", 1000)
.lt("created_at", "2026-01-01")

// In a set
.in("status", ["draft", "sent"])

// Pattern matching
.ilike("customer_name", "%acme%")

// JSONB containment
.contains("metadata", { source: "import" })

// NULL checks
.is("deleted_at", null)
.not("assigned_to", "is", null)

// Combining filters (AND)
.eq("tenant_id", tenantId)
.eq("status", "paid")
.gte("created_at", startDate)

// OR conditions
.or("status.eq.draft,status.eq.sent")
```

---

## Pagination

Always paginate list queries. Never return unbounded result sets.

```typescript
const PAGE_SIZE = 50;

interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

async function getInvoices(
  tenantId: string,
  page: number = 1,
  pageSize: number = PAGE_SIZE,
): Promise<PaginatedResult<Invoice>> {
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  const { data, error, count } = await supabase
    .from("invoices")
    .select("id, status, created_at, customer:customers(name)", { count: "exact" })
    .eq("tenant_id", tenantId)
    .order("created_at", { ascending: false })
    .range(from, to);

  if (error) throw new SupabaseQueryError("Failed to fetch invoices", error);

  return {
    items: data as Invoice[],
    total: count ?? 0,
    page,
    pageSize,
    hasMore: (count ?? 0) > page * pageSize,
  };
}
```

### Pagination Rules

1. Always use `range(from, to)` for offset pagination
2. Pass `{ count: "exact" }` to `select()` to get total count
3. Default page size of 50, max of 100
4. Return pagination metadata alongside results
5. Consider cursor-based pagination for large datasets

---

## Error Handling

ALWAYS check the `error` property on Supabase responses. Never assume success.

```typescript
// Custom error class for Supabase query errors
class SupabaseQueryError extends Error {
  constructor(
    message: string,
    public readonly pgError: { message: string; code: string; details: string | null },
  ) {
    super(`${message}: ${pgError.message} (code: ${pgError.code})`);
    this.name = "SupabaseQueryError";
  }
}

// Helper function that throws on error
async function queryOrThrow<T>(
  query: PromiseLike<{ data: T | null; error: any }>,
): Promise<T> {
  const { data, error } = await query;
  if (error) throw new SupabaseQueryError("Query failed", error);
  if (data === null) throw new Error("Query returned null data without error");
  return data;
}

// Usage
const invoices = await queryOrThrow(
  supabase
    .from("invoices")
    .select("id, status")
    .eq("tenant_id", tenantId),
);
```

---

## RPC (Remote Procedure Calls)

Use Postgres functions (RPC) for complex operations that don't fit the REST model.

```sql
-- Define the function in a migration
CREATE OR REPLACE FUNCTION calculate_invoice_total(p_invoice_id UUID)
RETURNS TABLE(subtotal NUMERIC, tax NUMERIC, total NUMERIC)
LANGUAGE sql
STABLE
SECURITY INVOKER  -- Respects RLS
AS $$
  SELECT
    SUM(quantity * unit_price) AS subtotal,
    SUM(quantity * unit_price) * 0.08 AS tax,
    SUM(quantity * unit_price) * 1.08 AS total
  FROM line_items
  WHERE invoice_id = p_invoice_id;
$$;
```

```typescript
// Call from TypeScript
const { data, error } = await supabase
  .rpc("calculate_invoice_total", { p_invoice_id: invoiceId });

if (error) throw new SupabaseQueryError("Failed to calculate total", error);
// data is { subtotal: number, tax: number, total: number }
```

### RPC Rules

1. Use RPC for aggregations, multi-table operations, or complex logic
2. Use `SECURITY INVOKER` to respect RLS
3. Name functions clearly: `calculate_invoice_total`, `get_dashboard_stats`
4. Return typed results (TABLE or specific type)
5. Prefer `STABLE` or `IMMUTABLE` volatility when possible

---

## TypeScript Typing

Generate types from your database schema and use them for all queries.

```typescript
// Generated types (from supabase gen types typescript)
import type { Database } from "./database.types";

type Invoice = Database["public"]["Tables"]["invoices"]["Row"];
type InvoiceInsert = Database["public"]["Tables"]["invoices"]["Insert"];
type InvoiceUpdate = Database["public"]["Tables"]["invoices"]["Update"];

// Typed client
const supabase = createClient<Database>(url, key);

// Queries are now typed
const { data } = await supabase
  .from("invoices")        // TypeScript knows this table exists
  .select("id, status")    // TypeScript knows these columns exist
  .eq("status", "paid");   // TypeScript validates the column name and value type
```

### Typing Rules

1. Generate types with `supabase gen types typescript` after every migration
2. Use generated types for all query results
3. Use `Insert` and `Update` types for mutations
4. Keep generated types in version control
5. Re-generate types in CI to catch schema drift

---

## Realtime Subscriptions

Use Supabase Realtime for live data updates:

```typescript
const channel = supabase
  .channel("invoice-changes")
  .on<Invoice>(
    "postgres_changes",
    {
      event: "*",
      schema: "public",
      table: "invoices",
      filter: `tenant_id=eq.${tenantId}`,
    },
    (payload) => {
      switch (payload.eventType) {
        case "INSERT":
          handleNewInvoice(payload.new);
          break;
        case "UPDATE":
          handleUpdatedInvoice(payload.new);
          break;
        case "DELETE":
          handleDeletedInvoice(payload.old);
          break;
      }
    },
  )
  .subscribe();

// Cleanup
channel.unsubscribe();
```

### Realtime Rules

1. Always filter subscriptions to the minimum scope (use `filter`)
2. Handle all event types (INSERT, UPDATE, DELETE)
3. Clean up subscriptions on component unmount
4. Don't use Realtime as a replacement for initial data fetch
