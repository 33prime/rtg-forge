# Supabase RLS Patterns

Row Level Security (RLS) is the primary authorization mechanism in Supabase. Every table exposed to PostgREST MUST have RLS enabled with explicit policies. There is no "default deny" without enabling RLS — without it, all rows are visible.

---

## Enabling RLS

Every table MUST have RLS enabled in the same migration that creates it:

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
```

**No exceptions.** A table without RLS is fully readable and writable by any authenticated user.

---

## auth.uid() and auth.jwt()

Supabase provides helper functions to access the authenticated user's identity:

```sql
-- Get the user's UUID (from the JWT sub claim)
auth.uid()

-- Get the full JWT payload (for custom claims like tenant_id, role)
auth.jwt()

-- Extract a specific claim
(auth.jwt() ->> 'tenant_id')::uuid
(auth.jwt() ->> 'role')::text
```

### Custom Claims

For multi-tenant apps, set custom claims in the JWT (via Supabase Auth hooks or custom token):

```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "admin",
  "app_metadata": {
    "permissions": ["invoices:read", "invoices:write"]
  }
}
```

---

## Policy Patterns

### Pattern 1: User Owns Row

For tables where each row belongs to a single user:

```sql
CREATE POLICY users_own_data ON user_profiles
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```

### Pattern 2: Tenant Isolation

For multi-tenant tables — the most common pattern:

```sql
CREATE POLICY tenant_isolation ON invoices
    FOR ALL
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
```

### Pattern 3: Role-Based Access

For tables where access depends on the user's role:

```sql
-- Anyone in the tenant can read
CREATE POLICY invoices_select ON invoices
    FOR SELECT
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

-- Only admins and managers can insert/update
CREATE POLICY invoices_modify ON invoices
    FOR INSERT
    WITH CHECK (
        tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
        AND (auth.jwt() ->> 'role')::text IN ('admin', 'manager')
    );

CREATE POLICY invoices_update ON invoices
    FOR UPDATE
    USING (
        tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
        AND (auth.jwt() ->> 'role')::text IN ('admin', 'manager')
    )
    WITH CHECK (
        tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
    );
```

### Pattern 4: Child Table Access Via Parent

For child tables that inherit access from their parent:

```sql
CREATE POLICY line_items_via_invoice ON line_items
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
        )
    );
```

### Pattern 5: Public Read, Authenticated Write

For tables like product catalogs:

```sql
CREATE POLICY products_public_read ON products
    FOR SELECT
    USING (published = true);

CREATE POLICY products_admin_write ON products
    FOR ALL
    USING ((auth.jwt() ->> 'role')::text = 'admin')
    WITH CHECK ((auth.jwt() ->> 'role')::text = 'admin');
```

---

## Policy Naming Convention

Use a consistent naming scheme:

```
<table>_<operation>_<who>
```

Examples:
- `invoices_select_tenant` — Tenant members can read invoices
- `invoices_insert_admin` — Only admins can create invoices
- `line_items_all_via_invoice` — All operations via parent invoice check
- `products_select_public` — Anyone can read published products

---

## USING vs WITH CHECK

| Clause | Applies To | Purpose |
|---|---|---|
| `USING` | SELECT, UPDATE (existing rows), DELETE | Filters which existing rows are visible |
| `WITH CHECK` | INSERT, UPDATE (new row values) | Validates the new/modified row |

**Always specify both** for INSERT and UPDATE policies to prevent:
- Users inserting rows into other tenants
- Users changing `tenant_id` on existing rows

---

## Service Role Bypass

The `service_role` key bypasses RLS entirely. Use it ONLY for:
- Server-side admin operations
- Migrations and seeding
- Background jobs that span tenants

```python
# Python — service role client for admin operations
admin_client = create_client(
    supabase_url=settings.supabase_url,
    supabase_key=settings.supabase_service_role_key,  # Bypasses RLS!
)
```

**Never expose the service_role key to the frontend.**

---

## SECURITY DEFINER Functions

Use `SECURITY DEFINER` with extreme caution. It runs the function as the function owner (usually the `postgres` superuser), bypassing RLS.

```sql
-- DANGEROUS — this function bypasses all RLS
CREATE OR REPLACE FUNCTION get_all_invoices()
RETURNS SETOF invoices
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT * FROM invoices;
$$;
```

### When to Use SECURITY DEFINER

- Cross-tenant aggregation for analytics
- Admin operations that must span tenants
- Functions called by triggers (which run as the table owner anyway)

### Safety Rules for SECURITY DEFINER

1. Always set `search_path` to prevent injection:
   ```sql
   SET search_path = public, pg_temp;
   ```
2. Validate all inputs
3. Return only the minimum necessary data
4. Add a comment explaining WHY it needs SECURITY DEFINER

---

## Testing RLS

Always test your policies by simulating different user contexts:

```sql
-- Simulate an authenticated user
SET request.jwt.claims = '{"sub": "user-1", "tenant_id": "tenant-1", "role": "member"}';
SET role = 'authenticated';

-- This should return only tenant-1 invoices
SELECT * FROM invoices;

-- This should fail (wrong tenant)
INSERT INTO invoices (tenant_id, customer_id, status)
VALUES ('tenant-2', 'customer-1', 'draft');

-- Reset
RESET role;
RESET request.jwt.claims;
```

### RLS Testing Checklist

- [ ] User can only see their own tenant's data
- [ ] User cannot insert rows for other tenants
- [ ] User cannot update tenant_id on existing rows
- [ ] Role-based restrictions work correctly
- [ ] Child table access is properly scoped through parent
- [ ] Service role can bypass when needed
- [ ] Anonymous users see only public data
