"""CLAUDE.md generator — produce project-specific guidance from correction data.

Detects a project's tech stack, matches against forge corrections and skills,
and generates a CLAUDE.md file with empirically-ranked patterns.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tomli

from .correction_aggregator import (
    aggregate,
    filter_by_tech,
    load_corrections,
    rank_by_frequency,
)


def _load_toml(path: Path) -> dict:
    try:
        return tomli.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def detect_tech_stack(project_root: Path) -> list[str]:
    """Detect technologies used in a project by scanning config files."""
    technologies: list[str] = []

    # package.json
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        data = _read_json(pkg_json)
        if isinstance(data, dict):
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))

            dep_map = {
                "react": "react",
                "next": "nextjs",
                "vue": "vue",
                "typescript": "typescript",
                "vite": "vite",
                "tailwindcss": "tailwind",
                "@tanstack/react-query": "tanstack-query",
                "@supabase/supabase-js": "supabase",
                "zod": "zod",
            }

            for dep, tech in dep_map.items():
                if dep in all_deps:
                    technologies.append(tech)

    # pyproject.toml
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        data = _load_toml(pyproject)
        deps = data.get("project", {}).get("dependencies", [])
        dep_str = " ".join(deps).lower()

        py_map = {
            "fastapi": "fastapi",
            "pydantic": "pydantic",
            "langgraph": "langgraph",
            "langchain": "langchain",
            "supabase": "supabase",
            "httpx": "httpx",
            "django": "django",
            "flask": "flask",
            "langfuse": "langfuse",
        }

        for dep, tech in py_map.items():
            if dep in dep_str:
                technologies.append(tech)

        technologies.append("python")

    # requirements.txt fallback
    reqs = project_root / "requirements.txt"
    if reqs.exists() and "python" not in technologies:
        technologies.append("python")

    # tsconfig.json
    if (project_root / "tsconfig.json").exists() and "typescript" not in technologies:
        technologies.append("typescript")

    # tailwind config
    for name in ("tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs"):
        if (project_root / name).exists() and "tailwind" not in technologies:
            technologies.append("tailwind")

    # Supabase directory
    if (project_root / "supabase").is_dir() and "supabase" not in technologies:
        technologies.append("supabase")

    return technologies


def find_relevant_skills(
    technologies: list[str],
    forge_root: Path,
) -> list[dict]:
    """Find skills relevant to the detected technologies."""
    skills_dir = forge_root / "skills"
    if not skills_dir.is_dir():
        return []

    tech_set = {t.lower() for t in technologies}
    relevant: list[tuple[int, dict]] = []

    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            meta_path = skill_dir / "meta.toml"
            if not meta_path.exists():
                continue

            data = _load_toml(meta_path)
            sk = data.get("skill", {})
            tags = [t.lower() for t in sk.get("relevance_tags", [])]

            overlap = len(tech_set & set(tags))
            if overlap > 0:
                weight = sk.get("priority_weight", 0)
                relevant.append((overlap * weight, {
                    "name": sk.get("name", skill_dir.name),
                    "description": sk.get("description", ""),
                    "tier": sk.get("tier", "unknown"),
                    "category": category_dir.name,
                    "tags": tags,
                }))

    relevant.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in relevant]


def generate_claude_md(
    project_root: Path,
    forge_root: Path,
) -> str:
    """Generate CLAUDE.md content for a project.

    Detects tech stack, matches corrections and skills, produces
    ranked guidance content.
    """
    technologies = detect_tech_stack(project_root)
    corrections = load_corrections(forge_root)
    relevant_corrections = filter_by_tech(corrections, technologies)
    ranked = rank_by_frequency(relevant_corrections)
    skills = find_relevant_skills(technologies, forge_root)

    lines: list[str] = []

    # Header
    lines.append("# CLAUDE.md")
    lines.append("")

    # Project overview
    lines.append("## Project Overview")
    lines.append("")
    if technologies:
        lines.append(f"**Detected technologies:** {', '.join(technologies)}")
    else:
        lines.append("_No technologies auto-detected. Add manually._")
    lines.append("")

    # Patterns Claude Gets Wrong Here
    lines.append("## Patterns Claude Gets Wrong Here")
    lines.append("")
    if ranked:
        lines.append(
            "_Ranked by observation frequency — most common mistakes first._"
        )
        lines.append("")
        for i, c in enumerate(ranked, 1):
            lines.append(f"### {i}. {c.description or c.name}")
            lines.append("")
            lines.append(f"**Frequency:** observed {c.total_observations} time(s)")
            lines.append(f"**Impact:** {c.impact_level} | **Predictability:** {c.predictability}")
            lines.append("")
            lines.append(f"**What Claude tends to do:** {c.instinct_pattern}")
            lines.append("")
            lines.append(f"**What to do instead:** {c.corrected_pattern}")
            lines.append("")
            lines.append(f"**Skill:** `{c.skill_applied}`")
            lines.append("")
    else:
        lines.append(
            "_No corrections recorded yet for this tech stack. "
            "Use `/capture-correction` to start building empirical data._"
        )
        lines.append("")

    # Recommended Skills
    lines.append("## Recommended Skills")
    lines.append("")
    if skills:
        for s in skills[:10]:
            lines.append(f"- **{s['name']}** ({s['tier']}) — {s['description']}")
    else:
        lines.append("_No matching skills found for this tech stack._")
    lines.append("")

    # Key Conventions (from corrections themes)
    if ranked:
        all_themes: dict[str, int] = {}
        for c in ranked:
            for theme in c.themes:
                all_themes[theme] = all_themes.get(theme, 0) + c.total_observations

        if all_themes:
            lines.append("## Key Themes")
            lines.append("")
            lines.append(
                "_Recurring themes from correction data, ranked by frequency._"
            )
            lines.append("")
            for theme, count in sorted(
                all_themes.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"- **{theme}** ({count} observation(s))")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        "_Generated by RTG Forge from empirical correction data. "
        "Update with `/generate-claude-md`._"
    )

    return "\n".join(lines)


def main() -> None:
    """CLI entry point: generate_claude_md [project-root] [forge-root] [output-path]."""
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    forge_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else project_root / "CLAUDE.md"

    content = generate_claude_md(project_root, forge_root)
    output_path.write_text(content, encoding="utf-8")
    print(f"CLAUDE.md written to {output_path}")


if __name__ == "__main__":
    main()
