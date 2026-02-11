"""Supabase client factory with connection management."""

from functools import lru_cache

from supabase import Client, create_client

from rtg_core.config import CoreConfig


@lru_cache(maxsize=1)
def _get_config() -> CoreConfig:
    return CoreConfig()


def get_supabase_client() -> Client:
    """Return a Supabase client instance.

    Uses lru_cache on config to avoid re-reading env vars on every call.
    The Supabase Python client handles connection pooling internally.
    """
    config = _get_config()
    if not config.supabase_url or not config.supabase_service_key:
        from rtg_core.errors import ConfigError

        raise ConfigError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(config.supabase_url, config.supabase_service_key)
