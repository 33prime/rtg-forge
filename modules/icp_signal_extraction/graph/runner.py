"""Runner — background task entry point for the ICP signal extraction pipeline.

This is the single entry point invoked by webhook background tasks.
It creates a pipeline_run row, builds the LangGraph, and handles crashes.
"""

from __future__ import annotations

import logging

from ..config import get_settings

logger = logging.getLogger(__name__)

# Module-level DB singleton (set via on_startup or lazily)
_db = None


def get_db():
    """Return the module's database client.

    In production (rtg2026site), this is typically the asyncpg-based Database
    singleton from app.db.client. During module extraction, the host application
    is responsible for setting this via set_db().
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_db() first.")
    return _db


def set_db(db_instance):
    """Set the database client for the module. Called by the host application."""
    global _db
    _db = db_instance


async def run_pipeline(source_type: str, source_id: str, raw_content: dict) -> None:
    """Single entry point for all ICP pipeline invocations.

    Creates a pipeline_run row, builds the LangGraph, invokes it, and handles
    top-level crashes by marking the run as failed.
    """
    from uuid import UUID
    from .graph import build_pipeline

    db = get_db()
    pipeline_run_id = None

    try:
        pipeline_run_id = await db.create_pipeline_run(
            source_type, UUID(source_id) if source_id else None
        )

        graph = build_pipeline()
        result = await graph.ainvoke({
            "source_type": source_type,
            "source_id": source_id,
            "source_data": raw_content,
            "extracted_signals": [],
            "embeddings": [],
            "routing_results": [],
            "outlier_indices": [],
            "cluster_assignments": [],
            "pipeline_run_id": str(pipeline_run_id),
            "errors": [],
        })

        errors = result.get("errors", [])
        routed = len(result.get("routing_results", []))
        logger.info(
            f"ICP pipeline complete for {source_type}/{source_id}: "
            f"{routed} signals routed, {len(errors)} errors"
        )

    except Exception as e:
        logger.error(
            f"ICP pipeline crashed for {source_type}/{source_id}: {e}",
            exc_info=True,
        )
        if pipeline_run_id:
            try:
                await db.update_pipeline_run(
                    pipeline_run_id,
                    status="failed",
                    error_message=str(e),
                )
            except Exception:
                logger.error(f"Could not mark pipeline_run {pipeline_run_id} as failed")
