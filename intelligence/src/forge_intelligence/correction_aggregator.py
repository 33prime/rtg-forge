"""Correction aggregator — load, filter, and rank correction records.

Shared module used by the intelligence layer, GitHub Actions, and
CLAUDE.md generation to work with accumulated correction data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import tomli


@dataclass
class Observation:
    date: str
    project: str
    file: str


@dataclass
class Correction:
    name: str
    skill_applied: str
    instinct_pattern: str
    corrected_pattern: str
    impact_level: str
    severity: str
    total_observations: int
    first_observed: str
    last_observed: str
    observations: list[Observation]
    themes: list[str]
    origin: str
    predictability: str
    applies_to: list[str]
    description: str
    path: str


@dataclass
class AggregatedStats:
    total_corrections: int = 0
    total_observations: int = 0
    by_skill: dict[str, int] = field(default_factory=dict)
    by_theme: dict[str, int] = field(default_factory=dict)
    by_impact: dict[str, int] = field(default_factory=dict)
    by_origin: dict[str, int] = field(default_factory=dict)
    by_predictability: dict[str, int] = field(default_factory=dict)
    corrections: list[Correction] = field(default_factory=list)


def _load_toml(path: Path) -> dict:
    """Load and parse a TOML file. Returns empty dict on failure."""
    try:
        return tomli.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_corrections(forge_root: Path) -> list[Correction]:
    """Load all correction records from the decisions directory.

    Scans decisions/<category>/*/decision.toml for type="correction".
    """
    decisions_dir = forge_root / "decisions"
    if not decisions_dir.is_dir():
        return []

    corrections: list[Correction] = []

    for category_dir in sorted(decisions_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith(("_", ".")):
            continue

        for decision_dir in sorted(category_dir.iterdir()):
            toml_path = decision_dir / "decision.toml"
            if not (decision_dir.is_dir() and toml_path.exists()):
                continue

            data = _load_toml(toml_path)
            dec = data.get("decision", {})

            if dec.get("type") != "correction":
                continue

            corr = data.get("correction", {})
            freq = corr.get("frequency", {})
            classification = corr.get("classification", {})
            ctx = dec.get("context", {})

            observations = [
                Observation(
                    date=obs.get("date", ""),
                    project=obs.get("project", ""),
                    file=obs.get("file", ""),
                )
                for obs in freq.get("observations", [])
            ]

            corrections.append(
                Correction(
                    name=dec.get("name", decision_dir.name),
                    skill_applied=corr.get("skill_applied", ""),
                    instinct_pattern=corr.get("instinct_pattern", ""),
                    corrected_pattern=corr.get("corrected_pattern", ""),
                    impact_level=corr.get("impact_level", "unknown"),
                    severity=dec.get("severity", "unknown"),
                    total_observations=freq.get("total_observations", 0),
                    first_observed=freq.get("first_observed", ""),
                    last_observed=freq.get("last_observed", ""),
                    observations=observations,
                    themes=classification.get("themes", []),
                    origin=classification.get("origin", "unknown"),
                    predictability=classification.get("predictability", "unknown"),
                    applies_to=ctx.get("applies_to", []),
                    description=dec.get("description", ""),
                    path=str(decision_dir),
                )
            )

    return corrections


def filter_by_skill(corrections: list[Correction], skill_name: str) -> list[Correction]:
    """Filter corrections to those triggered by a specific skill."""
    return [c for c in corrections if c.skill_applied == skill_name]


def filter_by_tech(corrections: list[Correction], technologies: list[str]) -> list[Correction]:
    """Filter corrections to those relevant to the given technologies."""
    tech_set = {t.lower() for t in technologies}
    return [
        c for c in corrections
        if any(tag.lower() in tech_set for tag in c.applies_to)
    ]


def filter_by_min_frequency(corrections: list[Correction], min_freq: int) -> list[Correction]:
    """Filter corrections to those with at least min_freq observations."""
    return [c for c in corrections if c.total_observations >= min_freq]


def rank_by_frequency(corrections: list[Correction]) -> list[Correction]:
    """Sort corrections by observation frequency, highest first."""
    return sorted(corrections, key=lambda c: c.total_observations, reverse=True)


def aggregate(corrections: list[Correction]) -> AggregatedStats:
    """Compute aggregate statistics across a set of corrections."""
    stats = AggregatedStats()
    stats.total_corrections = len(corrections)
    stats.corrections = rank_by_frequency(corrections)

    for c in corrections:
        stats.total_observations += c.total_observations

        stats.by_skill[c.skill_applied] = (
            stats.by_skill.get(c.skill_applied, 0) + c.total_observations
        )

        for theme in c.themes:
            stats.by_theme[theme] = stats.by_theme.get(theme, 0) + c.total_observations

        stats.by_impact[c.impact_level] = (
            stats.by_impact.get(c.impact_level, 0) + c.total_observations
        )

        stats.by_origin[c.origin] = (
            stats.by_origin.get(c.origin, 0) + c.total_observations
        )

        stats.by_predictability[c.predictability] = (
            stats.by_predictability.get(c.predictability, 0) + c.total_observations
        )

    return stats


def to_json(stats: AggregatedStats) -> str:
    """Serialize aggregated stats to JSON."""
    return json.dumps(
        {
            "total_corrections": stats.total_corrections,
            "total_observations": stats.total_observations,
            "by_skill": dict(
                sorted(stats.by_skill.items(), key=lambda x: x[1], reverse=True)
            ),
            "by_theme": dict(
                sorted(stats.by_theme.items(), key=lambda x: x[1], reverse=True)
            ),
            "by_impact": stats.by_impact,
            "by_origin": stats.by_origin,
            "by_predictability": stats.by_predictability,
            "corrections": [
                {
                    "name": c.name,
                    "skill": c.skill_applied,
                    "instinct_pattern": c.instinct_pattern,
                    "corrected_pattern": c.corrected_pattern,
                    "impact_level": c.impact_level,
                    "total_observations": c.total_observations,
                    "predictability": c.predictability,
                    "themes": c.themes,
                }
                for c in stats.corrections
            ],
        },
        indent=2,
    )
