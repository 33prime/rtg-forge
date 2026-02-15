"""Deepgram provider — transcribe recordings with speaker diarization.

Uses httpx directly (no SDK dependency). Can be swapped for the
`deepgram-sdk` package if you prefer typed responses.

Setup:
  1. Sign up at deepgram.com
  2. Set CI_DEEPGRAM_API_KEY
  3. No webhook config needed — this module calls Deepgram directly
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import CallIntelligenceSettings
from ..models import Transcript, TranscriptSegment

logger = logging.getLogger(__name__)

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"


class DeepgramClient:
    """HTTP client for Deepgram pre-recorded transcription."""

    def __init__(self, settings: CallIntelligenceSettings) -> None:
        self.api_key = settings.deepgram_api_key
        self.model = settings.deepgram_model

    async def transcribe_url(self, audio_url: str) -> Transcript:
        """Transcribe audio from a URL with speaker diarization.

        Args:
            audio_url: Public URL of the audio/video file.

        Returns:
            Transcript with full text, segments, and speaker map.
        """
        params = {
            "model": self.model,
            "diarize": "true",
            "punctuate": "true",
            "utterances": "true",
            "smart_format": "true",
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(
                DEEPGRAM_API_URL,
                params=params,
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"url": audio_url},
                timeout=300,  # transcription can take a while
            )

        if res.status_code >= 400:
            error_text = res.text
            logger.error("Deepgram error %s: %s", res.status_code, error_text)
            raise DeepgramError(f"Deepgram returned {res.status_code}: {error_text}")

        data = res.json()
        return self._parse_response(data)

    def _parse_response(self, data: dict[str, Any]) -> Transcript:
        """Parse Deepgram response into our Transcript model."""
        results = data.get("results", {})
        utterances = results.get("utterances", [])
        metadata = data.get("metadata", {})

        # Build segments from utterances
        segments: list[TranscriptSegment] = []
        speaker_ids: set[str] = set()

        for utt in utterances:
            speaker = f"Speaker {utt.get('speaker', 0)}"
            speaker_ids.add(speaker)
            segments.append(
                TranscriptSegment(
                    speaker=speaker,
                    text=utt.get("transcript", ""),
                    start=utt.get("start", 0.0),
                    end=utt.get("end", 0.0),
                )
            )

        # Build speaker map (default: identity mapping)
        speaker_map = {s: s for s in sorted(speaker_ids)}

        # Full text from first channel alternative, or join utterance texts
        channels = results.get("channels", [])
        if channels:
            full_text = channels[0].get("alternatives", [{}])[0].get("transcript", "")
        else:
            full_text = " ".join(s.text for s in segments)

        word_count = len(full_text.split()) if full_text else 0
        duration = metadata.get("duration")

        return Transcript(
            full_text=full_text,
            segments=segments,
            speaker_map=speaker_map,
            word_count=word_count,
            duration_seconds=int(duration) if duration else None,
        )


class DeepgramError(Exception):
    pass
