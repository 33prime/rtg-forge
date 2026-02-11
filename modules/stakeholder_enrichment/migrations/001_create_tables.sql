-- Migration 001: Create enrichment_profiles and enrichment_sources tables
-- Module: stakeholder_enrichment
-- Created: 2026-02-11

-- ==========================================================================
-- enrichment_profiles
-- ==========================================================================

CREATE TABLE IF NOT EXISTS enrichment_profiles (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    stakeholder_name text       NOT NULL,
    synthesis       text,
    confidence_score float,
    icp_signals     jsonb       DEFAULT '[]'::jsonb,
    suggested_projects jsonb    DEFAULT '[]'::jsonb,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_enrichment_profiles_stakeholder_name
    ON enrichment_profiles (stakeholder_name);

ALTER TABLE enrichment_profiles ENABLE ROW LEVEL SECURITY;

-- ==========================================================================
-- enrichment_sources
-- ==========================================================================

CREATE TABLE IF NOT EXISTS enrichment_sources (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id  uuid        NOT NULL
                            REFERENCES enrichment_profiles (id)
                            ON DELETE CASCADE,
    source_type text        NOT NULL,
    url         text,
    raw_data    jsonb       DEFAULT '{}'::jsonb,
    confidence  float       DEFAULT 0,
    extracted_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_enrichment_sources_profile_id
    ON enrichment_sources (profile_id);

ALTER TABLE enrichment_sources ENABLE ROW LEVEL SECURITY;
