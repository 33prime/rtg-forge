"""Business logic for the ICP signal extraction module.

Contains:
  - Signal routing: route_signal, batch_route
  - Cluster operations: promote_cluster, recompute_clusters
  - Signal review: review_signal
  - Embedding: generate_embedding, generate_embeddings_batch

Source file mapping from production codebase:
  - icp-service/app/services/routing.py     -> route_signal, batch_route
  - icp-service/app/services/clustering.py  -> recompute_clusters
  - icp-service/app/services/icp_signals.py -> promote_cluster, review_signal
  - icp-service/app/services/embedding.py   -> generate_embedding, generate_embeddings_batch

NO FastAPI imports. Framework-agnostic.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

import httpx
import numpy as np
from openai import AsyncOpenAI
from sklearn.cluster import DBSCAN

from .config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------


def _supabase_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _supabase_base() -> str:
    return get_settings().supabase_url + "/rest/v1"


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


async def generate_embedding(text: str) -> list[float]:
    """Generate a single embedding using OpenAI text-embedding-3-small."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        input=[text],
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    if not texts:
        return []
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        input=texts,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


# ---------------------------------------------------------------------------
# Signal Routing
# ---------------------------------------------------------------------------


async def route_signal(
    db,
    signal_id: UUID,
    embedding: list[float],
) -> dict:
    """Route a single signal to the best matching profile based on cosine similarity.

    Args:
        db: Database client instance
        signal_id: UUID of the signal to route
        embedding: Signal embedding vector

    Returns:
        dict with keys: status, profile_id, profile_name, similarity
    """
    settings = get_settings()
    match = await db.match_profile(embedding, threshold=settings.review_threshold)

    if match is None:
        await db.update_signal_routing(signal_id, None, None, "outlier")
        return {"status": "outlier", "profile_id": None, "profile_name": None, "similarity": None}

    similarity = match["similarity"]
    profile_id = match["profile_id"]
    profile_name = match["profile_name"]

    if similarity >= settings.auto_route_threshold:
        await db.update_signal_routing(signal_id, profile_id, similarity, "auto_routed")
        # Boost profile confidence asymptotically
        profile = await db.get_profile(profile_id)
        if profile:
            old_conf = float(profile["confidence"])
            new_conf = old_conf + (1 - old_conf) * settings.confidence_increment_factor
            conn = await db.acquire()
            try:
                await conn.execute(
                    """
                    UPDATE icp_intelligence.profiles
                    SET confidence = $1, signal_count = signal_count + 1, updated_at = NOW()
                    WHERE id = $2
                    """,
                    new_conf,
                    profile_id,
                )
            finally:
                await db.release(conn)
        return {
            "status": "auto_routed",
            "profile_id": profile_id,
            "profile_name": profile_name,
            "similarity": similarity,
        }
    else:
        await db.update_signal_routing(signal_id, profile_id, similarity, "review_required")
        return {
            "status": "review_required",
            "profile_id": profile_id,
            "profile_name": profile_name,
            "similarity": similarity,
        }


async def batch_route(db, signal_ids: list[UUID], embeddings: list[list[float]]) -> list[dict]:
    """Route multiple signals."""
    results = []
    for sid, emb in zip(signal_ids, embeddings):
        result = await route_signal(db, sid, emb)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Cluster Operations
# ---------------------------------------------------------------------------


async def promote_cluster(db, cluster_id: UUID, profile_name: str) -> dict:
    """Promote a cluster to a new ICP profile.

    Creates a profile from the cluster's signal types, updates cluster status,
    and re-routes member signals to the new profile.

    Args:
        db: Database client instance
        cluster_id: UUID of the cluster to promote
        profile_name: Name for the new profile

    Returns:
        dict with status and profile_id
    """
    signals = await db.get_cluster_signals(cluster_id)
    pain_points = [s["title"] for s in signals if s["signal_type"] == "pain_point"]
    goals = [s["title"] for s in signals if s["signal_type"] == "goal"]
    triggers = [s["title"] for s in signals if s["signal_type"] == "trigger"]
    objections = [s["title"] for s in signals if s["signal_type"] == "objection"]

    profile = await db.create_profile({
        "name": profile_name,
        "pain_points": pain_points,
        "goals": goals,
        "triggers": triggers,
        "objections": objections,
    })

    conn = await db.acquire()
    try:
        await conn.execute(
            """
            UPDATE icp_intelligence.clusters
            SET status = 'promoted', promoted_to_profile_id = $1, updated_at = NOW()
            WHERE id = $2
            """,
            profile["id"],
            cluster_id,
        )
        await conn.execute(
            """
            UPDATE icp_intelligence.signals
            SET routed_to_profile_id = $1, routing_status = 'auto_routed', updated_at = NOW()
            WHERE id IN (SELECT signal_id FROM icp_intelligence.cluster_signals WHERE cluster_id = $2)
            """,
            profile["id"],
            cluster_id,
        )
    finally:
        await db.release(conn)

    return {"status": "promoted", "profile_id": str(profile["id"])}


async def recompute_clusters(db) -> dict:
    """Run DBSCAN on all unassigned outlier signals to detect emerging clusters.

    Scans signals with routing_status='outlier' not in any cluster, groups them
    by embedding similarity, and creates new clusters.

    Args:
        db: Database client instance

    Returns:
        dict with new_clusters, signals_clustered, total_outliers, unclustered
    """
    settings = get_settings()
    conn = await db.acquire()
    try:
        rows = await conn.fetch(
            """
            SELECT s.id, s.signal_embedding
            FROM icp_intelligence.signals s
            WHERE s.routing_status = 'outlier'
              AND s.signal_embedding IS NOT NULL
              AND s.id NOT IN (SELECT signal_id FROM icp_intelligence.cluster_signals)
            ORDER BY s.created_at DESC
            """
        )

        if len(rows) < settings.min_cluster_size:
            return {"new_clusters": 0, "signals_clustered": 0, "message": "Not enough outliers"}

        signal_ids = [r["id"] for r in rows]
        embeddings = np.array([list(r["signal_embedding"]) for r in rows])

        clustering = DBSCAN(eps=0.3, min_samples=settings.min_cluster_size, metric="cosine")
        labels = clustering.fit_predict(embeddings)

        new_clusters = 0
        signals_clustered = 0

        unique_labels = set(labels)
        unique_labels.discard(-1)

        for label in unique_labels:
            member_indices = [i for i, l in enumerate(labels) if l == label]
            member_ids = [signal_ids[i] for i in member_indices]
            member_embeddings = embeddings[member_indices]

            centroid = member_embeddings.mean(axis=0).tolist()

            cluster_row = await conn.fetchrow(
                """
                INSERT INTO icp_intelligence.clusters (name, centroid_embedding, signal_count, status)
                VALUES ($1, $2, $3, 'emerging')
                RETURNING id
                """,
                f"Emerging Cluster #{new_clusters + 1}",
                centroid,
                len(member_ids),
            )

            for i, sid in zip(member_indices, member_ids):
                sim = float(1 - np.linalg.norm(embeddings[i] - np.array(centroid)))
                await conn.execute(
                    """
                    INSERT INTO icp_intelligence.cluster_signals (cluster_id, signal_id, similarity_to_centroid)
                    VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
                    """,
                    cluster_row["id"],
                    sid,
                    max(0, min(1, sim)),
                )

            new_clusters += 1
            signals_clustered += len(member_ids)

        return {
            "new_clusters": new_clusters,
            "signals_clustered": signals_clustered,
            "total_outliers": len(signal_ids),
            "unclustered": sum(1 for l in labels if l == -1),
        }

    finally:
        await db.release(conn)


# ---------------------------------------------------------------------------
# Signal Review
# ---------------------------------------------------------------------------


async def review_signal(
    db,
    signal_id: UUID,
    action: str,
    reviewed_by: str,
    target_profile_id: UUID | None = None,
) -> dict:
    """Accept, reject, or reroute a signal.

    Args:
        db: Database client instance
        signal_id: UUID of the signal
        action: One of accepted, rejected, rerouted, new_cluster
        reviewed_by: Identifier of the reviewer
        target_profile_id: Optional profile to reroute to

    Returns:
        dict with status and action
    """
    await db.review_signal(
        signal_id,
        action=action,
        reviewed_by=reviewed_by,
        target_profile_id=target_profile_id,
    )
    return {"status": "reviewed", "action": action}
