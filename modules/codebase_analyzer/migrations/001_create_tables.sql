-- Migration 001: Create codebase_context table
-- Module: codebase_analyzer
-- Stores AI-generated codebase context documents for use in instruction generation

CREATE TABLE IF NOT EXISTS codebase_context (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    content         text        NOT NULL,
    file_tree       text,
    generated_at    timestamptz NOT NULL DEFAULT now(),
    model_used      text        NOT NULL DEFAULT 'claude-sonnet-4-20250514',
    status          text        NOT NULL DEFAULT 'current'
                    CHECK (status IN ('current', 'stale', 'generating')),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_codebase_context_status
    ON codebase_context (status);

ALTER TABLE codebase_context ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on codebase_context"
    ON codebase_context FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read on codebase_context"
    ON codebase_context FOR SELECT TO authenticated USING (true);
