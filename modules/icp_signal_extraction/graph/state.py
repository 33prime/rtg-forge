"""Pipeline state definition for the ICP signal extraction graph."""

from typing import TypedDict


class PipelineState(TypedDict):
    # Input
    source_type: str            # "call_transcript" | "beta_application"
    source_id: str              # UUID of the source record
    source_data: dict           # Raw data fetched from the source

    # Extraction
    extracted_signals: list[dict]

    # Embedding
    embeddings: list[list[float]]

    # Routing
    routing_results: list[dict]  # {signal_idx, profile_id, similarity, status}

    # Outliers
    outlier_indices: list[int]
    cluster_assignments: list[dict]

    # Processing metadata
    pipeline_run_id: str
    errors: list[str]
