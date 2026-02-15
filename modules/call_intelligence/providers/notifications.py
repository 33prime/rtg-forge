"""Notification provider — Slack webhooks and generic HTTP callbacks.

Setup:
  Set CI_SLACK_WEBHOOK_URL to a Slack incoming webhook URL (optional).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def send_slack_notification(
    webhook_url: str,
    template: str,
    data: dict[str, Any],
) -> None:
    """Send a Slack notification using an incoming webhook.

    Args:
        webhook_url: Slack incoming webhook URL.
        template: Message template with {placeholders}.
        data: Values to fill placeholders.
    """
    if not webhook_url:
        return

    try:
        message = template.format_map(_SafeFormatDict(data))
        async with httpx.AsyncClient() as client:
            res = await client.post(
                webhook_url,
                json={"text": message},
                timeout=10,
            )
            if res.status_code >= 400:
                logger.warning("Slack webhook returned %s", res.status_code)
    except Exception as e:
        logger.warning("Slack notification failed: %s", e)


async def send_webhook(
    url: str,
    payload: dict[str, Any],
) -> None:
    """Fire-and-forget HTTP POST to a webhook URL.

    Used for downstream integrations (e.g. ICP pipeline triggers).
    """
    if not url:
        return

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                json=payload,
                timeout=10,
            )
            if res.status_code >= 400:
                logger.warning("Webhook %s returned %s", url, res.status_code)
    except Exception as e:
        logger.warning("Webhook to %s failed: %s", url, e)


class _SafeFormatDict(dict):
    """Dict that returns the key name for missing format placeholders."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
