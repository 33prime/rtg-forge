"""Pydantic models for the stakeholder enrichment module.

Mirrors the production models from icp-service/app/models/enrichment.py
plus synthesis output schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# API Request / Response
# ---------------------------------------------------------------------------


class EnrichRequest(BaseModel):
    """Trigger enrichment for a beta applicant."""

    beta_application_id: str = Field(
        ..., description="UUID of the beta_applications row to enrich."
    )


class EnrichResponse(BaseModel):
    """Acknowledgement that enrichment has been queued."""

    status: str = Field(default="accepted", description="Always 'accepted' — pipeline runs as background task.")
    message: str = Field(default="Enrichment started")


class GenerateIdeasRequest(BaseModel):
    """Trigger project idea generation for an enriched profile."""

    enrichment_profile_id: str = Field(
        ..., description="UUID of the enrichment_profiles row."
    )


class GenerateIdeasResponse(BaseModel):
    """Acknowledgement that idea generation has been queued."""

    status: str = Field(default="accepted")
    message: str = Field(default="Idea generation started")


# ---------------------------------------------------------------------------
# Synthesis Output Schemas
# ---------------------------------------------------------------------------


class ConsultantAssessment(BaseModel):
    """Structured output from Claude deep synthesis."""

    practice_maturity: int | None = Field(default=None, description="1-10 score")
    ai_readiness: int | None = Field(default=None, description="1-10 score")
    client_sophistication: int | None = Field(default=None, description="1-10 score")
    revenue_potential: int | None = Field(default=None, description="1-10 score")
    engagement_complexity: int | None = Field(default=None, description="1-10 score")
    primary_vertical: str | None = None
    seniority_tier: str | None = Field(
        default=None, description="solo | boutique_leader | mid_firm | enterprise"
    )
    consultant_summary: str | None = None
    key_strengths: list[str] = Field(default_factory=list)
    potential_concerns: list[str] = Field(default_factory=list)
    recommended_approach: str | None = None


class IcpPreScore(BaseModel):
    """Structured output from Claude ICP pre-scoring."""

    overall_score: int = Field(..., ge=0, le=100, description="0-100 integer score")
    fit_category: str = Field(
        ..., description="strong_fit | moderate_fit | weak_fit | anti_pattern"
    )
    reasoning: str = Field(..., description="2-3 sentences explaining the score")
    attribute_scores: dict = Field(
        default_factory=dict,
        description="Per-attribute scores: practice_maturity, ai_readiness, client_base, engagement_style, growth_potential",
    )
