"""Context Assembly Engine — Type definitions and Pydantic models.

Four core primitives: Block, Situation, ScoringRule, Budget.
Three layers: Goals, Memory, Context.
Unified by temporal metadata.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Temporal Dimension
# ---------------------------------------------------------------------------


class Trend(str, Enum):
    improving = "improving"
    stable = "stable"
    declining = "declining"
    volatile = "volatile"


class TemporalMetadata(BaseModel):
    """Time-series context that turns facts into narratives."""

    first_observed: datetime | None = None
    last_observed: datetime | None = None
    occurrences: int = 0
    trend: Trend = Trend.stable
    current: float = 0.0       # Last 7-14 days
    previous: float = 0.0      # 15-30 days ago
    baseline: float = 0.0      # 60-90 days ago (or start)
    delta: float = 0.0         # current - previous
    velocity: float = 0.0      # Rate of change acceleration


# ---------------------------------------------------------------------------
# Primitive 1: Block
# ---------------------------------------------------------------------------


class Block(BaseModel):
    """Atomic unit of knowledge with metadata for scoring, budgeting,
    and auditability. Every element in the CAE is a Block."""

    key: str
    category: str = ""
    priority: float = 50.0
    base_priority: float = 50.0
    estimated_tokens: int = 0
    included: bool = False
    exclude_reason: str | None = None
    formatted_text: str = ""
    raw_data: Any = None
    signals: list[str] = Field(default_factory=list)
    temporal: TemporalMetadata = Field(default_factory=TemporalMetadata)


# ---------------------------------------------------------------------------
# Primitive 2: Situation
# ---------------------------------------------------------------------------


class Situation(BaseModel):
    """Typed diagnosis computed from all data sources.

    Answers: "What is happening with this entity right now?"
    e.g. "bad round + practice gap + plateau on primary module"
    """

    entity_id: str = ""
    mode: str = "default"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    flags: dict[str, Any] = Field(default_factory=dict)
    narrative: str = ""

    def has_flag(self, flag: str) -> bool:
        return bool(self.flags.get(flag))

    def flag_value(self, flag: str, default: Any = None) -> Any:
        return self.flags.get(flag, default)


# ---------------------------------------------------------------------------
# Primitive 3: Scoring Rule (data representation)
# ---------------------------------------------------------------------------


class ScoringAdjustment(BaseModel):
    block_key: str
    adjustment: float


class ScoringRuleDef(BaseModel):
    """Serializable scoring rule definition (for storage/config)."""

    name: str
    description: str = ""
    condition_flag: str = ""
    condition_threshold: float = 0.0
    adjustments: list[ScoringAdjustment] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Primitive 4: Budget
# ---------------------------------------------------------------------------


class Budget(BaseModel):
    total_tokens: int = 1800
    used_tokens: int = 0
    remaining_tokens: int = 1800
    blocks_included: int = 0
    blocks_excluded: int = 0


# ---------------------------------------------------------------------------
# Manifest — Full transparency output
# ---------------------------------------------------------------------------


class ManifestEntry(BaseModel):
    key: str
    category: str
    base_priority: float
    final_priority: float
    estimated_tokens: int
    included: bool
    exclude_reason: str | None = None
    signals: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """Complete record of an assembly — what was included, excluded, and why."""

    entity_id: str
    mode: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    situation: Situation
    budget: Budget
    entries: list[ManifestEntry] = Field(default_factory=list)
    assembled_text: str = ""
    total_blocks_considered: int = 0


# ---------------------------------------------------------------------------
# Layer 1: Goals
# ---------------------------------------------------------------------------


class GoalStatus(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    abandoned = "abandoned"


class Goal(BaseModel):
    id: str | None = None
    entity_id: str
    name: str
    description: str = ""
    status: GoalStatus = GoalStatus.active
    priority_adjustments: dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    target_date: datetime | None = None
    progress: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Layer 2: Memory
# ---------------------------------------------------------------------------


class MemoryStage(str, Enum):
    draft = "draft"
    reinforced = "reinforced"
    mature = "mature"
    decaying = "decaying"
    revised = "revised"
    archived = "archived"


class MemoryCategory(str, Enum):
    behavioral_pattern = "behavioral_pattern"
    coaching_thread = "coaching_thread"
    emotional_signature = "emotional_signature"
    domain_knowledge = "domain_knowledge"
    breakthrough_moment = "breakthrough_moment"


class Memory(BaseModel):
    id: str | None = None
    entity_id: str
    category: MemoryCategory
    stage: MemoryStage = MemoryStage.draft
    confidence: float = 0.2
    summary: str
    detail: str = ""
    tags: list[str] = Field(default_factory=list)
    temporal: TemporalMetadata = Field(default_factory=TemporalMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    superseded_by: str | None = None


# ---------------------------------------------------------------------------
# Decision Log
# ---------------------------------------------------------------------------


class DecisionOutcome(BaseModel):
    followed: bool = False
    result: dict[str, float] = Field(default_factory=dict)
    feedback: str | None = None
    feedback_score: float | None = None


class DecisionRecord(BaseModel):
    id: str | None = None
    entity_id: str
    mode: str = "default"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    manifest_summary: dict[str, Any] = Field(default_factory=dict)
    memories_used: list[str] = Field(default_factory=list)
    active_goals: list[str] = Field(default_factory=list)
    recommendation: str = ""
    outcome: DecisionOutcome | None = None


# ---------------------------------------------------------------------------
# Engine Configuration
# ---------------------------------------------------------------------------


class Tier(int, Enum):
    always = 1          # Base priority 90 — always included
    conditional = 2     # Base priority 60 — when signal gate satisfied
    strong_signal = 3   # Base priority 30 — only when highly relevant


TIER_BASE_PRIORITY = {
    Tier.always: 90,
    Tier.conditional: 60,
    Tier.strong_signal: 30,
}


class BlockDef(BaseModel):
    """Serializable block definition for engine configuration."""

    key: str
    tier: Tier = Tier.conditional
    base_priority: float | None = None
    category: str = "context"
    description: str = ""

    def effective_priority(self) -> float:
        if self.base_priority is not None:
            return self.base_priority
        return TIER_BASE_PRIORITY.get(self.tier, 60)


class ModeConfig(BaseModel):
    """Configuration for a specific operational mode."""

    name: str
    budget: int = 1800
    block_keys: list[str] = Field(default_factory=list)
    description: str = ""


# ---------------------------------------------------------------------------
# API Schemas
# ---------------------------------------------------------------------------


class AssembleRequest(BaseModel):
    entity_id: str
    mode: str = "default"
    data: dict[str, Any] = Field(default_factory=dict)


class AssembleResponse(BaseModel):
    assembled_text: str
    manifest: Manifest


class GoalCreate(BaseModel):
    entity_id: str
    name: str
    description: str = ""
    priority_adjustments: dict[str, float] = Field(default_factory=dict)
    target_date: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GoalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: GoalStatus | None = None
    priority_adjustments: dict[str, float] | None = None
    progress: float | None = None
    metadata: dict[str, Any] | None = None


class MemoryCreate(BaseModel):
    entity_id: str
    category: MemoryCategory
    summary: str
    detail: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    summary: str | None = None
    detail: str | None = None
    stage: MemoryStage | None = None
    confidence: float | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
