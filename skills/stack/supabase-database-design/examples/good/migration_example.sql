-- Migration: 20260211000003_create_invoices.sql
-- Creates the invoices and line_items tables with proper types,
-- indexes, RLS policies, and audit timestamps.

-- ---------------------------------------------------------------------------
-- Invoices table
-- ---------------------------------------------------------------------------

CREATE TABLE invoices (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    status      TEXT NOT NULL DEFAULT 'draft'
                CHECK(status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    due_date    DATE,
    notes       TEXT CHECK(length(notes) <= 5000),
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Foreign key indexes (Postgres does NOT auto-create these)
CREATE INDEX idx_invoices_tenant_id ON invoices(tenant_id);
CREATE INDEX idx_invoices_customer_id ON invoices(customer_id);

-- Common query pattern: list invoices by tenant + status
CREATE INDEX idx_invoices_tenant_status ON invoices(tenant_id, status);

-- Partial index for active invoices (used in dashboard queries)
CREATE INDEX idx_invoices_unpaid ON invoices(tenant_id, due_date)
    WHERE status NOT IN ('paid', 'cancelled');

-- JSONB index for metadata queries
CREATE INDEX idx_invoices_metadata ON invoices USING GIN(metadata);

-- Updated-at trigger
CREATE TRIGGER set_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ---------------------------------------------------------------------------
-- Line items table
-- ---------------------------------------------------------------------------

CREATE TABLE line_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id  UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 500),
    quantity    INTEGER NOT NULL CHECK(quantity > 0),
    unit_price  NUMERIC(12, 2) NOT NULL CHECK(unit_price >= 0),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Foreign key index
CREATE INDEX idx_line_items_invoice_id ON line_items(invoice_id);

-- Updated-at trigger
CREATE TRIGGER set_line_items_updated_at
    BEFORE UPDATE ON line_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ---------------------------------------------------------------------------
-- RLS Policies
-- ---------------------------------------------------------------------------

ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_items ENABLE ROW LEVEL SECURITY;

-- Invoices: users can only see invoices belonging to their tenant
CREATE POLICY invoices_tenant_isolation ON invoices
    FOR ALL
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

-- Line items: access follows the parent invoice's tenant
CREATE POLICY line_items_tenant_isolation ON line_items
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

-- ---------------------------------------------------------------------------
-- Summary view
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW invoice_summaries AS
SELECT
    i.id,
    i.tenant_id,
    i.customer_id,
    i.status,
    i.due_date,
    i.created_at,
    i.updated_at,
    c.name AS customer_name,
    COUNT(li.id) AS line_item_count,
    COALESCE(SUM(li.quantity * li.unit_price), 0) AS total
FROM invoices i
JOIN customers c ON c.id = i.customer_id
LEFT JOIN line_items li ON li.invoice_id = i.id
GROUP BY i.id, c.id;
