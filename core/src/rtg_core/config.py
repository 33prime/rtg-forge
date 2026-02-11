"""Core configuration using pydantic-settings. Every module config extends this."""

from pydantic_settings import BaseSettings


class CoreConfig(BaseSettings):
    """Base configuration that all module configs extend.

    Reads from environment variables. Prefix with module name in subclasses.
    """

    supabase_url: str = ""
    supabase_service_key: str = ""
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}
