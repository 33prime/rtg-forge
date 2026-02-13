"""Configuration for the ICP signal extraction module.

Scoped to ICP-relevant settings: Supabase, AI providers, routing thresholds,
embedding config, and clustering parameters.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class IcpSignalConfig(BaseSettings):
    """All settings needed by the ICP signal extraction pipeline.

    Set via environment variables (uppercase, no prefix).
    """

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = ""

    # AI providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Extraction
    extraction_model: str = "claude-sonnet-4-20250514"

    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Routing thresholds (overridden by DB config at runtime)
    auto_route_threshold: float = 0.85
    review_threshold: float = 0.65
    confidence_increment_factor: float = 0.15

    # Clustering
    min_cluster_size: int = 3
    cluster_promotion_threshold: int = 5

    # Notifications
    slack_webhook_url: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: IcpSignalConfig | None = None


def get_settings() -> IcpSignalConfig:
    """Singleton accessor for module settings."""
    global _settings
    if _settings is None:
        _settings = IcpSignalConfig()
    return _settings
