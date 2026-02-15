"""Pydantic models for the Call Intelligence module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RecordingStatus(str, Enum):
    pending = "pending"
    bot_scheduled = "bot_scheduled"
    recording = "recording"
    transcribing = "transcribing"
    analyzing = "analyzing"
    complete = "complete"
    skipped = "skipped"
    failed = "failed"


class Reaction(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    confused = "confused"


class SignalType(str, Enum):
    pain_point = "pain_point"
    goal = "goal"
    tool_mentioned = "tool_mentioned"
    budget_signal = "budget_signal"
    timeline = "timeline"
    decision_process = "decision_process"
    maturity_indicator = "maturity_indicator"


class MomentType(str, Enum):
    strength = "strength"
    improvement = "improvement"
    missed_opportunity = "missed_opportunity"
    objection_handled = "objection_handled"
    objection_missed = "objection_missed"


class NuggetType(str, Enum):
    quote = "quote"
    pain_framing = "pain_framing"
    terminology = "terminology"
    objection = "objection"
    success_metric = "success_metric"
    industry_insight = "industry_insight"


class CompetitiveSentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class ReadinessMode(str, Enum):
    exploring = "exploring"
    evaluating = "evaluating"
    ready_to_buy = "ready_to_buy"
    not_interested = "not_interested"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ScheduleRecordingRequest(BaseModel):
    meeting_url: str
    contact_name: str | None = None
    contact_email: str | None = None
    contact_metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleRecordingResponse(BaseModel):
    success: bool
    recording_id: UUID | None = None
    recall_bot_id: str | None = None
    status: RecordingStatus
    message: str = ""


class RecallWebhookPayload(BaseModel):
    """Flexible payload — Recall.ai sends varying structures."""
    event: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    def get_bot_id(self) -> str | None:
        return (
            self.data.get("bot", {}).get("id")
            or self.data.get("bot_id")
            or self.data.get("id")
        )

    def get_event(self) -> str:
        return self.event or self.data.get("data", {}).get("code", "unknown")


class AnalyzeRequest(BaseModel):
    recording_id: UUID
    context_blocks: dict[str, str] = Field(
        default_factory=dict,
        description="Optional markdown context blocks keyed by label.",
    )


class AnalyzeResponse(BaseModel):
    success: bool
    analysis_id: UUID | None = None
    engagement_score: int | None = None
    tokens_used: int | None = None
    dimensions_processed: list[str] = []
    message: str = ""


class WebhookAccepted(BaseModel):
    status: str = "accepted"
    message: str = ""


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------

class TranscriptSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float


class Transcript(BaseModel):
    full_text: str
    segments: list[TranscriptSegment] = []
    speaker_map: dict[str, str] = Field(default_factory=dict)
    word_count: int | None = None
    duration_seconds: int | None = None


# ---------------------------------------------------------------------------
# Analysis result sub-models
# ---------------------------------------------------------------------------

class FeatureInsight(BaseModel):
    feature_name: str
    reaction: Reaction
    is_feature_request: bool = False
    is_aha_moment: bool = False
    description: str | None = None
    quote: str | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None


class Signal(BaseModel):
    signal_type: SignalType
    title: str
    description: str | None = None
    intensity: int | None = None
    quote: str | None = None


class CoachingMoment(BaseModel):
    moment_type: MomentType
    title: str
    description: str | None = None
    suggestion: str | None = None
    quote: str | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None


class ContentNugget(BaseModel):
    nugget_type: NuggetType
    content: str
    context: str | None = None
    industry: str | None = None


class CompetitiveMention(BaseModel):
    competitor_name: str
    mention_context: str | None = None
    sentiment: CompetitiveSentiment = CompetitiveSentiment.neutral
    features_compared: list[str] = []
    switching_signals: list[str] = []


class EngagementPoint(BaseModel):
    timestamp: str
    level: int
    note: str = ""


class ProspectReadiness(BaseModel):
    urgency_score: int = 0
    mode: ReadinessMode = ReadinessMode.exploring
    accelerators: list[str] = []
    follow_up_strategy: str = ""


class TalkRatio(BaseModel):
    presenter: float = 0.5
    prospect: float = 0.5


class AnalysisResult(BaseModel):
    """Full structured output from the analysis engine."""
    executive_summary: str = ""
    engagement_score: int = 0
    talk_ratio: TalkRatio = Field(default_factory=TalkRatio)
    engagement_timeline: list[EngagementPoint] = []
    feature_insights: list[FeatureInsight] = []
    signals: list[Signal] = []
    coaching_moments: list[CoachingMoment] = []
    content_nuggets: list[ContentNugget] = []
    competitive_intel: list[CompetitiveMention] = []
    prospect_readiness: ProspectReadiness = Field(default_factory=ProspectReadiness)
    custom_dimensions: dict[str, Any] = Field(default_factory=dict)
