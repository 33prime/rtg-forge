"""Contract tests for the icp_signal_extraction module.

Verifies the module adheres to the RTG Forge Module Contract.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Module Info
# ---------------------------------------------------------------------------


def test_module_info_exports():
    """ModuleInfo is exported with all required fields."""
    from modules.icp_signal_extraction import ModuleInfo, module_info

    assert isinstance(module_info, ModuleInfo)
    assert module_info.name == "icp_signal_extraction"
    assert module_info.version == "0.1.0"
    assert module_info.prefix == "/api/v1/icp"
    assert module_info.tags == ["icp-intelligence"]

    from fastapi import APIRouter

    assert isinstance(module_info.router, APIRouter)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def test_router_has_webhook_routes():
    """Router declares webhook endpoint paths."""
    from modules.icp_signal_extraction import module_info

    routes = {
        (route.path, tuple(route.methods))
        for route in module_info.router.routes
        if hasattr(route, "methods")
    }

    expected = {
        ("/webhooks/call-analyzed", ("POST",)),
        ("/webhooks/beta-enriched", ("POST",)),
    }
    assert expected.issubset(routes), f"Missing webhook routes. Got {routes}"


def test_router_has_profile_routes():
    """Router declares profile endpoint paths."""
    from modules.icp_signal_extraction import module_info

    paths = {route.path for route in module_info.router.routes}
    assert "/profiles" in paths
    assert "/profiles/{profile_id}" in paths
    assert "/profiles/{profile_id}/detail" in paths
    assert "/profiles/{profile_id}/activate" in paths


def test_router_has_signal_routes():
    """Router declares signal endpoint paths."""
    from modules.icp_signal_extraction import module_info

    paths = {route.path for route in module_info.router.routes}
    assert "/signals/review-queue" in paths
    assert "/signals/recent" in paths
    assert "/signals/{signal_id}/review" in paths
    assert "/signals/similar" in paths


def test_router_has_cluster_routes():
    """Router declares cluster endpoint paths."""
    from modules.icp_signal_extraction import module_info

    paths = {route.path for route in module_info.router.routes}
    assert "/clusters" in paths
    assert "/clusters/{cluster_id}" in paths
    assert "/clusters/{cluster_id}/promote" in paths
    assert "/clusters/{cluster_id}/dismiss" in paths
    assert "/clusters/recompute" in paths


def test_router_has_metrics_route():
    """Router declares metrics endpoint."""
    from modules.icp_signal_extraction import module_info

    paths = {route.path for route in module_info.router.routes}
    assert "/metrics" in paths


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_webhook_accepted_defaults():
    """WebhookAccepted has correct defaults."""
    from modules.icp_signal_extraction.models import WebhookAccepted

    resp = WebhookAccepted(source_type="call_transcript", source_id="abc")
    assert resp.status == "accepted"


def test_recompute_response_defaults():
    """RecomputeResponse has correct defaults."""
    from modules.icp_signal_extraction.models import RecomputeResponse

    resp = RecomputeResponse()
    assert resp.status == "accepted"
    assert resp.message == "Cluster recompute started"


def test_promote_response():
    """PromoteResponse validates."""
    from modules.icp_signal_extraction.models import PromoteResponse

    resp = PromoteResponse(profile_id="abc-123")
    assert resp.status == "promoted"


def test_review_response():
    """ReviewResponse validates."""
    from modules.icp_signal_extraction.models import ReviewResponse

    resp = ReviewResponse(action="accepted")
    assert resp.status == "reviewed"


def test_dismiss_response():
    """DismissResponse validates."""
    from modules.icp_signal_extraction.models import DismissResponse

    resp = DismissResponse()
    assert resp.status == "dismissed"


def test_metrics_response_defaults():
    """MetricsResponse has correct defaults."""
    from modules.icp_signal_extraction.models import MetricsResponse

    resp = MetricsResponse()
    assert resp.total_signals == 0
    assert resp.signals_by_type == {}


def test_signal_create_validation():
    """SignalCreate validates with defaults."""
    from modules.icp_signal_extraction.models import SignalCreate

    s = SignalCreate(source_type="call_transcript", signal_type="pain_point", title="Test")
    assert s.confidence == 0.5


def test_signal_create_rejects_invalid_confidence():
    """SignalCreate rejects confidence outside [0, 1]."""
    from pydantic import ValidationError
    from modules.icp_signal_extraction.models import SignalCreate

    with pytest.raises(ValidationError):
        SignalCreate(
            source_type="call_transcript",
            signal_type="pain_point",
            title="Test",
            confidence=1.5,
        )


def test_cluster_promote_model():
    """ClusterPromote validates."""
    from modules.icp_signal_extraction.models import ClusterPromote

    cp = ClusterPromote(profile_name="My ICP")
    assert cp.profile_name == "My ICP"


def test_signal_type_enum():
    """SignalType enum has expected values."""
    from modules.icp_signal_extraction.models import SignalType

    assert SignalType.PAIN_POINT.value == "pain_point"
    assert SignalType.SURPRISE.value == "surprise"


def test_routing_status_enum():
    """RoutingStatus enum has expected values."""
    from modules.icp_signal_extraction.models import RoutingStatus

    assert RoutingStatus.AUTO_ROUTED.value == "auto_routed"
    assert RoutingStatus.OUTLIER.value == "outlier"


def test_pipeline_run_status_enum():
    """PipelineRunStatus enum has expected values."""
    from modules.icp_signal_extraction.models import PipelineRunStatus

    assert PipelineRunStatus.STARTED.value == "started"
    assert PipelineRunStatus.FAILED.value == "failed"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_loads():
    """IcpSignalConfig can be instantiated with defaults."""
    from modules.icp_signal_extraction.config import IcpSignalConfig

    config = IcpSignalConfig()
    assert config.extraction_model == "claude-sonnet-4-20250514"
    assert config.embedding_model == "text-embedding-3-small"
    assert config.embedding_dimensions == 1536
    assert config.auto_route_threshold == 0.85
    assert config.review_threshold == 0.65
    assert config.min_cluster_size == 3


def test_config_singleton():
    """get_settings returns the same instance."""
    from modules.icp_signal_extraction.config import get_settings

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


# ---------------------------------------------------------------------------
# Service Functions Exist
# ---------------------------------------------------------------------------


def test_service_exports():
    """service.py exports the expected functions."""
    from modules.icp_signal_extraction import service

    assert callable(service.generate_embedding)
    assert callable(service.generate_embeddings_batch)
    assert callable(service.route_signal)
    assert callable(service.batch_route)
    assert callable(service.promote_cluster)
    assert callable(service.recompute_clusters)
    assert callable(service.review_signal)


# ---------------------------------------------------------------------------
# Graph Pipeline
# ---------------------------------------------------------------------------


def test_pipeline_builds():
    """LangGraph pipeline builds without error."""
    from modules.icp_signal_extraction.graph.graph import build_pipeline

    graph = build_pipeline()
    assert graph is not None


def test_pipeline_state_has_required_keys():
    """PipelineState TypedDict has all expected keys."""
    from modules.icp_signal_extraction.graph.state import PipelineState

    annotations = PipelineState.__annotations__
    required = [
        "source_type", "source_id", "source_data",
        "extracted_signals", "embeddings", "routing_results",
        "outlier_indices", "cluster_assignments",
        "pipeline_run_id", "errors",
    ]
    for key in required:
        assert key in annotations, f"PipelineState missing key: {key}"


def test_all_nodes_importable():
    """All graph node functions can be imported."""
    from modules.icp_signal_extraction.graph.nodes import (
        extract_signals,
        generate_embeddings,
        route_signals,
        handle_outliers,
        send_notifications,
    )

    assert all(callable(f) for f in [
        extract_signals, generate_embeddings, route_signals,
        handle_outliers, send_notifications,
    ])
