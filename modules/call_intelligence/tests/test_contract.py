"""Contract tests for the Call Intelligence module.

Verify that the module adheres to the RTG Forge Module Contract:
  - ModuleInfo exported with all required fields
  - Router has expected routes
  - Models validate correctly
  - Config can be instantiated
  - Service class exists and is framework-agnostic
"""

from __future__ import annotations

import importlib
import inspect

import pytest


# ---------------------------------------------------------------------------
# 1. ModuleInfo export
# ---------------------------------------------------------------------------


def test_module_exports_module_info():
    mod = importlib.import_module("modules.call_intelligence")
    assert hasattr(mod, "module_info"), "Module must export module_info"


def test_module_info_fields():
    from modules.call_intelligence import module_info

    assert module_info.name == "call_intelligence"
    assert module_info.version
    assert module_info.description
    assert module_info.router is not None
    assert module_info.prefix.startswith("/api/")
    assert isinstance(module_info.tags, list) and len(module_info.tags) > 0


# ---------------------------------------------------------------------------
# 2. Router routes
# ---------------------------------------------------------------------------


def test_router_has_expected_routes():
    from modules.call_intelligence.router import router

    paths = {r.path for r in router.routes if hasattr(r, "path")}
    assert "/recordings/schedule" in paths
    assert "/webhooks/recall" in paths
    assert "/recordings" in paths
    assert "/recordings/{recording_id}" in paths
    assert "/recordings/{recording_id}/details" in paths
    assert "/recordings/{recording_id}/analyze" in paths


def test_router_methods():
    from modules.call_intelligence.router import router

    method_map = {}
    for route in router.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            method_map[route.path] = route.methods

    assert "POST" in method_map.get("/recordings/schedule", set())
    assert "POST" in method_map.get("/webhooks/recall", set())
    assert "GET" in method_map.get("/recordings", set())
    assert "GET" in method_map.get("/recordings/{recording_id}", set())
    assert "GET" in method_map.get("/recordings/{recording_id}/details", set())
    assert "POST" in method_map.get("/recordings/{recording_id}/analyze", set())


# ---------------------------------------------------------------------------
# 3. Models validate
# ---------------------------------------------------------------------------


def test_schedule_recording_request():
    from modules.call_intelligence.models import ScheduleRecordingRequest

    req = ScheduleRecordingRequest(meeting_url="https://meet.google.com/abc-def-ghi")
    assert req.meeting_url == "https://meet.google.com/abc-def-ghi"
    assert req.contact_name is None


def test_schedule_recording_response():
    from modules.call_intelligence.models import (
        RecordingStatus,
        ScheduleRecordingResponse,
    )

    resp = ScheduleRecordingResponse(
        success=True,
        recording_id="12345678-1234-1234-1234-123456789abc",
        status=RecordingStatus.bot_scheduled,
    )
    assert resp.success is True
    assert resp.status == RecordingStatus.bot_scheduled


def test_recording_status_enum():
    from modules.call_intelligence.models import RecordingStatus

    assert RecordingStatus.pending.value == "pending"
    assert RecordingStatus.complete.value == "complete"
    assert RecordingStatus.failed.value == "failed"
    assert len(RecordingStatus) == 8


def test_analysis_result_defaults():
    from modules.call_intelligence.models import AnalysisResult

    result = AnalysisResult()
    assert result.engagement_score == 0
    assert result.executive_summary == ""
    assert result.feature_insights == []
    assert result.signals == []
    assert result.coaching_moments == []


def test_webhook_payload_bot_id_extraction():
    from modules.call_intelligence.models import RecallWebhookPayload

    payload = RecallWebhookPayload(
        event="bot.done",
        data={"bot": {"id": "bot-123"}},
    )
    assert payload.get_bot_id() == "bot-123"
    assert payload.get_event() == "bot.done"


def test_webhook_payload_fallback_bot_id():
    from modules.call_intelligence.models import RecallWebhookPayload

    payload = RecallWebhookPayload(data={"bot_id": "bot-456"})
    assert payload.get_bot_id() == "bot-456"


def test_analyze_response():
    from modules.call_intelligence.models import AnalyzeResponse

    resp = AnalyzeResponse(success=True, engagement_score=8, tokens_used=1500)
    assert resp.success is True
    assert resp.dimensions_processed == []


# ---------------------------------------------------------------------------
# 4. Config
# ---------------------------------------------------------------------------


def test_config_instantiates():
    from modules.call_intelligence.config import CallIntelligenceConfig

    config = CallIntelligenceConfig()
    assert config.recall_api_key == ""
    assert config.deepgram_api_key == ""
    assert config.analysis_model == "claude-sonnet-4-20250514"


def test_config_get_active_packs():
    from modules.call_intelligence.config import CallIntelligenceConfig

    config = CallIntelligenceConfig(active_packs="core,sales")
    assert config.get_active_packs() == ["core", "sales"]


def test_config_extends_core():
    from rtg_core.config import CoreConfig

    from modules.call_intelligence.config import CallIntelligenceConfig

    assert issubclass(CallIntelligenceConfig, CoreConfig)


# ---------------------------------------------------------------------------
# 5. Service is framework-agnostic
# ---------------------------------------------------------------------------


def test_service_no_fastapi_imports():
    """service.py must not import from fastapi."""
    source = inspect.getsource(
        importlib.import_module("modules.call_intelligence.service")
    )
    assert "from fastapi" not in source
    assert "import fastapi" not in source


def test_service_class_exists():
    from modules.call_intelligence.service import CallIntelligenceService

    assert callable(CallIntelligenceService)


# ---------------------------------------------------------------------------
# 6. Analysis dimensions
# ---------------------------------------------------------------------------


def test_dimension_packs_exist():
    from modules.call_intelligence.analysis.dimensions import (
        COACHING_PACK,
        CORE_PACK,
        RESEARCH_PACK,
        SALES_PACK,
    )

    assert len(CORE_PACK) > 0
    assert len(SALES_PACK) > 0
    assert len(COACHING_PACK) > 0
    assert len(RESEARCH_PACK) > 0


def test_resolve_dimensions():
    from modules.call_intelligence.analysis.dimensions import resolve_dimensions

    dims = resolve_dimensions(["core", "sales"], None)
    keys = [d.key for d in dims]
    assert "executive_summary" in keys
    assert "feature_insights" in keys
