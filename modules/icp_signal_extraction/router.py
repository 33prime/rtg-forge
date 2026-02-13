"""FastAPI router for the ICP signal extraction module.

Endpoints:
  Webhooks:
    POST /webhooks/call-analyzed     — trigger pipeline from call analysis
    POST /webhooks/beta-enriched     — trigger pipeline from beta enrichment

  Profiles:
    GET  /profiles                   — list ICP profiles
    GET  /profiles/{id}              — get single profile
    GET  /profiles/{id}/detail       — profile with signals + stats
    POST /profiles                   — create new profile
    POST /profiles/{id}/activate     — set as active (archives others)

  Signals:
    GET  /signals/review-queue       — signals pending human review
    GET  /signals/recent             — recently processed signals
    POST /signals/{id}/review        — accept/reject/reroute signal
    GET  /signals/similar            — ad hoc similarity search

  Clusters:
    GET  /clusters                   — list clusters
    GET  /clusters/{id}              — cluster with member signals
    POST /clusters/{id}/promote      — promote to new profile
    POST /clusters/{id}/dismiss      — dismiss cluster
    POST /clusters/recompute         — trigger DBSCAN re-clustering

  Metrics:
    GET  /metrics                    — dashboard metrics

All mutating endpoints are fire-and-forget background tasks where appropriate.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from .config import get_settings
from .models import (
    CallAnalyzedPayload,
    BetaEnrichedPayload,
    Cluster,
    ClusterDetail,
    ClusterPromote,
    DismissResponse,
    MetricsResponse,
    Profile,
    ProfileCreate,
    ProfileDetail,
    PromoteResponse,
    RecomputeResponse,
    ReviewResponse,
    SignalReview,
    SignalWithContext,
    WebhookAccepted,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


@router.post("/webhooks/call-analyzed", response_model=WebhookAccepted)
async def handle_call_analyzed(
    payload: CallAnalyzedPayload,
    background_tasks: BackgroundTasks,
):
    """Webhook from analyze-call edge function. Triggers ICP extraction pipeline."""
    raw_content = {
        "call_recording_id": payload.call_recording_id,
        "call_analysis_id": payload.call_analysis_id,
        "transcript": payload.transcript,
        "summary": payload.summary,
        "key_moments": payload.key_moments,
    }

    from .graph.runner import run_pipeline

    background_tasks.add_task(run_pipeline, "call_transcript", payload.call_recording_id, raw_content)
    return WebhookAccepted(source_type="call_transcript", source_id=payload.call_recording_id)


@router.post("/webhooks/beta-enriched", response_model=WebhookAccepted)
async def handle_beta_enriched(
    payload: BetaEnrichedPayload,
    background_tasks: BackgroundTasks,
):
    """Webhook from enrich-beta-applicant edge function. Triggers ICP extraction pipeline."""
    raw_content = {
        "beta_application_id": payload.beta_application_id,
        "enrichment_profile_id": payload.enrichment_profile_id,
        "company_name": payload.company_name,
        "role": payload.role,
        "enrichment_data": payload.enrichment_data,
    }

    from .graph.runner import run_pipeline

    background_tasks.add_task(run_pipeline, "beta_application", payload.beta_application_id, raw_content)
    return WebhookAccepted(source_type="beta_application", source_id=payload.beta_application_id)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


@router.get("/profiles", response_model=list[Profile])
async def list_profiles(status: str | None = None):
    """List all ICP profiles, optionally filtered by status."""
    from .graph.runner import get_db

    db = get_db()
    return await db.list_profiles(status)


@router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str):
    """Get a single profile by ID."""
    from .graph.runner import get_db

    db = get_db()
    row = await db.get_profile(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row


@router.get("/profiles/{profile_id}/detail", response_model=ProfileDetail)
async def get_profile_detail(profile_id: str, limit: int = Query(default=50, le=200)):
    """Get a profile with its signals and aggregate stats."""
    from .graph.runner import get_db

    db = get_db()
    row = await db.get_profile(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    signals = await db.list_signals_for_profile(profile_id, limit=limit)
    stats = await db.get_profile_signal_stats(profile_id)
    return {**row, "signals": signals, "signal_stats": stats}


@router.post("/profiles", response_model=Profile, status_code=201)
async def create_profile(data: ProfileCreate):
    """Create a new ICP profile."""
    from .graph.runner import get_db

    db = get_db()
    return await db.create_profile(data.model_dump())


@router.post("/profiles/{profile_id}/activate", response_model=Profile)
async def activate_profile(profile_id: str):
    """Set a profile as the active one (archives others)."""
    from .graph.runner import get_db

    db = get_db()
    row = await db.activate_profile(profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------


@router.get("/signals/review-queue", response_model=list[SignalWithContext])
async def get_review_queue(limit: int = Query(default=50, le=200)):
    """Get signals pending human review."""
    from .graph.runner import get_db

    db = get_db()
    return await db.list_review_queue(limit)


@router.get("/signals/recent", response_model=list[SignalWithContext])
async def get_recent_signals(limit: int = Query(default=50, le=200)):
    """Get recently processed signals."""
    from .graph.runner import get_db

    db = get_db()
    return await db.list_recent_signals(limit)


@router.post("/signals/{signal_id}/review", response_model=ReviewResponse)
async def review_signal_endpoint(signal_id: str, review: SignalReview):
    """Accept, reject, or reroute a signal."""
    from .graph.runner import get_db
    from .service import review_signal

    db = get_db()
    signal = await db.get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return await review_signal(
        db, signal_id, action=review.action.value,
        reviewed_by=review.reviewed_by, target_profile_id=review.target_profile_id,
    )


@router.get("/signals/similar")
async def find_similar_signals(
    text: str = Query(..., min_length=3),
    threshold: float = Query(default=0.7, ge=0, le=1),
    limit: int = Query(default=10, le=50),
):
    """Ad hoc similarity search by text."""
    from .graph.runner import get_db
    from .service import generate_embedding

    db = get_db()
    embedding = await generate_embedding(text)
    return await db.find_similar_signals(embedding, threshold, limit)


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------


@router.get("/clusters", response_model=list[Cluster])
async def list_clusters(status: str | None = None):
    """List all clusters, optionally filtered by status."""
    from .graph.runner import get_db

    db = get_db()
    return await db.list_clusters(status)


@router.get("/clusters/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(cluster_id: str):
    """Get a cluster with its member signals."""
    from .graph.runner import get_db

    db = get_db()
    cluster = await db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    signals = await db.get_cluster_signals(cluster_id)
    return {**cluster, "signals": signals}


@router.post("/clusters/{cluster_id}/promote", response_model=PromoteResponse)
async def promote_cluster_endpoint(cluster_id: str, data: ClusterPromote):
    """Promote a cluster to a new ICP profile."""
    from .graph.runner import get_db
    from .service import promote_cluster

    db = get_db()
    cluster = await db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    if cluster["status"] == "promoted":
        raise HTTPException(status_code=400, detail="Cluster already promoted")
    return await promote_cluster(db, cluster_id, data.profile_name)


@router.post("/clusters/{cluster_id}/dismiss", response_model=DismissResponse)
async def dismiss_cluster(cluster_id: str):
    """Dismiss a cluster (not a real ICP pattern)."""
    from .graph.runner import get_db

    db = get_db()
    cluster = await db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    await db.dismiss_cluster(cluster_id)
    return DismissResponse()


@router.post("/clusters/recompute", response_model=RecomputeResponse)
async def trigger_recompute(background_tasks: BackgroundTasks):
    """Trigger DBSCAN re-clustering on all outlier signals."""
    from .graph.runner import get_db
    from .service import recompute_clusters

    db = get_db()
    background_tasks.add_task(recompute_clusters, db)
    return RecomputeResponse()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Dashboard metrics for the ICP Intelligence tab."""
    from .graph.runner import get_db

    db = get_db()
    return await db.get_metrics()
