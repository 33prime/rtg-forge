"""FastAPI router for the stakeholder enrichment module.

Endpoints:
  POST /enrich          — trigger full enrichment pipeline (background task)
  POST /generate-ideas  — generate project ideas from stored enrichment data (background task)

Both endpoints are fire-and-forget: they accept the request, queue a background task,
and immediately return an acknowledgement. Pipeline results are written to Supabase.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks

from .config import get_settings
from .models import (
    EnrichRequest,
    EnrichResponse,
    GenerateIdeasRequest,
    GenerateIdeasResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_applicant(
    payload: EnrichRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger full enrichment pipeline. Runs as a background task.

    Routes to LangGraph pipeline if use_langgraph_enrichment is enabled,
    otherwise uses the legacy sequential pipeline.
    """
    settings = get_settings()
    if settings.use_langgraph_enrichment:
        from .graph.runner import run_enrichment_graph

        background_tasks.add_task(run_enrichment_graph, payload.beta_application_id)
    else:
        from .service import run_enrichment_pipeline

        background_tasks.add_task(run_enrichment_pipeline, payload.beta_application_id)
    return EnrichResponse(status="accepted", message="Enrichment started")


@router.post("/generate-ideas", response_model=GenerateIdeasResponse)
async def generate_ideas(
    payload: GenerateIdeasRequest,
    background_tasks: BackgroundTasks,
):
    """Generate personalized project ideas. Runs as a background task."""
    settings = get_settings()
    if settings.use_langgraph_enrichment:
        from .graph.runner import run_ideas_graph

        background_tasks.add_task(run_ideas_graph, payload.enrichment_profile_id)
    else:
        from .service import run_ideas_pipeline

        background_tasks.add_task(run_ideas_pipeline, payload.enrichment_profile_id)
    return GenerateIdeasResponse(status="accepted", message="Idea generation started")
