-- Migration 001: Create ICP Intelligence tables
-- Module: icp_signal_extraction
-- Schema: icp_intelligence
-- Tables: profiles, signals, clusters, cluster_signals, pipeline_runs, config
-- Depends on: pgvector extension (must be enabled)

CREATE SCHEMA IF NOT EXISTS icp_intelligence;

-- ── Profiles ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('active', 'draft', 'archived')),
    pain_points TEXT[] DEFAULT '{}',
    goals TEXT[] DEFAULT '{}',
    triggers TEXT[] DEFAULT '{}',
    objections TEXT[] DEFAULT '{}',
    demographics JSONB DEFAULT '{}',
    technical_profile JSONB DEFAULT '{}',
    client_profile JSONB DEFAULT '{}',
    success_criteria JSONB DEFAULT '{}',
    profile_embedding vector(1536),
    signal_count INT NOT NULL DEFAULT 0,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    promoted_from_cluster_id UUID,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Signals ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL CHECK (source_type IN ('call_transcript', 'beta_application')),
    source_id UUID,
    source_metadata JSONB DEFAULT '{}',
    signal_type TEXT NOT NULL CHECK (signal_type IN ('pain_point', 'goal', 'trigger', 'objection', 'demographic', 'surprise')),
    title TEXT NOT NULL,
    description TEXT,
    quote TEXT,
    confidence FLOAT NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    signal_embedding vector(1536),
    routed_to_profile_id UUID REFERENCES icp_intelligence.profiles(id) ON DELETE SET NULL,
    similarity_score FLOAT,
    routing_status TEXT NOT NULL DEFAULT 'pending' CHECK (routing_status IN ('pending', 'auto_routed', 'review_required', 'manually_routed', 'outlier')),
    review_action TEXT CHECK (review_action IN ('accepted', 'rejected', 'rerouted', 'new_cluster') OR review_action IS NULL),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    pipeline_run_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Clusters ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    description TEXT,
    centroid_embedding vector(1536),
    signal_count INT NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'emerging' CHECK (status IN ('emerging', 'stable', 'promoted', 'dismissed')),
    promoted_to_profile_id UUID REFERENCES icp_intelligence.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Cluster Signals (junction) ────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.cluster_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID NOT NULL REFERENCES icp_intelligence.clusters(id) ON DELETE CASCADE,
    signal_id UUID NOT NULL REFERENCES icp_intelligence.signals(id) ON DELETE CASCADE,
    similarity_to_centroid FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cluster_id, signal_id)
);

-- ── Pipeline Runs ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,
    source_id UUID,
    status TEXT NOT NULL DEFAULT 'started' CHECK (status IN ('started', 'extracting', 'embedding', 'routing', 'clustering', 'completed', 'failed')),
    signals_extracted INT NOT NULL DEFAULT 0,
    signals_auto_routed INT NOT NULL DEFAULT 0,
    signals_review_required INT NOT NULL DEFAULT 0,
    signals_outlier INT NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Config ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS icp_intelligence.config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,
    value JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Deferred FKs ──────────────────────────────────────────

ALTER TABLE icp_intelligence.signals
    ADD CONSTRAINT signals_pipeline_run_id_fk
    FOREIGN KEY (pipeline_run_id) REFERENCES icp_intelligence.pipeline_runs(id) ON DELETE SET NULL;

ALTER TABLE icp_intelligence.profiles
    ADD CONSTRAINT profiles_promoted_from_cluster_id_fk
    FOREIGN KEY (promoted_from_cluster_id) REFERENCES icp_intelligence.clusters(id) ON DELETE SET NULL;

-- ── Indexes ───────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_signals_routing_status ON icp_intelligence.signals(routing_status);
CREATE INDEX IF NOT EXISTS idx_signals_profile_id ON icp_intelligence.signals(routed_to_profile_id);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON icp_intelligence.signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON icp_intelligence.pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_config_key ON icp_intelligence.config(key);
CREATE INDEX IF NOT EXISTS idx_clusters_status ON icp_intelligence.clusters(status);

-- HNSW indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_signals_embedding ON icp_intelligence.signals
    USING hnsw (signal_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_profiles_embedding ON icp_intelligence.profiles
    USING hnsw (profile_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_clusters_centroid ON icp_intelligence.clusters
    USING hnsw (centroid_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ── Row Level Security ────────────────────────────────────

ALTER TABLE icp_intelligence.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_intelligence.signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_intelligence.clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_intelligence.cluster_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_intelligence.pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_intelligence.config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON icp_intelligence.profiles FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON icp_intelligence.signals FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON icp_intelligence.clusters FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON icp_intelligence.cluster_signals FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON icp_intelligence.pipeline_runs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON icp_intelligence.config FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "authenticated_read" ON icp_intelligence.profiles FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated_read" ON icp_intelligence.signals FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated_read" ON icp_intelligence.clusters FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated_read" ON icp_intelligence.cluster_signals FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated_read" ON icp_intelligence.pipeline_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated_read" ON icp_intelligence.config FOR SELECT TO authenticated USING (true);
