"""Pydantic models for the ICP signal extraction module.

Covers all request/response schemas, domain models for signals, profiles,
clusters, pipeline runs, and enums.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SignalType(str, Enum):
    PAIN_POINT = "pain_point"
    GOAL = "goal"
    TRIGGER = "trigger"
    OBJECTION = "objection"
    DEMOGRAPHIC = "demographic"
    SURPRISE = "surprise"


class SourceType(str, Enum):
    CALL_TRANSCRIPT = "call_transcript"
    BETA_APPLICATION = "beta_application"


class RoutingStatus(str, Enum):
    PENDING = "pending"
    AUTO_ROUTED = "auto_routed"
    REVIEW_REQUIRED = "review_required"
    MANUALLY_ROUTED = "manually_routed"
    OUTLIER = "outlier"


class ReviewAction(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REROUTED = "rerouted"
    NEW_CLUSTER = "new_cluster"


class ProfileStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ClusterStatus(str, Enum):
    EMERGING = "emerging"
    STABLE = "stable"
    PROMOTED = "promoted"
    DISMISSED = "dismissed"


class PipelineRunStatus(str, Enum):
    STARTED = "started"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    ROUTING = "routing"
    CLUSTERING = "clustering"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Webhook payloads
# ---------------------------------------------------------------------------


class CallAnalyzedPayload(BaseModel):
    """Webhook payload from the analyze-call edge function."""

    call_recording_id: str = Field(..., description="UUID of the call recording")
    call_analysis_id: str | None = Field(default=None, description="UUID of the call analysis")
    transcript: str | None = None
    summary: str | None = None
    key_moments: list[dict] | None = None


class BetaEnrichedPayload(BaseModel):
    """Webhook payload from the enrich-beta-applicant edge function."""

    beta_application_id: str = Field(..., description="UUID of the beta application")
    enrichment_profile_id: str | None = None
    company_name: str | None = None
    role: str | None = None
    enrichment_data: dict | None = None


# ---------------------------------------------------------------------------
# API responses
# ---------------------------------------------------------------------------


class WebhookAccepted(BaseModel):
    """Acknowledgement that a webhook has been accepted for processing."""

    status: str = Field(default="accepted")
    source_type: str
    source_id: str


class RecomputeResponse(BaseModel):
    """Acknowledgement that cluster recompute has started."""

    status: str = Field(default="accepted")
    message: str = Field(default="Cluster recompute started")


class PromoteResponse(BaseModel):
    """Result of promoting a cluster to a profile."""

    status: str = Field(default="promoted")
    profile_id: str


class ReviewResponse(BaseModel):
    """Result of reviewing a signal."""

    status: str = Field(default="reviewed")
    action: str


class DismissResponse(BaseModel):
    """Result of dismissing a cluster."""

    status: str = Field(default="dismissed")


class MetricsResponse(BaseModel):
    """Dashboard metrics for the ICP intelligence tab."""

    total_signals: int = 0
    pending_review: int = 0
    active_profiles: int = 0
    active_clusters: int = 0
    signals_by_type: dict[str, int] = Field(default_factory=dict)
    signals_by_status: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class SignalCreate(BaseModel):
    """Create a new signal."""

    source_type: SourceType
    source_id: str | None = None
    source_metadata: dict = Field(default_factory=dict)
    signal_type: SignalType
    title: str
    description: str | None = None
    quote: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)


class Signal(BaseModel):
    """A stored ICP signal."""

    id: str
    source_type: SourceType
    source_id: str | None = None
    source_metadata: dict = Field(default_factory=dict)
    signal_type: SignalType
    title: str
    description: str | None = None
    quote: str | None = None
    confidence: float
    routed_to_profile_id: str | None = None
    similarity_score: float | None = None
    routing_status: RoutingStatus
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_action: ReviewAction | None = None
    pipeline_run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class SignalWithContext(Signal):
    """Signal with joined profile/cluster names for display."""

    profile_name: str | None = None
    cluster_name: str | None = None


class SignalReview(BaseModel):
    """Request body for reviewing a signal."""

    action: ReviewAction
    target_profile_id: str | None = None
    reviewed_by: str = "admin"


class ProfileCreate(BaseModel):
    """Create a new ICP profile."""

    name: str
    pain_points: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    demographics: dict = Field(default_factory=dict)
    technical_profile: dict = Field(default_factory=dict)
    client_profile: dict = Field(default_factory=dict)
    success_criteria: dict = Field(default_factory=dict)


class Profile(BaseModel):
    """A stored ICP profile."""

    id: str
    name: str
    version: int
    status: ProfileStatus
    pain_points: list[str]
    goals: list[str]
    triggers: list[str]
    objections: list[str]
    demographics: dict
    technical_profile: dict = Field(default_factory=dict)
    client_profile: dict = Field(default_factory=dict)
    success_criteria: dict = Field(default_factory=dict)
    signal_count: int
    confidence: float
    promoted_from_cluster_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class ProfileDetail(Profile):
    """Profile with signals and aggregate stats."""

    signals: list[Signal] = Field(default_factory=list)
    signal_stats: dict = Field(default_factory=dict)


class Cluster(BaseModel):
    """A signal cluster."""

    id: str
    name: str | None = None
    description: str | None = None
    signal_count: int
    status: ClusterStatus
    promoted_to_profile_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ClusterDetail(Cluster):
    """Cluster with member signals."""

    signals: list = Field(default_factory=list)


class ClusterPromote(BaseModel):
    """Request body for promoting a cluster to a profile."""

    profile_name: str


class PipelineRun(BaseModel):
    """A pipeline execution record."""

    id: str
    source_type: str
    source_id: str | None = None
    status: PipelineRunStatus
    signals_extracted: int
    signals_auto_routed: int
    signals_review_required: int
    signals_outlier: int
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
