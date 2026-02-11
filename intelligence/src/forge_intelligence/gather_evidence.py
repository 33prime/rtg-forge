"""Evidence gatherer — collect all correction data for a skill.

Produces an evidence.json file that council agents consume to debate
whether a skill should be updated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tomli

from .correction_aggregator import (
    aggregate,
    filter_by_skill,
    load_corrections,
    to_json,
)


def _load_toml(path: Path) -> dict:
    try:
        return tomli.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _find_skill(name: str, forge_root: Path) -> tuple[dict, Path] | None:
    """Find a skill by name across all category directories."""
    skills_dir = forge_root / "skills"
    if not skills_dir.is_dir():
        return None

    for category_dir in skills_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        skill_dir = category_dir / name
        toml_path = skill_dir / "meta.toml"
        if toml_path.exists():
            return _load_toml(toml_path), skill_dir
    return None


def gather_evidence(skill_name: str, forge_root: Path) -> dict:
    """Gather all evidence for a skill evolution decision.

    Returns a dict containing:
    - skill metadata (meta.toml)
    - skill content (SKILL.md)
    - all corrections triggered by this skill
    - aggregated correction statistics
    """
    # Load skill data
    skill_result = _find_skill(skill_name, forge_root)
    if skill_result is None:
        return {"error": f"Skill '{skill_name}' not found."}

    skill_data, skill_dir = skill_result
    skill_content = _read_md(skill_dir / "SKILL.md")

    # Load and filter corrections
    all_corrections = load_corrections(forge_root)
    skill_corrections = filter_by_skill(all_corrections, skill_name)
    stats = aggregate(skill_corrections)

    return {
        "skill_name": skill_name,
        "skill_metadata": skill_data,
        "skill_content": skill_content,
        "skill_path": str(skill_dir),
        "correction_count": stats.total_corrections,
        "observation_count": stats.total_observations,
        "corrections": [
            {
                "name": c.name,
                "instinct_pattern": c.instinct_pattern,
                "corrected_pattern": c.corrected_pattern,
                "impact_level": c.impact_level,
                "total_observations": c.total_observations,
                "predictability": c.predictability,
                "themes": c.themes,
                "origin": c.origin,
                "first_observed": c.first_observed,
                "last_observed": c.last_observed,
                "projects": list({o.project for o in c.observations if o.project}),
            }
            for c in stats.corrections
        ],
        "aggregated_stats": json.loads(to_json(stats)),
    }


def main() -> None:
    """CLI entry point: gather_evidence <skill-name> [forge-root] [output-path]."""
    if len(sys.argv) < 2:
        print("Usage: python -m forge_intelligence.gather_evidence <skill-name> [forge-root] [output]")
        sys.exit(1)

    skill_name = sys.argv[1]
    forge_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    evidence = gather_evidence(skill_name, forge_root)

    output = json.dumps(evidence, indent=2)
    if output_path:
        output_path.write_text(output, encoding="utf-8")
        print(f"Evidence written to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
