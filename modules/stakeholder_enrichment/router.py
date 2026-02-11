"""FastAPI router for the stakeholder enrichment module."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    EnrichmentListResponse,
    EnrichmentRequest,
    EnrichmentResponse,
)
from .service import EnrichmentService

router = APIRouter()

# ---------------------------------------------------------------------------
# Dependency: singleton service instance
# ---------------------------------------------------------------------------

_service: EnrichmentService | None = None


def get_service() -> EnrichmentService:
    """FastAPI dependency that provides the EnrichmentService singleton."""
    global _service
    if _service is None:
        _service = EnrichmentService()
    return _service


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/enrich",
    response_model=EnrichmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger stakeholder enrichment",
    description=(
        "Submit a stakeholder for multi-source enrichment. Returns the "
        "enriched profile with AI synthesis, confidence scores, ICP "
        "signals, and suggested projects."
    ),
)
async def enrich_stakeholder(
    request: EnrichmentRequest,
    service: EnrichmentService = Depends(get_service),
) -> EnrichmentResponse:
    profile = await service.enrich_stakeholder(request)
    return EnrichmentResponse(profile=profile, status="completed")


@router.get(
    "/profiles/{profile_id}",
    response_model=EnrichmentResponse,
    summary="Get enrichment profile",
    description="Retrieve a single enrichment profile by its UUID.",
)
async def get_profile(
    profile_id: UUID,
    service: EnrichmentService = Depends(get_service),
) -> EnrichmentResponse:
    profile = await service.get_profile(profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment profile not found: {profile_id}",
        )
    return EnrichmentResponse(profile=profile, status="completed")


@router.get(
    "/profiles",
    response_model=EnrichmentListResponse,
    summary="List enrichment profiles",
    description="List enrichment profiles with pagination support.",
)
async def list_profiles(
    limit: int = Query(default=20, ge=1, le=100, description="Number of profiles to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    service: EnrichmentService = Depends(get_service),
) -> EnrichmentListResponse:
    profiles, total = await service.list_profiles(limit=limit, offset=offset)
    return EnrichmentListResponse(profiles=profiles, total=total)


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete enrichment profile",
    description="Delete an enrichment profile and all associated source data.",
)
async def delete_profile(
    profile_id: UUID,
    service: EnrichmentService = Depends(get_service),
) -> None:
    deleted = await service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment profile not found: {profile_id}",
        )
