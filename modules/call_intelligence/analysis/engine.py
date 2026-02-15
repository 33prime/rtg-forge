"""Analysis engine — assembles prompts from dimensions, calls Claude, parses results.

This is the core of the module. It:
  1. Takes a transcript + optional context blocks + active dimensions
  2. Assembles a structured prompt from templates
  3. Calls Claude with the combined JSON schema
  4. Parses the response and returns typed results

The prompt is never hardcoded — it's composed from the active dimensions,
so engineers can add/remove analysis capabilities by editing the config.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from ..config import CallIntelligenceSettings
from ..models import (
    AnalysisResult,
    CoachingMoment,
    CompetitiveMention,
    ContentNugget,
    EngagementPoint,
    FeatureInsight,
    MomentType,
    ProspectReadiness,
    Signal,
    TalkRatio,
)
from .dimensions import Dimension, build_json_schema

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Config-driven call analysis engine powered by Claude."""

    def __init__(self, settings: CallIntelligenceSettings) -> None:
        self.api_key = settings.anthropic_api_key
        self.model = settings.analysis_model
        self.max_tokens = settings.analysis_max_tokens
        module_config = settings.load_module_config()
        analysis_cfg = module_config.get("analysis", {})
        self.system_prompt = analysis_cfg.get(
            "system_prompt",
            "You are a call analysis engine. Analyze the transcript and extract "
            "structured intelligence across the requested dimensions. "
            "Output valid JSON only. No text outside the JSON.",
        )

    async def analyze(
        self,
        transcript_text: str,
        dimensions: list[Dimension],
        context_blocks: dict[str, str] | None = None,
    ) -> tuple[AnalysisResult, dict[str, Any]]:
        """Run analysis on a transcript.

        Args:
            transcript_text: The full transcript (speaker-labeled lines).
            dimensions: Active dimensions to extract.
            context_blocks: Optional markdown context blocks, keyed by heading.
                Example: {"Contact Profile": "- Name: Jane Doe\\n- Role: CTO"}

        Returns:
            Tuple of (typed AnalysisResult, raw Claude response dict).
        """
        prompt = self._build_prompt(transcript_text, dimensions, context_blocks)
        raw = await self._call_claude(prompt)
        parsed = self._parse_response(raw)
        result = self._map_to_result(parsed, dimensions)
        return result, raw

    def _build_prompt(
        self,
        transcript_text: str,
        dimensions: list[Dimension],
        context_blocks: dict[str, str] | None = None,
    ) -> str:
        """Assemble the user prompt from context, transcript, and dimensions."""
        parts: list[str] = [
            "Analyze this call transcript and extract structured intelligence.\n"
        ]

        # Context blocks
        if context_blocks:
            for heading, content in context_blocks.items():
                parts.append(f"## {heading}\n{content}\n")

        # Transcript
        parts.append(f"## Transcript\n{transcript_text}\n")

        # Per-dimension instructions
        parts.append("## Extraction Instructions\n")
        for dim in dimensions:
            parts.append(f"### `{dim.key}`\n{dim.instruction}\n")

        # Combined JSON schema
        schema = build_json_schema(dimensions)
        parts.append(
            "## Output JSON Schema\n"
            "Respond with a single JSON object matching this schema. "
            "No text outside the JSON.\n\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n"
        )

        return "\n".join(parts)

    async def _call_claude(self, user_prompt: str) -> dict[str, Any]:
        """Call the Anthropic Messages API."""
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "system": self.system_prompt,
                },
                timeout=120,
            )

        if res.status_code >= 400:
            raise AnalysisError(f"Claude API returned {res.status_code}: {res.text}")

        return res.json()

    def _parse_response(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Extract and parse the JSON from Claude's response."""
        content = raw.get("content", [{}])
        text = content[0].get("text", "") if content else ""

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
        text = re.sub(r"\n?```\s*$", "", text.strip())

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response: %s", text[:500])
            raise AnalysisError(f"Failed to parse analysis JSON: {e}") from e

    def _map_to_result(
        self,
        parsed: dict[str, Any],
        dimensions: list[Dimension],
    ) -> AnalysisResult:
        """Map raw parsed JSON into a typed AnalysisResult."""
        result = AnalysisResult()

        # Core
        result.executive_summary = parsed.get("executive_summary", "")
        result.engagement_score = parsed.get("engagement_score", 0)

        talk = parsed.get("talk_ratio")
        if isinstance(talk, dict):
            result.talk_ratio = TalkRatio(**talk)

        timeline = parsed.get("engagement_timeline", [])
        result.engagement_timeline = [EngagementPoint(**p) for p in timeline if isinstance(p, dict)]

        # Sales
        features = parsed.get("feature_insights", [])
        result.feature_insights = [FeatureInsight(**f) for f in features if isinstance(f, dict)]

        readiness = parsed.get("prospect_readiness")
        if isinstance(readiness, dict):
            result.prospect_readiness = ProspectReadiness(**readiness)

        # Coaching — flatten sub-arrays into CoachingMoment list
        coaching = parsed.get("coaching", {})
        if isinstance(coaching, dict):
            moments: list[CoachingMoment] = []
            for item in coaching.get("strengths", []):
                if isinstance(item, dict):
                    moments.append(CoachingMoment(moment_type=MomentType.strength, **item))
            for item in coaching.get("improvements", []):
                if isinstance(item, dict):
                    moments.append(CoachingMoment(moment_type=MomentType.improvement, **item))
            for item in coaching.get("missed_opportunities", []):
                if isinstance(item, dict):
                    moments.append(CoachingMoment(moment_type=MomentType.missed_opportunity, **item))
            for item in coaching.get("objection_handling", []):
                if isinstance(item, dict):
                    handled = item.pop("handled_well", True)
                    mt = MomentType.objection_handled if handled else MomentType.objection_missed
                    moments.append(CoachingMoment(moment_type=mt, **item))
            result.coaching_moments = moments

        # Research
        signals = parsed.get("signals", [])
        result.signals = [Signal(**s) for s in signals if isinstance(s, dict)]

        nuggets = parsed.get("content_nuggets", [])
        result.content_nuggets = [ContentNugget(**n) for n in nuggets if isinstance(n, dict)]

        competitive = parsed.get("competitive_intel", [])
        result.competitive_intel = [CompetitiveMention(**c) for c in competitive if isinstance(c, dict)]

        # Custom dimensions — anything not handled above goes here
        known_keys = {
            "executive_summary", "engagement_score", "talk_ratio",
            "engagement_timeline", "feature_insights", "prospect_readiness",
            "coaching", "signals", "content_nuggets", "competitive_intel",
        }
        for key, value in parsed.items():
            if key not in known_keys:
                result.custom_dimensions[key] = value

        return result


class AnalysisError(Exception):
    pass
