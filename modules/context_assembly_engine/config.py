"""Context Assembly Engine — Module configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class CAEConfig(BaseSettings):
    """Configuration for the Context Assembly Engine module."""

    cae_default_budget: int = 1800
    cae_max_memories_per_entity: int = 100
    cae_memory_decay_interval_days: int = 30
    cae_manifest_retention_days: int = 90

    # Supabase (for persistent storage when deployed)
    supabase_url: str = ""
    supabase_service_key: str = ""

    model_config = {"env_prefix": "", "case_sensitive": False}
