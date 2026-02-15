"""FastAPI router for the Call Intelligence module.

Endpoints:
  POST /recordings/schedule     — schedule a recording bot
  POST /webhooks/recall         — Recall.ai webhook receiver
  POST /recordings/{id}/analyze — trigger (re-)analysis
  GET  /recordings              — list all recordings
  GET  /recordings/{id}         — get single recording
  GET  /recordings/{id}/details — get full analysis details
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

from .config import get_settings
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    RecallWebhookPayload,
    ScheduleRecordingRequest,
    ScheduleRecordingResponse,
    WebhookAccepted,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Lazy service factory — creates per-request to avoid import-time side effects.
# In production, use FastAPI Depends() with a lifespan-managed singleton.
# ---------------------------------------------------------------------------

_service_instance = None


async def _get_service():
    global _service_instance
    if _service_instance is None:
        from supabase import acreate_client

        settings = get_settings()
        client = await acreate_client(settings.supabase_url, settings.supabase_service_key)
        from .service import CallIntelligenceService

        _service_instance = CallIntelligenceService(settings, client)
    return _service_instance


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/recordings/schedule", response_model=ScheduleRecordingResponse)
async def schedule_recording(req: ScheduleRecordingRequest):
    """Schedule a recording bot for a meeting.

    Supports Google Meet, Zoom, and Microsoft Teams.
    """
    service = await _get_service()
    return await service.schedule_bot(req)


@router.post("/webhooks/recall", response_model=WebhookAccepted)
async def recall_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Recall.ai bot status webhooks.

    Configure this URL in your Recall.ai dashboard:
    https://your-domain.com/api/v1/call-intelligence/webhooks/recall
    """
    from .providers.recall import RecallClient

    settings = get_settings()
    recall = RecallClient(settings)

    body = await request.body()
    headers = dict(request.headers)
    if not recall.verify_webhook(body, headers):
        logger.warning("Invalid Recall webhook signature")
        return Response(status_code=401, content="Invalid signature")

    payload = RecallWebhookPayload.model_validate_json(body)
    bot_id = payload.get_bot_id()
    event = payload.get_event()

    if not bot_id:
        return WebhookAccepted(status="ignored", message="No bot ID in payload")

    service = await _get_service()
    background_tasks.add_task(service.handle_recall_event, event, bot_id, payload.data)

    return WebhookAccepted(status="accepted", message=f"Processing {event}")


@router.post("/recordings/{recording_id}/analyze", response_model=AnalyzeResponse)
async def analyze_recording(recording_id: UUID, req: AnalyzeRequest | None = None):
    """Manually trigger (re-)analysis of a recording."""
    service = await _get_service()
    context_blocks = req.context_blocks if req else None
    return await service.analyze_call(recording_id, context_blocks)


@router.get("/recordings")
async def list_recordings():
    """List all call recordings, most recent first."""
    service = await _get_service()
    return await service.list_recordings()


@router.get("/recordings/{recording_id}")
async def get_recording(recording_id: UUID):
    """Get a single recording by ID."""
    service = await _get_service()
    rec = await service.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recording not found")
    return rec


@router.get("/recordings/{recording_id}/details")
async def get_recording_details(recording_id: UUID):
    """Get full analysis details for a recording."""
    service = await _get_service()
    return await service.get_call_details(recording_id)
