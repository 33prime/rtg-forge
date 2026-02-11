from rtg_core.config import CoreConfig


class EnrichmentConfig(CoreConfig):
    """Configuration for the stakeholder enrichment module.

    All settings can be overridden via environment variables with the
    ENRICHMENT_ prefix. For example, ENRICHMENT_MAX_SOURCES=10.
    """

    enrichment_max_sources: int = 5
    enrichment_cache_ttl_hours: int = 24
    enrichment_max_concurrent: int = 3

    model_config = {"env_prefix": "ENRICHMENT_", "env_file": ".env", "extra": "ignore"}
