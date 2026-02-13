"""API endpoints for codebase context management.

Thin router — all business logic lives in service.py.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from .config import get_settings
from .models import ContextResponse, RefreshResponse
from .service import get_current_context, run_refresh_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ContextResponse)
async def get_context():
    """Get the current codebase context document."""
    row = await get_current_context()
    if not row:
        raise HTTPException(status_code=404, detail="No codebase context found. Run a refresh first.")

    return ContextResponse(
        content=row["content"],
        generated_at=row["generated_at"],
        status=row["status"],
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_context(background_tasks: BackgroundTasks):
    """Trigger a codebase context refresh (runs in background).

    Uses incremental mode when existing context is found, full analysis otherwise.
    """
    settings = get_settings()
    if not settings.github_token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured on server")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured on server")

    background_tasks.add_task(run_refresh_pipeline)
    return RefreshResponse()
