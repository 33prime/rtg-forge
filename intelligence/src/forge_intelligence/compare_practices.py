"""Practice comparison — compare current skill content against upstream findings.

Takes upstream check results and identifies areas where skills may be
out of date or missing new patterns from library updates.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import tomli


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


def extract_version_mentions(content: str) -> list[str]:
    """Extract version-like strings from skill content."""
    # Match patterns like: 1.2.3, >=1.0, v2.0, etc.
    pattern = r'(?:v|>=?|<=?|~=|==)?\d+\.\d+(?:\.\d+)?'
    return re.findall(pattern, content)


def compare_skill_practices(
    upstream_result: dict,
    forge_root: Path,
) -> dict:
    """Compare a skill's content against upstream findings.

    Returns:
    - version_mentions: versions found in SKILL.md
    - upstream_versions: current upstream versions
    - potentially_outdated: packages where skill mentions older version
    - recommendations: list of things to check
    """
    skill_name = upstream_result.get("skill_name", "unknown")
    skill_path = upstream_result.get("skill_path", "")

    if not skill_path:
        return {"error": f"No path for skill '{skill_name}'"}

    skill_dir = Path(skill_path)
    skill_content = _read_md(skill_dir / "SKILL.md")
    version_mentions = extract_version_mentions(skill_content)

    upstream_versions = upstream_result.get("upstream_versions", {})
    last_optimized = upstream_result.get("last_optimized", "unknown")

    recommendations: list[str] = []

    if upstream_versions and last_optimized != "unknown":
        recommendations.append(
            f"Skill was last optimized on {last_optimized}. "
            "Check if upstream changes since then affect the patterns."
        )

    for pkg, version in upstream_versions.items():
        recommendations.append(
            f"Upstream {pkg} is at version {version}. "
            "Review if new features or breaking changes affect this skill."
        )

    return {
        "skill_name": skill_name,
        "skill_path": skill_path,
        "last_optimized": last_optimized,
        "version_mentions_in_skill": version_mentions,
        "upstream_versions": upstream_versions,
        "recommendations": recommendations,
    }


def main() -> None:
    """CLI entry point: compare_practices <upstream.json> [forge-root]."""
    if len(sys.argv) < 2:
        print("Usage: python -m forge_intelligence.compare_practices <upstream.json> [forge-root]")
        sys.exit(1)

    upstream_path = Path(sys.argv[1])
    forge_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    upstream_data = json.loads(upstream_path.read_text(encoding="utf-8"))

    # Handle single skill or list
    if isinstance(upstream_data, list):
        results = [compare_skill_practices(u, forge_root) for u in upstream_data]
    else:
        results = [compare_skill_practices(upstream_data, forge_root)]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
