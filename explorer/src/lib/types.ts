// Module types
export interface ModuleManifest {
  module: {
    name: string;
    version: string;
    description: string;
    status: 'draft' | 'stable' | 'deprecated';
    category: 'enrichment' | 'intelligence' | 'extraction' | 'integration';
    author: string;
    dependencies: {
      python: string[];
      services: string[];
      modules: string[];
    };
    api: {
      prefix: string;
      auth_required: boolean;
    };
    database: {
      tables: string[];
      requires_rls: boolean;
    };
  };
  ai: {
    use_when: string;
    input_summary: string;
    output_summary: string;
    complexity: 'low' | 'medium' | 'high';
    estimated_setup_minutes: number;
    related_modules: string[];
  };
  health: {
    last_validated: string;
    test_coverage: number;
    known_issues: string[];
  };
}

// Skill types
export interface SkillMeta {
  skill: {
    name: string;
    version: string;
    tier: 'foundation' | 'specialized' | 'workflow';
    category: 'stack' | 'practices' | 'workflows';
    relevance_tags: string[];
    priority_weight: number;
    description: string;
  };
  relationships: {
    prerequisites: string[];
    complements: string[];
    supersedes: string[];
  };
  optimization: {
    last_optimized: string;
    token_count: number;
    token_count_previous: number;
    growth_justified: boolean;
  };
  tracking: {
    common_mistakes: string[];
  };
}

// Profile types
export interface ProfileData {
  profile: {
    name: string;
    display_name: string;
    version: string;
    description: string;
    maturity: 'seed' | 'developing' | 'production' | 'battle-tested';
    vendor: string;
    vendor_url: string;
  };
  base: {
    extends: string;
  };
  constraints: {
    description: string;
    required: Record<string, { name: string; reason: string }>;
    allowed: Record<string, string[]>;
    forbidden: Record<string, string[]>;
    overrides: Record<string, string>;
  };
}

// Search types
export interface SearchResult {
  type: 'module' | 'skill' | 'profile';
  name: string;
  description: string;
  category?: string;
  url: string;
  score: number;
}
