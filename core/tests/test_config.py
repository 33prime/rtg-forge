"""Tests for core configuration."""

from rtg_core.config import CoreConfig


def test_core_config_defaults():
    config = CoreConfig()
    assert config.supabase_url == ""
    assert config.supabase_service_key == ""
    assert config.anthropic_api_key == ""


def test_core_config_from_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-key")
    config = CoreConfig()
    assert config.supabase_url == "https://test.supabase.co"
    assert config.supabase_service_key == "test-key"
