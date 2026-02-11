-- Migration 001: Create enrichment pipeline tables
-- Module: stakeholder_enrichment
-- Tables: enrichment_profiles, icp_fit_assessments, demo_project_ideas
-- Depends on: beta_applications (must exist), icp_definitions (must exist)

-- ==========================================================================
-- enrichment_profiles
-- ==========================================================================

CREATE TABLE IF NOT EXISTS enrichment_profiles (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    beta_application_id     uuid        NOT NULL REFERENCES beta_applications(id) ON DELETE CASCADE,

    -- Status
    enrichment_status       text        NOT NULL DEFAULT 'pending'
                            CHECK (enrichment_status IN (
                                'pending', 'enriching', 'scored', 'accepted',
                                'ideas_ready', 'booked', 'content_ready', 'seeded', 'failed'
                            )),
    error_log               jsonb,

    -- PDL enrichment
    pdl_data                jsonb,
    pdl_job_title           text,
    pdl_company_name        text,
    pdl_industry            text,
    pdl_company_size        text,
    pdl_location            text,
    pdl_seniority           text,
    pdl_skills              jsonb       DEFAULT '[]'::jsonb,
    pdl_enriched_at         timestamptz,

    -- BrightData LinkedIn enrichment
    brightdata_data         jsonb,
    linkedin_headline       text,
    linkedin_about          text,
    linkedin_posts          jsonb,
    linkedin_recommendations jsonb,
    brightdata_enriched_at  timestamptz,

    -- Firecrawl website enrichment
    firecrawl_data          jsonb,
    firecrawl_services      jsonb,
    firecrawl_industries    jsonb,
    firecrawl_enriched_at   timestamptz,

    -- Claude synthesis
    consultant_assessment   jsonb,
    consultant_summary      text,

    -- ICP pre-scoring
    pre_call_icp_score      int,
    pre_call_fit_category   text,
    pre_call_icp_reasoning  text,

    -- Timestamps
    created_at              timestamptz DEFAULT now(),
    updated_at              timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_enrichment_profiles_beta_app
    ON enrichment_profiles (beta_application_id);

CREATE INDEX IF NOT EXISTS idx_enrichment_profiles_status
    ON enrichment_profiles (enrichment_status);

ALTER TABLE enrichment_profiles ENABLE ROW LEVEL SECURITY;


-- ==========================================================================
-- icp_fit_assessments
-- ==========================================================================

CREATE TABLE IF NOT EXISTS icp_fit_assessments (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    enrichment_profile_id   uuid        NOT NULL REFERENCES enrichment_profiles(id) ON DELETE CASCADE,
    icp_definition_id       uuid        REFERENCES icp_definitions(id) ON DELETE SET NULL,
    overall_score           int         NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    attribute_scores        jsonb       DEFAULT '{}'::jsonb,
    reasoning               text,
    fit_category            text        NOT NULL
                            CHECK (fit_category IN ('strong_fit', 'moderate_fit', 'weak_fit', 'anti_pattern')),
    created_at              timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_icp_fit_enrichment_profile
    ON icp_fit_assessments (enrichment_profile_id);

CREATE INDEX IF NOT EXISTS idx_icp_fit_category
    ON icp_fit_assessments (fit_category);

ALTER TABLE icp_fit_assessments ENABLE ROW LEVEL SECURITY;


-- ==========================================================================
-- demo_project_ideas
-- ==========================================================================

CREATE TABLE IF NOT EXISTS demo_project_ideas (
    id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    enrichment_profile_id   uuid        NOT NULL REFERENCES enrichment_profiles(id) ON DELETE CASCADE,
    rank                    int         NOT NULL DEFAULT 1,
    title                   text,
    fictional_client        jsonb,
    problem_statement       text,
    proposed_solution       text,
    prototype_type          text,
    why_this_is_perfect     text,
    wow_factor              text,
    created_at              timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_demo_ideas_enrichment_profile
    ON demo_project_ideas (enrichment_profile_id);

ALTER TABLE demo_project_ideas ENABLE ROW LEVEL SECURITY;
