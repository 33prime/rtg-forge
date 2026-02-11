"""Business logic for the stakeholder enrichment module.

This module contains no FastAPI imports. All business logic is
framework-agnostic and operates on Pydantic models and standard
Python types.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from .models import (
    EnrichmentProfile,
    EnrichmentRequest,
    EnrichmentSource,
)


class ProfileNotFoundError(Exception):
    """Raised when a requested enrichment profile does not exist."""

    def __init__(self, profile_id: UUID) -> None:
        self.profile_id = profile_id
        super().__init__(f"Enrichment profile not found: {profile_id}")


class EnrichmentService:
    """Service layer for stakeholder enrichment operations.

    Phase 1: In-memory store with stub enrichment logic.
    Phase 2 (TODO): Supabase persistence + LangGraph enrichment pipeline.
    """

    def __init__(self) -> None:
        # Phase 1: in-memory storage keyed by profile UUID
        self._profiles: dict[UUID, EnrichmentProfile] = {}

    async def enrich_stakeholder(
        self, request: EnrichmentRequest
    ) -> EnrichmentProfile:
        """Trigger enrichment for a stakeholder and return the resulting profile.

        In Phase 1 this creates a stub profile with mock data. In Phase 2
        this will execute the full LangGraph pipeline:
        fetch_sources -> extract_data -> synthesize_profile ->
        score_confidence -> generate_signals.

        Args:
            request: The enrichment request containing stakeholder details
                and source URLs.

        Returns:
            The enriched stakeholder profile.
        """
        now = datetime.utcnow()
        profile_id = uuid4()
        sources: list[EnrichmentSource] = []

        # -- Phase 1: Build stub sources from provided URLs ----------------
        if request.linkedin_url:
            sources.append(
                EnrichmentSource(
                    source_type="linkedin",
                    url=request.linkedin_url,
                    raw_data={"stub": True, "name": request.stakeholder_name},
                    extracted_at=now,
                    confidence=0.7,
                )
            )

        if request.company_url:
            sources.append(
                EnrichmentSource(
                    source_type="company_website",
                    url=request.company_url,
                    raw_data={"stub": True, "name": request.stakeholder_name},
                    extracted_at=now,
                    confidence=0.6,
                )
            )

        # -- Phase 1: Stub synthesis and signals ---------------------------
        context_note = ""
        if request.additional_context:
            context_note = f" Additional context: {request.additional_context}"

        synthesis = (
            f"{request.stakeholder_name} is a stakeholder identified for enrichment."
            f" {len(sources)} source(s) were consulted.{context_note}"
            f" (Phase 1 stub -- full AI synthesis coming in Phase 2.)"
        )

        # TODO Phase 2: Replace stubs with LangGraph pipeline execution
        # pipeline = build_enrichment_graph()
        # result = await pipeline.ainvoke({
        #     "request": request,
        #     "sources": [],
        #     "synthesis": "",
        #     "confidence": 0.0,
        #     "signals": [],
        #     "projects": [],
        # })

        confidence_score = (
            sum(s.confidence for s in sources) / len(sources) if sources else 0.0
        )

        profile = EnrichmentProfile(
            id=profile_id,
            stakeholder_name=request.stakeholder_name,
            sources=sources,
            synthesis=synthesis,
            confidence_score=round(confidence_score, 2),
            icp_signals=["stub-signal"],
            suggested_projects=["stub-project"],
            created_at=now,
            updated_at=now,
        )

        # Persist (Phase 1: in-memory)
        self._profiles[profile_id] = profile
        return profile

    async def get_profile(self, profile_id: UUID) -> EnrichmentProfile | None:
        """Retrieve a single enrichment profile by its ID.

        Args:
            profile_id: UUID of the profile to retrieve.

        Returns:
            The enrichment profile if found, otherwise None.
        """
        # TODO Phase 2: Query Supabase instead of in-memory dict
        return self._profiles.get(profile_id)

    async def list_profiles(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[EnrichmentProfile], int]:
        """List enrichment profiles with pagination.

        Args:
            limit: Maximum number of profiles to return.
            offset: Number of profiles to skip.

        Returns:
            A tuple of (profiles_list, total_count).
        """
        # TODO Phase 2: Query Supabase with LIMIT/OFFSET
        all_profiles = list(self._profiles.values())
        total = len(all_profiles)

        # Sort by created_at descending for consistent ordering
        all_profiles.sort(key=lambda p: p.created_at, reverse=True)

        page = all_profiles[offset : offset + limit]
        return page, total

    async def delete_profile(self, profile_id: UUID) -> bool:
        """Delete an enrichment profile and all associated sources.

        Args:
            profile_id: UUID of the profile to delete.

        Returns:
            True if the profile was deleted, False if it did not exist.
        """
        # TODO Phase 2: Delete from Supabase (CASCADE handles sources)
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False
