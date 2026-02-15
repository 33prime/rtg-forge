-- Call Intelligence Module — Database Schema
-- Run this migration against your Supabase project.
-- Tables are created in the public schema with RLS enabled.

-- ============================================================
-- 1. call_recordings — primary recording metadata + status
-- ============================================================
CREATE TABLE IF NOT EXISTS call_recordings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_name TEXT,
    contact_email TEXT,
    contact_metadata JSONB DEFAULT '{}',
    recall_bot_id TEXT,
    recall_status TEXT,
    recording_url TEXT,
    audio_url TEXT,
    video_url TEXT,
    duration_seconds INTEGER,
    meeting_url TEXT,
    status TEXT DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'bot_scheduled', 'recording',
            'transcribing', 'analyzing', 'complete',
            'skipped', 'failed'
        )),
    error_log JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_recordings_status ON call_recordings(status);
CREATE INDEX IF NOT EXISTS idx_call_recordings_recall_bot ON call_recordings(recall_bot_id);
CREATE INDEX IF NOT EXISTS idx_call_recordings_created ON call_recordings(created_at DESC);

ALTER TABLE call_recordings ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 2. call_transcripts — full text + speaker-diarized segments
-- ============================================================
CREATE TABLE IF NOT EXISTS call_transcripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    full_text TEXT,
    segments JSONB DEFAULT '[]',
    speaker_map JSONB DEFAULT '{}',
    word_count INTEGER,
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_transcripts_recording ON call_transcripts(call_recording_id);

ALTER TABLE call_transcripts ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 3. call_analyses — scores, ratios, timeline, summary
-- ============================================================
CREATE TABLE IF NOT EXISTS call_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    analysis_model TEXT,
    analysis_tokens_used INTEGER,
    executive_summary TEXT,
    engagement_score INTEGER,
    prospect_readiness_score INTEGER,
    talk_ratio JSONB,
    engagement_timeline JSONB DEFAULT '[]',
    prospect_readiness JSONB,
    custom_dimensions JSONB DEFAULT '{}',
    raw_analysis JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_analyses_recording ON call_analyses(call_recording_id);

ALTER TABLE call_analyses ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 4. call_feature_insights — feature reactions + quotes
-- ============================================================
CREATE TABLE IF NOT EXISTS call_feature_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_analysis_id UUID NOT NULL REFERENCES call_analyses(id) ON DELETE CASCADE,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    reaction TEXT CHECK (reaction IN ('positive', 'negative', 'neutral', 'confused')),
    is_feature_request BOOLEAN DEFAULT FALSE,
    is_aha_moment BOOLEAN DEFAULT FALSE,
    description TEXT,
    quote TEXT,
    timestamp_start TEXT,
    timestamp_end TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_features_recording ON call_feature_insights(call_recording_id);
CREATE INDEX IF NOT EXISTS idx_call_features_analysis ON call_feature_insights(call_analysis_id);

ALTER TABLE call_feature_insights ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 5. call_signals — ICP / market signals
-- ============================================================
CREATE TABLE IF NOT EXISTS call_signals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_analysis_id UUID NOT NULL REFERENCES call_analyses(id) ON DELETE CASCADE,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    intensity INTEGER,
    quote TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_signals_recording ON call_signals(call_recording_id);
CREATE INDEX IF NOT EXISTS idx_call_signals_type ON call_signals(signal_type);

ALTER TABLE call_signals ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 6. call_coaching_moments — performance feedback
-- ============================================================
CREATE TABLE IF NOT EXISTS call_coaching_moments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_analysis_id UUID NOT NULL REFERENCES call_analyses(id) ON DELETE CASCADE,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    moment_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    suggestion TEXT,
    quote TEXT,
    timestamp_start TEXT,
    timestamp_end TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_coaching_recording ON call_coaching_moments(call_recording_id);
CREATE INDEX IF NOT EXISTS idx_call_coaching_type ON call_coaching_moments(moment_type);

ALTER TABLE call_coaching_moments ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 7. call_content_nuggets — reusable content extracts
-- ============================================================
CREATE TABLE IF NOT EXISTS call_content_nuggets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_analysis_id UUID NOT NULL REFERENCES call_analyses(id) ON DELETE CASCADE,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    nugget_type TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    industry TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_nuggets_recording ON call_content_nuggets(call_recording_id);

ALTER TABLE call_content_nuggets ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- 8. call_competitive_mentions — competitor tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS call_competitive_mentions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_analysis_id UUID NOT NULL REFERENCES call_analyses(id) ON DELETE CASCADE,
    call_recording_id UUID NOT NULL REFERENCES call_recordings(id) ON DELETE CASCADE,
    competitor_name TEXT NOT NULL,
    mention_context TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    features_compared TEXT[] DEFAULT '{}',
    switching_signals TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_competitive_recording ON call_competitive_mentions(call_recording_id);

ALTER TABLE call_competitive_mentions ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Updated_at trigger (apply to tables that have updated_at)
-- ============================================================
CREATE OR REPLACE FUNCTION call_intelligence_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_call_recordings_updated
    BEFORE UPDATE ON call_recordings
    FOR EACH ROW
    EXECUTE FUNCTION call_intelligence_update_timestamp();
