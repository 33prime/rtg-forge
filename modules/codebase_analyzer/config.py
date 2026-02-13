"""Configuration for the codebase analyzer module."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class CodebaseAnalyzerConfig(BaseSettings):
    """All settings needed by the codebase analyzer.

    Set via environment variables (uppercase, no prefix).
    """

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # AI
    anthropic_api_key: str = ""
    codebase_full_analysis_model: str = "claude-sonnet-4-20250514"
    codebase_incremental_model: str = "claude-haiku-4-5-20251001"

    # GitHub
    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: CodebaseAnalyzerConfig | None = None


def get_settings() -> CodebaseAnalyzerConfig:
    """Singleton accessor for module settings."""
    global _settings
    if _settings is None:
        _settings = CodebaseAnalyzerConfig()
    return _settings
