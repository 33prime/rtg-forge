-- BAD RLS Example: Overly permissive, insecure policies.
--
-- Problems demonstrated:
-- - RLS not enabled on some tables
-- - USING (true) — allows ALL rows
-- - No tenant isolation
-- - Missing WITH CHECK on write policies
-- - SECURITY DEFINER used incorrectly
-- - No role-based access control
-- - Inconsistent policy naming

-- Forgot to enable RLS on line_items table!
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE line_items ENABLE ROW LEVEL SECURITY;  -- MISSING!

-- PROBLEM: Allows ANY authenticated user to see ALL invoices (no tenant check)
CREATE POLICY allow_read ON invoices
    FOR SELECT
    USING (true);  -- This is almost never correct!

-- PROBLEM: No WITH CHECK — user can insert rows for ANY tenant
CREATE POLICY allow_insert ON invoices
    FOR INSERT
    WITH CHECK (true);  -- Anyone can insert anything!

-- PROBLEM: No tenant isolation, no role check
CREATE POLICY allow_update ON invoices
    FOR UPDATE
    USING (true);
    -- Missing WITH CHECK — user could change tenant_id

-- PROBLEM: Anyone can delete anything
CREATE POLICY allow_delete ON invoices
    FOR DELETE
    USING (true);

-- PROBLEM: SECURITY DEFINER function that bypasses RLS and returns all data
-- without any access control. No search_path set.
CREATE OR REPLACE FUNCTION get_all_tenant_invoices(p_tenant_id UUID)
RETURNS SETOF invoices
LANGUAGE sql
SECURITY DEFINER  -- Bypasses RLS!
AS $$
    -- No validation that the caller actually belongs to this tenant
    -- Anyone can call this with any tenant_id
    SELECT * FROM invoices WHERE tenant_id = p_tenant_id;
$$;
-- Missing: SET search_path = public, pg_temp;
-- Missing: validation that caller belongs to the tenant
-- Missing: comment explaining why SECURITY DEFINER is needed (it isn't)

-- PROBLEM: Using auth.uid() directly without tenant check
-- This only works for single-user apps, not multi-tenant
CREATE POLICY customers_by_user ON customers
    FOR SELECT
    USING (created_by = auth.uid());
    -- In a multi-tenant app, a user should see ALL customers in their tenant,
    -- not just ones they personally created.

-- line_items has NO RLS at all because we forgot to enable it above.
-- Any authenticated user can read/write ALL line items!
