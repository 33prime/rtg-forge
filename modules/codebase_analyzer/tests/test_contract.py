"""Contract tests for the codebase_analyzer module.

Verifies the module adheres to the RTG Forge Module Contract.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Module Info
# ---------------------------------------------------------------------------


def test_module_info_exports():
    """ModuleInfo is exported with all required fields."""
    from modules.codebase_analyzer import ModuleInfo, module_info

    assert isinstance(module_info, ModuleInfo)
    assert module_info.name == "codebase_analyzer"
    assert module_info.version == "1.0.0"
    assert module_info.prefix == "/api/v1/codebase-context"
    assert module_info.tags == ["codebase-context"]

    from fastapi import APIRouter

    assert isinstance(module_info.router, APIRouter)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def test_router_has_routes():
    """Router declares the expected endpoint paths and methods."""
    from modules.codebase_analyzer import module_info

    routes = {
        (route.path, tuple(route.methods))
        for route in module_info.router.routes
        if hasattr(route, "methods")
    }

    expected = {
        ("", ("GET",)),
        ("/refresh", ("POST",)),
    }

    assert expected.issubset(routes), f"Missing routes. Expected {expected}, got {routes}"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_context_response_fields():
    """ContextResponse requires content, generated_at, status."""
    from modules.codebase_analyzer.models import ContextResponse

    resp = ContextResponse(
        content="# Context doc",
        generated_at="2026-01-01T00:00:00Z",
        status="current",
    )
    assert resp.content == "# Context doc"
    assert resp.status == "current"


def test_refresh_response_defaults():
    """RefreshResponse has sensible defaults."""
    from modules.codebase_analyzer.models import RefreshResponse

    resp = RefreshResponse()
    assert resp.status == "accepted"
    assert "refresh" in resp.message.lower() or "started" in resp.message.lower()


def test_context_response_rejects_missing_fields():
    """ContextResponse rejects missing required fields."""
    from pydantic import ValidationError

    from modules.codebase_analyzer.models import ContextResponse

    with pytest.raises(ValidationError):
        ContextResponse()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_loads():
    """CodebaseAnalyzerConfig can be instantiated with defaults."""
    from modules.codebase_analyzer.config import CodebaseAnalyzerConfig

    config = CodebaseAnalyzerConfig()
    assert config.codebase_full_analysis_model == "claude-sonnet-4-20250514"
    assert config.codebase_incremental_model == "claude-haiku-4-5-20251001"
    assert config.supabase_url == ""
    assert config.github_repo_owner == ""


def test_config_singleton():
    """get_settings returns the same instance."""
    from modules.codebase_analyzer.config import get_settings

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


# ---------------------------------------------------------------------------
# Service Functions Exist
# ---------------------------------------------------------------------------


def test_service_exports():
    """service.py exports the expected functions."""
    from modules.codebase_analyzer import service

    assert callable(service.get_current_context)
    assert callable(service.analyze_codebase_full)
    assert callable(service.analyze_codebase_incremental)
    assert callable(service.run_refresh_pipeline)
