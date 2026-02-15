"""Configuration for the call intelligence module.

Extends CoreConfig from rtg_core. All settings are read from environment
variables (no prefix by default, matching the enrichment module pattern).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from rtg_core.config import CoreConfig

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).resolve().parent


class CallIntelligenceConfig(CoreConfig):
    """All settings for the call intelligence pipeline.

    Set via environment variables (uppercase).
    """

    # Recording (Recall.ai)
    recall_api_key: str = ""
    recall_webhook_secret: str = ""
    recall_region: str = "us-west-2"
    recall_bot_name: str = "Meeting Notetaker"

    # Transcription (Deepgram)
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-2"

    # Analysis
    analysis_model: str = "claude-sonnet-4-20250514"
    analysis_max_tokens: int = 16384

    # Notifications
    slack_webhook_url: str = ""

    # Dimension packs (comma-separated)
    active_packs: str = "core,sales,coaching,research"

    model_config = {"env_file": ".env", "extra": "ignore"}

    def get_active_packs(self) -> list[str]:
        return [p.strip() for p in self.active_packs.split(",") if p.strip()]

    def load_module_config(self) -> dict:
        """Load call-intelligence.config.json from the module directory."""
        config_path = MODULE_DIR / "call-intelligence.config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        logger.warning("No call-intelligence.config.json found, using defaults")
        return {}


_settings: CallIntelligenceConfig | None = None


def get_settings() -> CallIntelligenceConfig:
    """Singleton accessor for module settings."""
    global _settings
    if _settings is None:
        _settings = CallIntelligenceConfig()
    return _settings
