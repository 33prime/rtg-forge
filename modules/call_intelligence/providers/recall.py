"""Recall.ai provider — schedule bots and fetch recording URLs.

No SDK required. Plain HTTP via httpx.

Setup:
  1. Sign up at recall.ai
  2. Set CI_RECALL_API_KEY
  3. In Recall dashboard → Webhooks → Add your endpoint URL
  4. Set CI_RECALL_WEBHOOK_SECRET (the Svix signing secret)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re
from typing import Any

import httpx

from ..config import CallIntelligenceSettings

logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {
    "google_meet": re.compile(r"https://meet\.google\.com/"),
    "zoom": re.compile(r"https://([\w-]+\.)?zoom\.us/"),
    "teams": re.compile(r"https://teams\.(microsoft|live)\.com/"),
}


class RecallClient:
    """HTTP client for the Recall.ai REST API."""

    def __init__(self, settings: CallIntelligenceSettings) -> None:
        self.api_key = settings.recall_api_key
        self.region = settings.recall_region
        self.bot_name = settings.recall_bot_name
        self.webhook_secret = settings.recall_webhook_secret
        self.base_url = f"https://{self.region}.recall.ai"

    def is_supported_platform(self, meeting_url: str) -> bool:
        return any(p.search(meeting_url) for p in SUPPORTED_PLATFORMS.values())

    async def create_bot(self, meeting_url: str) -> dict[str, Any]:
        """Schedule a recording bot for the given meeting URL.

        Returns the Recall API response with bot id and status.
        """
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/api/v1/bot/",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "meeting_url": meeting_url,
                    "bot_name": self.bot_name,
                },
                timeout=30,
            )
        if res.status_code >= 400:
            error_text = res.text
            logger.error("Recall API error %s: %s", res.status_code, error_text)
            raise RecallError(f"Recall API returned {res.status_code}: {error_text}")
        return res.json()

    async def fetch_bot(self, bot_id: str) -> dict[str, Any]:
        """Fetch bot details including recording URLs after call ends."""
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/api/v1/bot/{bot_id}/",
                headers={"Authorization": f"Token {self.api_key}"},
                timeout=30,
            )
        if res.status_code >= 400:
            raise RecallError(f"Recall API returned {res.status_code}: {res.text}")
        return res.json()

    def extract_media_urls(self, bot_data: dict) -> dict[str, str | None]:
        """Extract video/audio download URLs from bot response.

        Handles both v1 flat structure and v2 nested media_shortcuts.
        """
        recordings = bot_data.get("recordings", [])
        if recordings:
            shortcuts = recordings[0].get("media_shortcuts", {})
            video_url = shortcuts.get("video_mixed", {}).get("data", {}).get("download_url")
            audio_url = shortcuts.get("audio_mixed", {}).get("data", {}).get("download_url")
        else:
            video_url = bot_data.get("video_url")
            audio_url = bot_data.get("audio_url")

        recording_url = video_url or audio_url
        return {
            "recording_url": recording_url,
            "video_url": video_url,
            "audio_url": audio_url,
        }

    def compute_duration(self, bot_data: dict) -> int | None:
        """Compute call duration in seconds from bot timestamps."""
        from datetime import datetime

        started = bot_data.get("started_at") or bot_data.get("join_at")
        completed = bot_data.get("completed_at") or bot_data.get("ended_at")
        if started and completed:
            try:
                s = datetime.fromisoformat(started.replace("Z", "+00:00"))
                e = datetime.fromisoformat(completed.replace("Z", "+00:00"))
                return max(0, int((e - s).total_seconds()))
            except (ValueError, TypeError):
                pass
        return bot_data.get("meeting_metadata", {}).get("duration")

    def verify_webhook(self, body: bytes, headers: dict[str, str]) -> bool:
        """Verify Svix HMAC-SHA256 webhook signature.

        Returns True if signature is valid, False otherwise.
        """
        if not self.webhook_secret:
            logger.warning("No RECALL_WEBHOOK_SECRET set — skipping verification")
            return True

        msg_id = headers.get("webhook-id", "")
        timestamp = headers.get("webhook-timestamp", "")
        signature_header = headers.get("webhook-signature", "")
        if not all([msg_id, timestamp, signature_header]):
            return False

        secret = self.webhook_secret
        if secret.startswith("whsec_"):
            secret = secret[6:]

        try:
            key_bytes = base64.b64decode(secret)
        except Exception:
            logger.error("Failed to decode webhook secret")
            return False

        signed_content = f"{msg_id}.{timestamp}.{body.decode('utf-8')}"
        computed = base64.b64encode(
            hmac.new(key_bytes, signed_content.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")

        for part in signature_header.split(" "):
            if "," in part:
                _, sig = part.split(",", 1)
                if hmac.compare_digest(sig, computed):
                    return True
        return False


class RecallError(Exception):
    pass
