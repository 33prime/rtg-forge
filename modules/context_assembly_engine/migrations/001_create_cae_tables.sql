-- Context Assembly Engine: core tables for goals, memories, decisions, and manifests.

CREATE TABLE cae_goals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id text NOT NULL,
    name text NOT NULL,
    description text DEFAULT '',
    status text DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
    priority_adjustments jsonb DEFAULT '{}',
    target_date timestamptz,
    progress float DEFAULT 0 CHECK (progress >= 0 AND progress <= 1),
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE cae_memories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id text NOT NULL,
    category text NOT NULL CHECK (category IN (
        'behavioral_pattern', 'coaching_thread', 'emotional_signature',
        'domain_knowledge', 'breakthrough_moment'
    )),
    stage text DEFAULT 'draft' CHECK (stage IN (
        'draft', 'reinforced', 'mature', 'decaying', 'revised', 'archived'
    )),
    confidence float DEFAULT 0.2 CHECK (confidence >= 0 AND confidence <= 1),
    summary text NOT NULL,
    detail text DEFAULT '',
    tags text[] DEFAULT '{}',
    temporal jsonb DEFAULT '{}',
    metadata jsonb DEFAULT '{}',
    superseded_by uuid REFERENCES cae_memories(id),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE cae_decision_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id text NOT NULL,
    mode text DEFAULT 'default',
    manifest_summary jsonb DEFAULT '{}',
    memories_used uuid[] DEFAULT '{}',
    active_goals uuid[] DEFAULT '{}',
    recommendation text DEFAULT '',
    outcome jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE cae_manifests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id text NOT NULL,
    mode text DEFAULT 'default',
    situation jsonb NOT NULL DEFAULT '{}',
    budget jsonb NOT NULL DEFAULT '{}',
    entries jsonb NOT NULL DEFAULT '[]',
    assembled_text text DEFAULT '',
    total_blocks_considered int DEFAULT 0,
    created_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX idx_cae_goals_entity ON cae_goals(entity_id);
CREATE INDEX idx_cae_goals_status ON cae_goals(entity_id, status);
CREATE INDEX idx_cae_memories_entity ON cae_memories(entity_id);
CREATE INDEX idx_cae_memories_category ON cae_memories(entity_id, category);
CREATE INDEX idx_cae_memories_stage ON cae_memories(entity_id, stage);
CREATE INDEX idx_cae_decision_log_entity ON cae_decision_log(entity_id);
CREATE INDEX idx_cae_manifests_entity ON cae_manifests(entity_id, mode);
CREATE INDEX idx_cae_manifests_created ON cae_manifests(entity_id, created_at DESC);
