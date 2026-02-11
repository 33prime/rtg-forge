"""Contract tests for the stakeholder_enrichment module.

Verifies the module adheres to the RTG Forge Module Contract.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Module Info
# ---------------------------------------------------------------------------


def test_module_info_exports():
    """ModuleInfo is exported with all required fields."""
    from modules.stakeholder_enrichment import ModuleInfo, module_info

    assert isinstance(module_info, ModuleInfo)
    assert module_info.name == "stakeholder_enrichment"
    assert module_info.version == "1.0.0"
    assert module_info.prefix == "/api/v1/enrichment"
    assert module_info.tags == ["enrichment"]

    from fastapi import APIRouter

    assert isinstance(module_info.router, APIRouter)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def test_router_has_routes():
    """Router declares the expected endpoint paths and methods."""
    from modules.stakeholder_enrichment import module_info

    routes = {
        (route.path, tuple(route.methods))
        for route in module_info.router.routes
        if hasattr(route, "methods")
    }

    expected = {
        ("/enrich", ("POST",)),
        ("/generate-ideas", ("POST",)),
    }

    assert expected.issubset(routes), f"Missing routes. Expected {expected}, got {routes}"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_enrich_request_validates():
    """EnrichRequest requires beta_application_id."""
    from modules.stakeholder_enrichment.models import EnrichRequest

    req = EnrichRequest(beta_application_id="abc-123")
    assert req.beta_application_id == "abc-123"


def test_enrich_request_rejects_missing_id():
    """EnrichRequest rejects missing beta_application_id."""
    from pydantic import ValidationError

    from modules.stakeholder_enrichment.models import EnrichRequest

    with pytest.raises(ValidationError):
        EnrichRequest()


def test_enrich_response_defaults():
    """EnrichResponse has sensible defaults."""
    from modules.stakeholder_enrichment.models import EnrichResponse

    resp = EnrichResponse()
    assert resp.status == "accepted"
    assert resp.message == "Enrichment started"


def test_generate_ideas_request_validates():
    """GenerateIdeasRequest requires enrichment_profile_id."""
    from modules.stakeholder_enrichment.models import GenerateIdeasRequest

    req = GenerateIdeasRequest(enrichment_profile_id="xyz-456")
    assert req.enrichment_profile_id == "xyz-456"


def test_consultant_assessment_optional_fields():
    """ConsultantAssessment fields are all optional."""
    from modules.stakeholder_enrichment.models import ConsultantAssessment

    ca = ConsultantAssessment()
    assert ca.practice_maturity is None
    assert ca.key_strengths == []


def test_icp_pre_score_validates():
    """IcpPreScore validates required fields and score bounds."""
    from modules.stakeholder_enrichment.models import IcpPreScore

    score = IcpPreScore(
        overall_score=75,
        fit_category="strong_fit",
        reasoning="Good match",
    )
    assert score.overall_score == 75
    assert score.attribute_scores == {}


def test_icp_pre_score_rejects_invalid_score():
    """IcpPreScore rejects scores outside [0, 100]."""
    from pydantic import ValidationError

    from modules.stakeholder_enrichment.models import IcpPreScore

    with pytest.raises(ValidationError):
        IcpPreScore(overall_score=150, fit_category="strong_fit", reasoning="test")

    with pytest.raises(ValidationError):
        IcpPreScore(overall_score=-1, fit_category="strong_fit", reasoning="test")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_loads():
    """EnrichmentConfig can be instantiated with defaults."""
    from modules.stakeholder_enrichment.config import EnrichmentConfig

    config = EnrichmentConfig()
    assert config.synthesis_model == "claude-sonnet-4-20250514"
    assert config.use_langgraph_enrichment is False
    assert config.supabase_url == ""


def test_config_singleton():
    """get_settings returns the same instance."""
    from modules.stakeholder_enrichment.config import get_settings

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


# ---------------------------------------------------------------------------
# Service Functions Exist
# ---------------------------------------------------------------------------


def test_service_exports():
    """service.py exports the expected functions."""
    from modules.stakeholder_enrichment import service

    assert callable(service.enrich_pdl)
    assert callable(service.enrich_brightdata)
    assert callable(service.enrich_firecrawl)
    assert callable(service.synthesize_consultant)
    assert callable(service.score_icp_fit)
    assert callable(service.generate_project_ideas)
    assert callable(service.generate_psychographic_sales_intel)
    assert callable(service.run_enrichment_pipeline)
    assert callable(service.run_ideas_pipeline)
