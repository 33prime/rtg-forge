-- BAD EXAMPLE — Migration with many schema design problems.
--
-- Problems demonstrated:
-- - No timestamps (created_at, updated_at)
-- - No indexes on foreign keys
-- - Using SERIAL instead of UUID
-- - Using VARCHAR instead of TEXT + CHECK
-- - Using FLOAT for money
-- - Using ENUM instead of TEXT + CHECK
-- - No RLS policies
-- - No ON DELETE behavior on foreign keys
-- - Missing NOT NULL constraints
-- - No CHECK constraints

-- Using SERIAL — not suitable for distributed systems, exposes ordering
CREATE TABLE invoice (  -- Should be plural: invoices
    id SERIAL PRIMARY KEY,  -- Should be UUID
    customer INTEGER REFERENCES customer(id),  -- No ON DELETE, no NOT NULL, no index
    status VARCHAR(20),  -- Should be TEXT + CHECK, also nullable!
    total FLOAT,  -- NEVER use float for money
    notes VARCHAR(255),  -- Arbitrary limit, should be TEXT + CHECK
    data JSON  -- Should be JSONB, not JSON
    -- No created_at!
    -- No updated_at!
    -- No tenant_id for multi-tenancy!
);

-- No indexes at all!

-- Using Postgres ENUM — hard to modify later
CREATE TYPE item_status AS ENUM ('active', 'deleted');

CREATE TABLE invoice_item (  -- Should be line_items (plural, descriptive)
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoice(id),  -- No ON DELETE CASCADE, no index
    name VARCHAR(100),  -- Should be TEXT + CHECK
    qty INTEGER,  -- Not constrained — could be 0 or negative
    price FLOAT,  -- Float for money again!
    status item_status  -- ENUM type, hard to add new values
    -- No created_at!
    -- No updated_at!
    -- No sort_order!
);

-- No RLS! Anyone with access can read/write all rows.
-- No updated_at triggers!
-- No views for common query patterns!
-- No partial indexes for common filters!
