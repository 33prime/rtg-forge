"""Configuration for the stakeholder enrichment module.

Mirrors the production config from icp-service/app/config.py, scoped
to enrichment-relevant settings only.
"""

from __future__ import annotations

import json

from pydantic_settings import BaseSettings


def _parse_origins(raw: str) -> list[str]:
    """Parse CORS origins from env var — handles JSON arrays and comma-separated strings."""
    if not raw:
        return ["http://localhost:3000", "http://localhost:3001"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    raw = raw.strip("[]")
    return [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]


class EnrichmentConfig(BaseSettings):
    """All settings needed by the enrichment pipeline.

    Set via environment variables (uppercase, no prefix).
    """

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # AI
    anthropic_api_key: str = ""
    synthesis_model: str = "claude-sonnet-4-20250514"

    # Enrichment providers
    pdl_api_key: str = ""
    brightdata_api_key: str = ""
    firecrawl_api_key: str = ""

    # Feature flags
    use_langgraph_enrichment: bool = False

    # Server
    cors_origins: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_cors_origins(self) -> list[str]:
        return _parse_origins(self.cors_origins)


_settings: EnrichmentConfig | None = None


def get_settings() -> EnrichmentConfig:
    """Singleton accessor for module settings."""
    global _settings
    if _settings is None:
        _settings = EnrichmentConfig()
    return _settings
