"""Dimension registry — the configurable analysis schema.

Each dimension defines:
  - key: unique identifier
  - pack: which preset pack it belongs to
  - instruction: what Claude should extract
  - schema: JSON schema for the expected output shape
  - output: where results go (column on call_analyses or child table)

Engineers customize by enabling/disabling packs or adding custom dimensions
in call-intelligence.config.json.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DimensionOutput:
    """Where the dimension's output is stored."""
    target: str  # table name or "call_analyses" for column
    column: str | None = None  # if storing as a column on call_analyses
    spread: bool = False  # if True, array items become rows in target table


@dataclass
class Dimension:
    key: str
    pack: str
    instruction: str
    schema: dict[str, Any]
    output: DimensionOutput
    enabled: bool = True


# ---------------------------------------------------------------------------
# Preset packs
# ---------------------------------------------------------------------------

CORE_PACK: list[Dimension] = [
    Dimension(
        key="executive_summary",
        pack="core",
        instruction=(
            "Write a 2-3 paragraph executive summary of the call. "
            "Cover what was discussed, the prospect's key concerns, and the overall tone."
        ),
        schema={"type": "string"},
        output=DimensionOutput(target="call_analyses", column="executive_summary"),
    ),
    Dimension(
        key="engagement_score",
        pack="core",
        instruction=(
            "Rate the prospect's overall engagement from 1 to 10 (integer). "
            "Consider how actively they participated, asked questions, and showed interest."
        ),
        schema={"type": "integer", "minimum": 1, "maximum": 10},
        output=DimensionOutput(target="call_analyses", column="engagement_score"),
    ),
    Dimension(
        key="talk_ratio",
        pack="core",
        instruction=(
            "Estimate the talk ratio as percentages (floats 0-1). "
            'Return {"presenter": 0.45, "prospect": 0.55} format.'
        ),
        schema={
            "type": "object",
            "properties": {
                "presenter": {"type": "number"},
                "prospect": {"type": "number"},
            },
        },
        output=DimensionOutput(target="call_analyses", column="talk_ratio"),
    ),
    Dimension(
        key="engagement_timeline",
        pack="core",
        instruction=(
            "Create a timeline of engagement levels throughout the call. "
            "Each point should have a rough timestamp, engagement level (1-10), "
            "and a brief note about what caused the change."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string"},
                    "level": {"type": "integer", "minimum": 1, "maximum": 10},
                    "note": {"type": "string"},
                },
            },
        },
        output=DimensionOutput(target="call_analyses", column="engagement_timeline"),
    ),
]

SALES_PACK: list[Dimension] = [
    Dimension(
        key="feature_insights",
        pack="sales",
        instruction=(
            "Extract every product feature or capability mentioned. For each, note:\n"
            "- feature_name: what was discussed\n"
            "- reaction: positive, negative, neutral, or confused\n"
            "- is_feature_request: true if the prospect asked for something that doesn't exist\n"
            "- is_aha_moment: true if there was a clear moment of excitement or realization\n"
            "- description: brief context\n"
            "- quote: direct quote if available\n"
            "- timestamp_start / timestamp_end: approximate timestamps if identifiable"
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "feature_name": {"type": "string"},
                    "reaction": {"enum": ["positive", "negative", "neutral", "confused"]},
                    "is_feature_request": {"type": "boolean"},
                    "is_aha_moment": {"type": "boolean"},
                    "description": {"type": "string"},
                    "quote": {"type": ["string", "null"]},
                    "timestamp_start": {"type": ["string", "null"]},
                    "timestamp_end": {"type": ["string", "null"]},
                },
            },
        },
        output=DimensionOutput(target="call_feature_insights", spread=True),
    ),
    Dimension(
        key="prospect_readiness",
        pack="sales",
        instruction=(
            "Assess the prospect's buying readiness:\n"
            "- urgency_score: 1-10 integer\n"
            "- mode: exploring, evaluating, ready_to_buy, or not_interested\n"
            "- accelerators: list of factors that could speed up the decision\n"
            "- follow_up_strategy: recommended next step in 1-2 sentences"
        ),
        schema={
            "type": "object",
            "properties": {
                "urgency_score": {"type": "integer", "minimum": 1, "maximum": 10},
                "mode": {"enum": ["exploring", "evaluating", "ready_to_buy", "not_interested"]},
                "accelerators": {"type": "array", "items": {"type": "string"}},
                "follow_up_strategy": {"type": "string"},
            },
        },
        output=DimensionOutput(target="call_analyses", column="prospect_readiness"),
    ),
]

COACHING_PACK: list[Dimension] = [
    Dimension(
        key="coaching",
        pack="coaching",
        instruction=(
            "Analyze the presenter's performance across four categories. For each item "
            "include title, description, and a quote where relevant.\n\n"
            "Categories:\n"
            "- strengths: things the presenter did well\n"
            "- improvements: areas where the presenter could improve (include suggestion)\n"
            "- missed_opportunities: moments where the presenter could have done more "
            "(include suggestion and quote)\n"
            "- objection_handling: each objection raised, whether it was handled well "
            "(boolean), and a suggestion if not"
        ),
        schema={
            "type": "object",
            "properties": {
                "talk_ratio": {
                    "type": "object",
                    "properties": {
                        "presenter": {"type": "number"},
                        "prospect": {"type": "number"},
                    },
                },
                "strengths": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "quote": {"type": ["string", "null"]},
                        },
                    },
                },
                "improvements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "suggestion": {"type": "string"},
                        },
                    },
                },
                "missed_opportunities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "suggestion": {"type": "string"},
                            "quote": {"type": ["string", "null"]},
                        },
                    },
                },
                "objection_handling": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "handled_well": {"type": "boolean"},
                            "suggestion": {"type": ["string", "null"]},
                        },
                    },
                },
            },
        },
        output=DimensionOutput(target="call_coaching_moments", spread=True),
    ),
]

RESEARCH_PACK: list[Dimension] = [
    Dimension(
        key="signals",
        pack="research",
        instruction=(
            "Extract ICP / market signals from the conversation:\n"
            "- signal_type: pain_point, goal, tool_mentioned, budget_signal, "
            "timeline, decision_process, or maturity_indicator\n"
            "- title: short label\n"
            "- description: context\n"
            "- intensity: 1-10\n"
            "- quote: direct quote if available"
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signal_type": {
                        "enum": [
                            "pain_point", "goal", "tool_mentioned",
                            "budget_signal", "timeline", "decision_process",
                            "maturity_indicator",
                        ]
                    },
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "intensity": {"type": "integer", "minimum": 1, "maximum": 10},
                    "quote": {"type": ["string", "null"]},
                },
            },
        },
        output=DimensionOutput(target="call_signals", spread=True),
    ),
    Dimension(
        key="content_nuggets",
        pack="research",
        instruction=(
            "Extract reusable content nuggets — quotes, pain framings, terminology, "
            "objections, success metrics, and industry insights that could be repurposed "
            "for marketing or sales content."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nugget_type": {
                        "enum": [
                            "quote", "pain_framing", "terminology",
                            "objection", "success_metric", "industry_insight",
                        ]
                    },
                    "content": {"type": "string"},
                    "context": {"type": "string"},
                    "industry": {"type": ["string", "null"]},
                },
            },
        },
        output=DimensionOutput(target="call_content_nuggets", spread=True),
    ),
    Dimension(
        key="competitive_intel",
        pack="research",
        instruction=(
            "Extract any mentions of competitors or alternative solutions:\n"
            "- competitor_name\n"
            "- mention_context: what was said\n"
            "- sentiment: positive, negative, or neutral toward the competitor\n"
            "- features_compared: list of features explicitly compared\n"
            "- switching_signals: indicators they might switch to/from this competitor"
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "competitor_name": {"type": "string"},
                    "mention_context": {"type": "string"},
                    "sentiment": {"enum": ["positive", "negative", "neutral"]},
                    "features_compared": {"type": "array", "items": {"type": "string"}},
                    "switching_signals": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        output=DimensionOutput(target="call_competitive_mentions", spread=True),
    ),
]

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_PACKS: dict[str, list[Dimension]] = {
    "core": CORE_PACK,
    "sales": SALES_PACK,
    "coaching": COACHING_PACK,
    "research": RESEARCH_PACK,
}


def resolve_dimensions(
    active_packs: list[str],
    custom_dimensions: list[dict] | None = None,
) -> list[Dimension]:
    """Resolve active dimensions from pack names + any custom definitions."""
    dims: list[Dimension] = []
    for pack_name in active_packs:
        pack = ALL_PACKS.get(pack_name)
        if pack:
            dims.extend(pack)
    if custom_dimensions:
        for d in custom_dimensions:
            dims.append(
                Dimension(
                    key=d["key"],
                    pack="custom",
                    instruction=d["instruction"],
                    schema=d.get("schema", {"type": "string"}),
                    output=DimensionOutput(
                        target=d.get("output", {}).get("target", "call_analyses"),
                        column=d.get("output", {}).get("column"),
                        spread=d.get("output", {}).get("spread", False),
                    ),
                )
            )
    return dims


def build_json_schema(dimensions: list[Dimension]) -> dict:
    """Build the combined JSON schema from active dimensions."""
    properties = {}
    for dim in dimensions:
        properties[dim.key] = dim.schema
    return {
        "type": "object",
        "properties": properties,
    }
