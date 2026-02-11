"""Pydantic models for the stakeholder enrichment module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EnrichmentRequest(BaseModel):
    """Request to trigger a stakeholder enrichment pipeline."""

    stakeholder_name: str = Field(
        ...,
        description="Full name of the stakeholder to enrich.",
        min_length=1,
        max_length=256,
    )
    linkedin_url: str | None = Field(
        default=None,
        description="LinkedIn profile URL for the stakeholder.",
    )
    company_url: str | None = Field(
        default=None,
        description="Company website URL associated with the stakeholder.",
    )
    additional_context: str | None = Field(
        default=None,
        description="Free-text context to guide enrichment (role, interests, etc.).",
    )


class EnrichmentSource(BaseModel):
    """A single data source used during enrichment."""

    source_type: str = Field(
        ...,
        description="Type of source (e.g., 'linkedin', 'company_website', 'crunchbase').",
    )
    url: str = Field(
        ...,
        description="URL that was fetched for this source.",
    )
    raw_data: dict = Field(
        default_factory=dict,
        description="Raw extracted data from the source.",
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when data was extracted from this source.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the data extracted from this source (0.0 to 1.0).",
    )


class EnrichmentProfile(BaseModel):
    """A fully enriched stakeholder profile."""

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the enrichment profile.",
    )
    stakeholder_name: str = Field(
        ...,
        description="Full name of the stakeholder.",
    )
    sources: list[EnrichmentSource] = Field(
        default_factory=list,
        description="List of sources used during enrichment.",
    )
    synthesis: str = Field(
        default="",
        description="AI-synthesized narrative profile of the stakeholder.",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the enriched profile (0.0 to 1.0).",
    )
    icp_signals: list[str] = Field(
        default_factory=list,
        description="ICP (Ideal Customer Profile) signals extracted from the profile.",
    )
    suggested_projects: list[str] = Field(
        default_factory=list,
        description="Suggested project ideas based on the stakeholder's profile.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the profile was created.",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the profile was last updated.",
    )


class EnrichmentResponse(BaseModel):
    """Response returned after triggering or completing an enrichment."""

    profile: EnrichmentProfile = Field(
        ...,
        description="The enriched stakeholder profile.",
    )
    status: str = Field(
        default="completed",
        description="Status of the enrichment (e.g., 'completed', 'pending', 'failed').",
    )


class EnrichmentListResponse(BaseModel):
    """Response for listing multiple enrichment profiles."""

    profiles: list[EnrichmentProfile] = Field(
        default_factory=list,
        description="List of enrichment profiles.",
    )
    total: int = Field(
        default=0,
        description="Total number of profiles matching the query.",
    )
