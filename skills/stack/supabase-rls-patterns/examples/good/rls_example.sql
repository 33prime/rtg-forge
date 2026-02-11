-- Good RLS Example: Multi-tenant invoice system with role-based access.
--
-- Demonstrates:
-- - Proper tenant isolation using auth.jwt() claims
-- - Role-based write access (admin/manager vs member)
-- - Child table access via parent relationship
-- - Consistent policy naming
-- - Both USING and WITH CHECK on write policies

-- ---------------------------------------------------------------------------
-- Enable RLS on all tables
-- ---------------------------------------------------------------------------

ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- Helper: extract tenant_id from JWT
-- ---------------------------------------------------------------------------

-- Using a function avoids repeating the cast everywhere
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
    SELECT (auth.jwt() ->> 'tenant_id')::uuid;
$$;

CREATE OR REPLACE FUNCTION current_user_role()
RETURNS TEXT
LANGUAGE sql
STABLE
AS $$
    SELECT (auth.jwt() ->> 'role')::text;
$$;

-- ---------------------------------------------------------------------------
-- Invoices policies
-- ---------------------------------------------------------------------------

-- All tenant members can read invoices
CREATE POLICY invoices_select_tenant ON invoices
    FOR SELECT
    USING (tenant_id = current_tenant_id());

-- Only admins and managers can create invoices
CREATE POLICY invoices_insert_admin ON invoices
    FOR INSERT
    WITH CHECK (
        tenant_id = current_tenant_id()
        AND current_user_role() IN ('admin', 'manager')
    );

-- Only admins and managers can update invoices
CREATE POLICY invoices_update_admin ON invoices
    FOR UPDATE
    USING (
        tenant_id = current_tenant_id()
        AND current_user_role() IN ('admin', 'manager')
    )
    WITH CHECK (
        -- Prevent changing tenant_id on update
        tenant_id = current_tenant_id()
    );

-- Only admins can delete invoices
CREATE POLICY invoices_delete_admin ON invoices
    FOR DELETE
    USING (
        tenant_id = current_tenant_id()
        AND current_user_role() = 'admin'
    );

-- ---------------------------------------------------------------------------
-- Line items policies (access via parent invoice)
-- ---------------------------------------------------------------------------

CREATE POLICY line_items_select_via_invoice ON line_items
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = current_tenant_id()
        )
    );

CREATE POLICY line_items_insert_via_invoice ON line_items
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = current_tenant_id()
        )
        AND current_user_role() IN ('admin', 'manager')
    );

CREATE POLICY line_items_update_via_invoice ON line_items
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = current_tenant_id()
        )
        AND current_user_role() IN ('admin', 'manager')
    );

CREATE POLICY line_items_delete_via_invoice ON line_items
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM invoices
            WHERE invoices.id = line_items.invoice_id
            AND invoices.tenant_id = current_tenant_id()
        )
        AND current_user_role() = 'admin'
    );

-- ---------------------------------------------------------------------------
-- Customers policies
-- ---------------------------------------------------------------------------

CREATE POLICY customers_select_tenant ON customers
    FOR SELECT
    USING (tenant_id = current_tenant_id());

CREATE POLICY customers_insert_tenant ON customers
    FOR INSERT
    WITH CHECK (
        tenant_id = current_tenant_id()
        AND current_user_role() IN ('admin', 'manager')
    );

CREATE POLICY customers_update_tenant ON customers
    FOR UPDATE
    USING (
        tenant_id = current_tenant_id()
        AND current_user_role() IN ('admin', 'manager')
    )
    WITH CHECK (tenant_id = current_tenant_id());
