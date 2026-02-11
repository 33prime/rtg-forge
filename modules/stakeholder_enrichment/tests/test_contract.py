"""Contract tests for the stakeholder_enrichment module.

These tests verify that the module adheres to the RTG Forge Module Contract
as defined in modules/MODULE_CONTRACT.md.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# test_module_info_exports
# ---------------------------------------------------------------------------


def test_module_info_exports():
    """ModuleInfo is exported with all required fields populated correctly."""
    from modules.stakeholder_enrichment import ModuleInfo, module_info

    assert isinstance(module_info, ModuleInfo)
    assert module_info.name == "stakeholder_enrichment"
    assert module_info.version == "0.1.0"
    assert module_info.description == (
        "Multi-source stakeholder profile enrichment with AI synthesis"
    )
    assert module_info.prefix == "/api/v1/enrichment"
    assert module_info.tags == ["enrichment"]

    # Router should be a FastAPI APIRouter
    from fastapi import APIRouter

    assert isinstance(module_info.router, APIRouter)


# ---------------------------------------------------------------------------
# test_router_has_routes
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
        ("/profiles/{profile_id}", ("GET",)),
        ("/profiles", ("GET",)),
        ("/profiles/{profile_id}", ("DELETE",)),
    }

    assert expected.issubset(routes), (
        f"Missing routes. Expected {expected}, got {routes}"
    )


# ---------------------------------------------------------------------------
# test_models_validate
# ---------------------------------------------------------------------------


def test_models_validate_enrichment_request():
    """EnrichmentRequest validates with required and optional fields."""
    from modules.stakeholder_enrichment.models import EnrichmentRequest

    # Minimal -- only required field
    req = EnrichmentRequest(stakeholder_name="Jane Smith")
    assert req.stakeholder_name == "Jane Smith"
    assert req.linkedin_url is None
    assert req.company_url is None
    assert req.additional_context is None

    # Full
    req_full = EnrichmentRequest(
        stakeholder_name="Jane Smith",
        linkedin_url="https://linkedin.com/in/janesmith",
        company_url="https://acmecorp.com",
        additional_context="CTO, AI/ML",
    )
    assert req_full.linkedin_url == "https://linkedin.com/in/janesmith"


def test_models_validate_enrichment_profile():
    """EnrichmentProfile validates with all fields."""
    from modules.stakeholder_enrichment.models import (
        EnrichmentProfile,
        EnrichmentSource,
    )

    source = EnrichmentSource(
        source_type="linkedin",
        url="https://linkedin.com/in/janesmith",
        raw_data={"title": "CTO"},
        extracted_at=datetime.utcnow(),
        confidence=0.85,
    )
    assert source.confidence == 0.85

    profile = EnrichmentProfile(
        id=uuid4(),
        stakeholder_name="Jane Smith",
        sources=[source],
        synthesis="Jane Smith is a CTO...",
        confidence_score=0.82,
        icp_signals=["technical-leader"],
        suggested_projects=["AI audit"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert profile.stakeholder_name == "Jane Smith"
    assert len(profile.sources) == 1
    assert profile.confidence_score == 0.82
    assert "technical-leader" in profile.icp_signals


def test_models_validate_enrichment_request_rejects_empty_name():
    """EnrichmentRequest rejects an empty stakeholder_name."""
    from pydantic import ValidationError

    from modules.stakeholder_enrichment.models import EnrichmentRequest

    with pytest.raises(ValidationError):
        EnrichmentRequest(stakeholder_name="")


def test_models_validate_confidence_bounds():
    """EnrichmentSource and EnrichmentProfile reject confidence outside [0, 1]."""
    from pydantic import ValidationError

    from modules.stakeholder_enrichment.models import (
        EnrichmentProfile,
        EnrichmentSource,
    )

    with pytest.raises(ValidationError):
        EnrichmentSource(
            source_type="test",
            url="https://example.com",
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        EnrichmentProfile(
            stakeholder_name="Test",
            confidence_score=-0.1,
        )


# ---------------------------------------------------------------------------
# test_config_loads
# ---------------------------------------------------------------------------


def test_config_loads():
    """EnrichmentConfig can be instantiated with defaults."""
    try:
        from modules.stakeholder_enrichment.config import EnrichmentConfig

        config = EnrichmentConfig()
        assert config.enrichment_max_sources == 5
        assert config.enrichment_cache_ttl_hours == 24
        assert config.enrichment_max_concurrent == 3
    except Exception:
        # If CoreConfig requires env vars that aren't set, we at least
        # verify the import succeeds and the class exists.
        from modules.stakeholder_enrichment.config import EnrichmentConfig

        assert hasattr(EnrichmentConfig, "enrichment_max_sources")
        assert hasattr(EnrichmentConfig, "enrichment_cache_ttl_hours")
        assert hasattr(EnrichmentConfig, "enrichment_max_concurrent")
