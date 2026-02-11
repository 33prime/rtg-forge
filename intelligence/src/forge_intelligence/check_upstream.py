"""Upstream checker — check PyPI versions and community patterns.

Compares current skill content against the latest library versions
and community patterns to identify skills that may need updates.
"""

from __future__ import annotations

import json
import sys
import urllib.request
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


# Map of relevance tags to PyPI package names
TAG_TO_PYPI: dict[str, str] = {
    "fastapi": "fastapi",
    "pydantic": "pydantic",
    "langgraph": "langgraph",
    "langchain": "langchain-core",
    "supabase": "supabase",
    "httpx": "httpx",
    "langfuse": "langfuse",
}

# Map of relevance tags to npm package names
TAG_TO_NPM: dict[str, str] = {
    "react": "react",
    "typescript": "typescript",
    "vite": "vite",
    "tailwind": "tailwindcss",
    "tanstack-query": "@tanstack/react-query",
}


def check_pypi_version(package: str) -> str | None:
    """Fetch the latest version of a package from PyPI."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("info", {}).get("version")
    except Exception:
        return None


def check_npm_version(package: str) -> str | None:
    """Fetch the latest version of a package from npm registry."""
    url = f"https://registry.npmjs.org/{package}/latest"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("version")
    except Exception:
        return None


def check_skill_upstream(skill_name: str, forge_root: Path) -> dict:
    """Check upstream versions for technologies in a skill's relevance tags.

    Returns a dict with:
    - skill_name
    - tags checked
    - current upstream versions found
    - any version mentions in SKILL.md
    """
    skills_dir = forge_root / "skills"
    skill_dir = None
    skill_data = {}

    if skills_dir.is_dir():
        for category_dir in skills_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            candidate = category_dir / skill_name
            if (candidate / "meta.toml").exists():
                skill_dir = candidate
                skill_data = _load_toml(candidate / "meta.toml")
                break

    if skill_dir is None:
        return {"error": f"Skill '{skill_name}' not found."}

    tags = skill_data.get("skill", {}).get("relevance_tags", [])
    skill_content = _read_md(skill_dir / "SKILL.md")

    upstream_versions: dict[str, str | None] = {}

    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in TAG_TO_PYPI:
            version = check_pypi_version(TAG_TO_PYPI[tag_lower])
            if version:
                upstream_versions[f"pypi:{TAG_TO_PYPI[tag_lower]}"] = version
        if tag_lower in TAG_TO_NPM:
            version = check_npm_version(TAG_TO_NPM[tag_lower])
            if version:
                upstream_versions[f"npm:{TAG_TO_NPM[tag_lower]}"] = version

    return {
        "skill_name": skill_name,
        "skill_path": str(skill_dir),
        "tags_checked": tags,
        "upstream_versions": upstream_versions,
        "last_optimized": skill_data.get("optimization", {}).get("last_optimized", "unknown"),
    }


def check_all_skills(forge_root: Path) -> list[dict]:
    """Check upstream for all skills in the forge."""
    skills_dir = forge_root / "skills"
    if not skills_dir.is_dir():
        return []

    results = []
    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if (skill_dir / "meta.toml").exists():
                result = check_skill_upstream(skill_dir.name, forge_root)
                if "error" not in result:
                    results.append(result)

    return results


def main() -> None:
    """CLI entry point: check_upstream [skill-name] [forge-root]."""
    forge_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        result = check_skill_upstream(sys.argv[1], forge_root)
        print(json.dumps(result, indent=2))
    else:
        results = check_all_skills(forge_root)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
