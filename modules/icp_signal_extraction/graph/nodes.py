"""Graph node implementations for the ICP signal extraction pipeline.

Each node takes PipelineState and returns a partial state update.
Error accumulation is via the errors list — nodes don't raise.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

import httpx
from anthropic import AsyncAnthropic

from ..config import get_settings
from ..service import generate_embeddings_batch, route_signal
from .state import PipelineState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Extraction Prompt
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """Analyze the following {source_type} data and extract ICP (Ideal Customer Profile) signals.

For each signal, provide:
- signal_type: one of "pain_point", "goal", "trigger", "objection", "demographic", "surprise"
- title: concise signal title (1 sentence)
- description: brief elaboration
- quote: verbatim quote from the source if available (null otherwise)
- confidence: 0.0 to 1.0 indicating how clearly this signal was expressed

Source data:
{source_data}

Return a JSON array of signal objects. Only return the JSON array, no other text."""


# ---------------------------------------------------------------------------
# Node: Extract Signals
# ---------------------------------------------------------------------------


async def extract_signals(state: PipelineState) -> PipelineState:
    """Use Claude to extract structured ICP signals from source data."""
    errors = list(state.get("errors", []))
    settings = get_settings()

    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        prompt = EXTRACTION_PROMPT.format(
            source_type=state["source_type"].replace("_", " "),
            source_data=json.dumps(state["source_data"], indent=2, default=str),
        )

        message = await client.messages.create(
            model=settings.extraction_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3].strip()

        signals = json.loads(content)
        if not isinstance(signals, list):
            signals = [signals]

        return {**state, "extracted_signals": signals, "errors": errors}

    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error in extraction: {e}")
        return {**state, "extracted_signals": [], "errors": errors}
    except Exception as e:
        errors.append(f"Extraction error: {e}")
        return {**state, "extracted_signals": [], "errors": errors}


# ---------------------------------------------------------------------------
# Node: Generate Embeddings
# ---------------------------------------------------------------------------


async def generate_embeddings(state: PipelineState) -> PipelineState:
    """Batch embed all extracted signals."""
    errors = list(state.get("errors", []))
    signals = state.get("extracted_signals", [])

    if not signals:
        return {**state, "embeddings": [], "errors": errors}

    try:
        texts = []
        for sig in signals:
            parts = [f"{sig['signal_type']}: {sig['title']}"]
            if sig.get("description"):
                parts.append(sig["description"])
            if sig.get("quote"):
                parts.append(f'Quote: "{sig["quote"]}"')
            texts.append(" | ".join(parts))

        embeddings = await generate_embeddings_batch(texts)
        return {**state, "embeddings": embeddings, "errors": errors}

    except Exception as e:
        errors.append(f"Embedding error: {e}")
        return {**state, "embeddings": [], "errors": errors}


# ---------------------------------------------------------------------------
# Node: Route Signals
# ---------------------------------------------------------------------------


async def route_signals(state: PipelineState) -> PipelineState:
    """Route each signal to the best matching profile or mark as outlier."""
    errors = list(state.get("errors", []))
    signals = state.get("extracted_signals", [])
    embeddings = state.get("embeddings", [])
    pipeline_run_id = state.get("pipeline_run_id")

    if not signals or not embeddings or len(signals) != len(embeddings):
        errors.append("Mismatch between signals and embeddings count")
        return {**state, "routing_results": [], "outlier_indices": [], "errors": errors}

    from .runner import get_db
    db = get_db()

    routing_results = []
    outlier_indices = []

    for idx, (sig, emb) in enumerate(zip(signals, embeddings)):
        try:
            inserted = await db.insert_signal({
                "source_type": state["source_type"],
                "source_id": UUID(state["source_id"]) if state.get("source_id") else None,
                "source_metadata": sig.get("source_metadata", {}),
                "signal_type": sig["signal_type"],
                "title": sig["title"],
                "description": sig.get("description"),
                "quote": sig.get("quote"),
                "confidence": sig.get("confidence", 0.5),
                "pipeline_run_id": UUID(pipeline_run_id) if pipeline_run_id else None,
            })

            await db.update_signal_embedding(inserted["id"], emb)

            result = await route_signal(db, inserted["id"], emb)
            result["signal_idx"] = idx
            result["signal_id"] = str(inserted["id"])
            routing_results.append(result)

            if result["status"] == "outlier":
                outlier_indices.append(idx)

        except Exception as e:
            logger.error(f"Routing error for signal {idx}: {e}", exc_info=True)
            errors.append(f"Routing error for signal {idx}: {e}")

    if pipeline_run_id:
        auto = sum(1 for r in routing_results if r["status"] == "auto_routed")
        review = sum(1 for r in routing_results if r["status"] == "review_required")
        outlier = len(outlier_indices)
        await db.update_pipeline_run(
            UUID(pipeline_run_id),
            status="routing",
            signals_extracted=len(signals),
            signals_auto_routed=auto,
            signals_review_required=review,
            signals_outlier=outlier,
        )

    return {
        **state,
        "routing_results": routing_results,
        "outlier_indices": outlier_indices,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Node: Handle Outliers
# ---------------------------------------------------------------------------


async def handle_outliers(state: PipelineState) -> PipelineState:
    """Try to assign outlier signals to existing clusters by centroid similarity."""
    errors = list(state.get("errors", []))
    outlier_indices = state.get("outlier_indices", [])
    routing_results = state.get("routing_results", [])
    embeddings = state.get("embeddings", [])

    cluster_assignments = []

    if not outlier_indices:
        return {**state, "cluster_assignments": [], "errors": errors}

    from .runner import get_db
    db = get_db()

    for idx in outlier_indices:
        if idx >= len(embeddings):
            continue

        emb = embeddings[idx]
        signal_result = next((r for r in routing_results if r.get("signal_idx") == idx), None)
        if not signal_result:
            continue

        try:
            conn = await db.acquire()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT id, name,
                           (1 - (centroid_embedding <=> $1::vector))::FLOAT AS similarity
                    FROM icp_intelligence.clusters
                    WHERE status IN ('emerging', 'stable')
                      AND centroid_embedding IS NOT NULL
                      AND (1 - (centroid_embedding <=> $1::vector)) > 0.7
                    ORDER BY centroid_embedding <=> $1::vector
                    LIMIT 1
                    """,
                    emb,
                )

                if row:
                    from uuid import UUID
                    signal_id = UUID(signal_result["signal_id"])
                    await conn.execute(
                        """
                        INSERT INTO icp_intelligence.cluster_signals (cluster_id, signal_id, similarity_to_centroid)
                        VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
                        """,
                        row["id"],
                        signal_id,
                        row["similarity"],
                    )
                    await conn.execute(
                        "UPDATE icp_intelligence.clusters SET signal_count = signal_count + 1, updated_at = NOW() WHERE id = $1",
                        row["id"],
                    )
                    cluster_assignments.append({
                        "signal_idx": idx,
                        "cluster_id": str(row["id"]),
                        "cluster_name": row["name"],
                        "similarity": row["similarity"],
                    })
            finally:
                await db.release(conn)

        except Exception as e:
            logger.error(f"Cluster assignment error for outlier {idx}: {e}", exc_info=True)
            errors.append(f"Cluster assignment error for outlier {idx}: {e}")

    return {**state, "cluster_assignments": cluster_assignments, "errors": errors}


# ---------------------------------------------------------------------------
# Node: Notify
# ---------------------------------------------------------------------------


async def send_notifications(state: PipelineState) -> PipelineState:
    """Send Slack notification if there are signals needing review."""
    errors = list(state.get("errors", []))
    routing_results = state.get("routing_results", [])
    pipeline_run_id = state.get("pipeline_run_id")
    settings = get_settings()

    auto = sum(1 for r in routing_results if r["status"] == "auto_routed")
    review = sum(1 for r in routing_results if r["status"] == "review_required")
    outlier = sum(1 for r in routing_results if r["status"] == "outlier")
    total = len(routing_results)

    if pipeline_run_id:
        from .runner import get_db
        db = get_db()
        await db.update_pipeline_run(
            __import__("uuid").UUID(pipeline_run_id),
            status="completed",
            completed_at="NOW()",
        )

    if review > 0 or outlier > 0:
        if not settings.slack_webhook_url:
            logger.warning("Slack webhook URL not configured — skipping notification")
        else:
            try:
                message = (
                    f"*ICP Intelligence Pipeline Complete*\n"
                    f"Source: `{state['source_type']}` | ID: `{state.get('source_id', 'N/A')}`\n"
                    f"Signals: {total} total | {auto} auto-routed | {review} need review | {outlier} outliers"
                )
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        settings.slack_webhook_url,
                        json={"text": message},
                        timeout=10,
                    )
                    if resp.status_code >= 400:
                        logger.warning(f"Slack webhook returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"Slack notification failed: {e}")
                errors.append(f"Slack notification error: {e}")

    return {**state, "errors": errors}
