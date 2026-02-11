"""RTG Forge MCP Server — AI interface to modules, skills, and profiles.

Provides tools, resources, and prompts for browsing and managing
the RTG Forge module/skill/profile ecosystem.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import tomli
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("rtg-forge")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_forge_root() -> Path:
    """Return the forge root directory.

    Resolution order:
    1. FORGE_ROOT environment variable
    2. Walk up from CWD looking for forge.toml
    """
    env_root = os.environ.get("FORGE_ROOT")
    if env_root:
        return Path(env_root)

    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "forge.toml").exists():
            return parent
    # Fallback: assume CWD
    return current


def _load_toml(path: Path) -> dict:
    """Load and parse a TOML file. Returns empty dict on failure."""
    try:
        return tomli.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_md(path: Path) -> str:
    """Read a Markdown file. Returns empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Scanners — return lists of parsed data
# ---------------------------------------------------------------------------


def _scan_modules(root: Path | None = None) -> list[dict]:
    """Scan modules/*/module.toml and return parsed module metadata."""
    root = root or _get_forge_root()
    modules_dir = root / "modules"
    if not modules_dir.is_dir():
        return []

    results: list[dict] = []
    for mod_dir in sorted(modules_dir.iterdir()):
        toml_path = mod_dir / "module.toml"
        if mod_dir.is_dir() and toml_path.exists():
            data = _load_toml(toml_path)
            data["_path"] = str(mod_dir)
            data["_name"] = mod_dir.name
            results.append(data)
    return results


def _scan_skills(root: Path | None = None) -> list[dict]:
    """Scan skills/<category>/*/meta.toml and return parsed skill metadata."""
    root = root or _get_forge_root()
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []

    results: list[dict] = []
    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        # Skip contract files
        if category_dir.is_file():
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            toml_path = skill_dir / "meta.toml"
            if skill_dir.is_dir() and toml_path.exists():
                data = _load_toml(toml_path)
                data["_path"] = str(skill_dir)
                data["_name"] = skill_dir.name
                data["_category_dir"] = category_dir.name
                results.append(data)
    return results


def _scan_profiles(root: Path | None = None) -> list[dict]:
    """Scan profiles/*/profile.toml and return parsed profile metadata."""
    root = root or _get_forge_root()
    profiles_dir = root / "profiles"
    if not profiles_dir.is_dir():
        return []

    results: list[dict] = []
    for prof_dir in sorted(profiles_dir.iterdir()):
        toml_path = prof_dir / "profile.toml"
        if prof_dir.is_dir() and toml_path.exists() and not prof_dir.name.startswith("_"):
            data = _load_toml(toml_path)
            data["_path"] = str(prof_dir)
            data["_name"] = prof_dir.name
            results.append(data)
    return results


def _find_module(name: str, root: Path | None = None) -> tuple[dict, Path] | None:
    """Find a module by name. Returns (toml_data, module_dir) or None."""
    root = root or _get_forge_root()
    mod_dir = root / "modules" / name
    toml_path = mod_dir / "module.toml"
    if toml_path.exists():
        return _load_toml(toml_path), mod_dir
    return None


def _find_skill(name: str, root: Path | None = None) -> tuple[dict, Path] | None:
    """Find a skill by name across all category directories."""
    root = root or _get_forge_root()
    skills_dir = root / "skills"
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


def _find_profile(name: str, root: Path | None = None) -> tuple[dict, Path] | None:
    """Find a profile by name. Returns (toml_data, profile_dir) or None."""
    root = root or _get_forge_root()
    prof_dir = root / "profiles" / name
    toml_path = prof_dir / "profile.toml"
    if toml_path.exists():
        return _load_toml(toml_path), prof_dir
    return None


def _keyword_score(text: str, query_words: list[str]) -> int:
    """Count how many query words appear in text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for w in query_words if w in text_lower)


# ---------------------------------------------------------------------------
# TOOLS — Module tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_modules(profile: str = "rtg-default", category: str = "") -> str:
    """List all forge modules with name, description, status, and category.

    Args:
        profile: Profile context (for future filtering).
        category: Filter by category (e.g. "enrichment"). Empty = all.
    """
    modules = _scan_modules()

    if category:
        modules = [
            m for m in modules
            if m.get("module", {}).get("category", "") == category
        ]

    if not modules:
        return "No modules found."

    lines = ["# Forge Modules\n"]
    for m in modules:
        mod = m.get("module", {})
        name = mod.get("name", m["_name"])
        desc = mod.get("description", "No description")
        status = mod.get("status", "unknown")
        cat = mod.get("category", "uncategorized")
        lines.append(f"- **{name}** (`{status}`) [{cat}] — {desc}")

    return "\n".join(lines)


@mcp.tool()
def get_module(name: str, profile: str = "rtg-default") -> str:
    """Get full details for a module: MODULE.md content + module.toml metadata.

    Args:
        name: Module directory name (e.g. "stakeholder_enrichment").
        profile: Profile context.
    """
    result = _find_module(name)
    if result is None:
        return f"Module '{name}' not found."

    data, mod_dir = result
    mod = data.get("module", {})

    lines = [f"# Module: {mod.get('name', name)}\n"]
    lines.append(f"- **Version:** {mod.get('version', 'unknown')}")
    lines.append(f"- **Status:** {mod.get('status', 'unknown')}")
    lines.append(f"- **Category:** {mod.get('category', 'uncategorized')}")
    lines.append(f"- **Description:** {mod.get('description', 'N/A')}")

    deps = mod.get("dependencies", {})
    if deps:
        lines.append("\n## Dependencies")
        if deps.get("python"):
            lines.append(f"- Python: {', '.join(deps['python'])}")
        if deps.get("services"):
            lines.append(f"- Services: {', '.join(deps['services'])}")
        if deps.get("modules"):
            lines.append(f"- Modules: {', '.join(deps['modules'])}")

    ai = data.get("ai", {})
    if ai:
        lines.append("\n## AI Metadata")
        lines.append(f"- **Use when:** {ai.get('use_when', 'N/A')}")
        lines.append(f"- **Input:** {ai.get('input_summary', 'N/A')}")
        lines.append(f"- **Output:** {ai.get('output_summary', 'N/A')}")
        lines.append(f"- **Complexity:** {ai.get('complexity', 'N/A')}")
        lines.append(f"- **Setup time:** ~{ai.get('estimated_setup_minutes', '?')} min")

    # Append MODULE.md content
    md_content = _read_md(mod_dir / "MODULE.md")
    if md_content:
        lines.append("\n---\n")
        lines.append(md_content)

    return "\n".join(lines)


@mcp.tool()
def search_modules(query: str, profile: str = "rtg-default") -> str:
    """Search modules by matching query against AI metadata, name, and description.

    Args:
        query: Search query (keywords).
        profile: Profile context.
    """
    query_words = [w.lower() for w in query.split() if w]
    if not query_words:
        return "Please provide a search query."

    modules = _scan_modules()
    scored: list[tuple[int, dict]] = []

    for m in modules:
        mod = m.get("module", {})
        ai = m.get("ai", {})

        searchable = " ".join([
            mod.get("name", ""),
            mod.get("description", ""),
            ai.get("use_when", ""),
            ai.get("input_summary", ""),
            ai.get("output_summary", ""),
        ])

        score = _keyword_score(searchable, query_words)
        if score > 0:
            scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return f"No modules matched query: '{query}'"

    lines = [f"# Search Results for '{query}'\n"]
    for score, m in scored:
        mod = m.get("module", {})
        name = mod.get("name", m["_name"])
        desc = mod.get("description", "No description")
        lines.append(f"- **{name}** (relevance: {score}) — {desc}")

    return "\n".join(lines)


@mcp.tool()
def get_module_setup(name: str, profile: str = "rtg-default") -> str:
    """Get setup instructions for a module: Setup section from MODULE.md + required env vars.

    Args:
        name: Module directory name.
        profile: Profile context.
    """
    result = _find_module(name)
    if result is None:
        return f"Module '{name}' not found."

    data, mod_dir = result
    mod = data.get("module", {})

    lines = [f"# Setup: {mod.get('name', name)}\n"]

    # Extract dependencies info
    deps = mod.get("dependencies", {})
    if deps.get("services"):
        lines.append("## Required Services")
        for svc in deps["services"]:
            lines.append(f"- {svc}")
        lines.append("")

    if deps.get("python"):
        lines.append("## Python Dependencies")
        for pkg in deps["python"]:
            lines.append(f"- {pkg}")
        lines.append("")

    # Extract Setup section from MODULE.md
    md_content = _read_md(mod_dir / "MODULE.md")
    if md_content:
        # Try to extract just the Setup section
        in_setup = False
        setup_lines: list[str] = []
        for line in md_content.splitlines():
            if line.strip().lower().startswith("## setup") or line.strip().lower().startswith("# setup"):
                in_setup = True
                setup_lines.append(line)
                continue
            if in_setup:
                # Stop at the next heading of same or higher level
                if line.startswith("## ") or line.startswith("# "):
                    break
                setup_lines.append(line)

        if setup_lines:
            lines.append("\n".join(setup_lines))
        else:
            lines.append("_No Setup section found in MODULE.md._")

    return "\n".join(lines)


@mcp.tool()
def validate_module(name: str) -> str:
    """Validate a module has all required contract files.

    Args:
        name: Module directory name.
    """
    root = _get_forge_root()
    mod_dir = root / "modules" / name

    if not mod_dir.is_dir():
        return f"Module directory '{name}' does not exist."

    required_files = [
        "module.toml",
        "MODULE.md",
        "__init__.py",
        "router.py",
        "service.py",
        "models.py",
        "config.py",
    ]
    required_dirs = [
        "migrations/",
        "tests/",
    ]

    results: list[dict] = []
    all_pass = True

    for fname in required_files:
        exists = (mod_dir / fname).is_file()
        results.append({"file": fname, "status": "pass" if exists else "FAIL"})
        if not exists:
            all_pass = False

    for dname in required_dirs:
        clean_name = dname.rstrip("/")
        exists = (mod_dir / clean_name).is_dir()
        results.append({"file": dname, "status": "pass" if exists else "FAIL"})
        if not exists:
            all_pass = False

    lines = [f"# Validation: {name}\n"]
    lines.append(f"**Overall:** {'PASS' if all_pass else 'FAIL'}\n")

    for r in results:
        icon = "pass" if r["status"] == "pass" else "FAIL"
        lines.append(f"- [{icon}] `{r['file']}`")

    return "\n".join(lines)


@mcp.tool()
def scaffold_module(name: str, category: str = "enrichment") -> str:
    """Return instructions and template for creating a new forge module.

    Does not create files — provides the blueprint for the CLI or human to execute.

    Args:
        name: Desired module name (snake_case).
        category: Module category.
    """
    files = [
        f"modules/{name}/module.toml",
        f"modules/{name}/MODULE.md",
        f"modules/{name}/__init__.py",
        f"modules/{name}/router.py",
        f"modules/{name}/service.py",
        f"modules/{name}/models.py",
        f"modules/{name}/config.py",
        f"modules/{name}/migrations/.gitkeep",
        f"modules/{name}/tests/__init__.py",
        f"modules/{name}/tests/test_contract.py",
        f"modules/{name}/pyproject.toml",
    ]

    toml_template = f'''[module]
name = "{name}"
version = "0.1.0"
description = ""
status = "draft"
category = "{category}"
author = "RTG"

[module.dependencies]
python = []
services = []
modules = []

[module.api]
prefix = "/api/v1/{name}"
auth_required = true

[module.database]
tables = []
requires_rls = true

[ai]
use_when = ""
input_summary = ""
output_summary = ""
complexity = "medium"
estimated_setup_minutes = 15
related_modules = []

[health]
last_validated = ""
test_coverage = 0
known_issues = []'''

    lines = [f"# Scaffold Module: {name}\n"]
    lines.append(f"**Category:** {category}\n")
    lines.append("## Required Files\n")
    for f in files:
        lines.append(f"- `{f}`")
    lines.append("\n## module.toml Template\n")
    lines.append(f"```toml\n{toml_template}\n```")
    lines.append("\n## Next Steps\n")
    lines.append("1. Create the directory structure above")
    lines.append("2. Fill in module.toml with actual description and dependencies")
    lines.append("3. Implement service.py with core business logic")
    lines.append("4. Implement router.py with FastAPI endpoints")
    lines.append("5. Define models.py with Pydantic schemas")
    lines.append("6. Write MODULE.md documentation")
    lines.append("7. Run `validate_module` to check completeness")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TOOLS — Skill tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_skills(profile: str = "rtg-default", tier: str = "") -> str:
    """List all forge skills with name, tier, category, priority_weight, and description.

    Args:
        profile: Profile context.
        tier: Filter by tier (e.g. "foundation", "applied"). Empty = all.
    """
    skills = _scan_skills()

    if tier:
        skills = [
            s for s in skills
            if s.get("skill", {}).get("tier", "") == tier
        ]

    if not skills:
        return "No skills found."

    lines = ["# Forge Skills\n"]
    for s in skills:
        sk = s.get("skill", {})
        name = sk.get("name", s["_name"])
        sk_tier = sk.get("tier", "unknown")
        cat = sk.get("category", s.get("_category_dir", "uncategorized"))
        weight = sk.get("priority_weight", 0)
        desc = sk.get("description", "No description")
        lines.append(f"- **{name}** (tier: {sk_tier}, weight: {weight}) [{cat}] — {desc}")

    return "\n".join(lines)


@mcp.tool()
def get_skill(name: str, profile: str = "rtg-default") -> str:
    """Get full details for a skill: SKILL.md content + meta.toml metadata.

    Args:
        name: Skill directory name (e.g. "python-clean-architecture").
        profile: Profile context.
    """
    result = _find_skill(name)
    if result is None:
        return f"Skill '{name}' not found."

    data, skill_dir = result
    sk = data.get("skill", {})

    lines = [f"# Skill: {sk.get('name', name)}\n"]
    lines.append(f"- **Tier:** {sk.get('tier', 'unknown')}")
    lines.append(f"- **Category:** {sk.get('category', 'uncategorized')}")
    lines.append(f"- **Priority Weight:** {sk.get('priority_weight', 0)}")
    lines.append(f"- **Description:** {sk.get('description', 'N/A')}")

    tags = sk.get("relevance_tags", [])
    if tags:
        lines.append(f"- **Tags:** {', '.join(tags)}")

    rels = data.get("relationships", {})
    if rels:
        lines.append("\n## Relationships")
        if rels.get("prerequisites"):
            lines.append(f"- Prerequisites: {', '.join(rels['prerequisites'])}")
        if rels.get("complements"):
            lines.append(f"- Complements: {', '.join(rels['complements'])}")
        if rels.get("supersedes"):
            lines.append(f"- Supersedes: {', '.join(rels['supersedes'])}")

    tracking = data.get("tracking", {})
    if tracking.get("common_mistakes"):
        lines.append("\n## Common Mistakes")
        for mistake in tracking["common_mistakes"]:
            lines.append(f"- {mistake}")

    # Append SKILL.md content
    md_content = _read_md(skill_dir / "SKILL.md")
    if md_content:
        lines.append("\n---\n")
        lines.append(md_content)

    return "\n".join(lines)


@mcp.tool()
def recommend_skills(task: str, profile: str = "rtg-default") -> str:
    """Recommend skills for a given task description.

    Matches against skill relevance_tags and descriptions.
    Returns top 5 ranked by (keyword_match_count * priority_weight).

    Args:
        task: Description of the task you need help with.
        profile: Profile context.
    """
    query_words = [w.lower() for w in task.split() if w]
    if not query_words:
        return "Please describe the task."

    skills = _scan_skills()
    scored: list[tuple[float, dict]] = []

    for s in skills:
        sk = s.get("skill", {})
        tags = sk.get("relevance_tags", [])
        weight = sk.get("priority_weight", 1)

        searchable = " ".join([
            sk.get("name", ""),
            sk.get("description", ""),
            " ".join(tags),
        ])

        match_count = _keyword_score(searchable, query_words)
        if match_count > 0:
            score = match_count * weight
            scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    if not top:
        return f"No skills matched task: '{task}'"

    lines = [f"# Recommended Skills for: {task}\n"]
    for rank, (score, s) in enumerate(top, 1):
        sk = s.get("skill", {})
        name = sk.get("name", s["_name"])
        desc = sk.get("description", "No description")
        lines.append(f"{rank}. **{name}** (score: {score:.0f}) — {desc}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TOOLS — Profile tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_profile(name: str) -> str:
    """Get full profile details: profile.toml + constraints summary + STACK.md content.

    Args:
        name: Profile directory name (e.g. "rtg-default").
    """
    result = _find_profile(name)
    if result is None:
        return f"Profile '{name}' not found."

    data, prof_dir = result
    prof = data.get("profile", {})

    lines = [f"# Profile: {prof.get('display_name', name)}\n"]
    lines.append(f"- **Name:** {prof.get('name', name)}")
    lines.append(f"- **Version:** {prof.get('version', 'unknown')}")
    lines.append(f"- **Maturity:** {prof.get('maturity', 'unknown')}")
    lines.append(f"- **Description:** {prof.get('description', 'N/A')}")

    # Constraints
    constraints_data = _load_toml(prof_dir / "constraints.toml")
    constraints = constraints_data.get("constraints", {})
    if constraints:
        lines.append("\n## Constraints\n")
        lines.append(f"_{constraints.get('description', '')}_\n")

        required = constraints.get("required", {})
        if required:
            lines.append("### Required Technologies")
            for key, val in required.items():
                if isinstance(val, dict):
                    lines.append(f"- **{key}:** {val.get('name', '')} — {val.get('reason', '')}")

        allowed = constraints.get("allowed", {})
        if allowed:
            lines.append("\n### Allowed")
            for key, vals in allowed.items():
                if isinstance(vals, list):
                    lines.append(f"- **{key}:** {', '.join(vals)}")

        forbidden = constraints.get("forbidden", {})
        if forbidden:
            lines.append("\n### Forbidden")
            for key, vals in forbidden.items():
                if isinstance(vals, list):
                    lines.append(f"- **{key}:** {', '.join(vals)}")

    # STACK.md
    stack_content = _read_md(prof_dir / "STACK.md")
    if stack_content:
        lines.append("\n---\n")
        lines.append(stack_content)

    return "\n".join(lines)


@mcp.tool()
def validate_against_profile(technologies: str, profile: str = "rtg-default") -> str:
    """Validate a technology list against profile constraints.

    Args:
        technologies: Comma-separated list of technologies (e.g. "fastapi, react, mongodb").
        profile: Profile to validate against.
    """
    result = _find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    _, prof_dir = result
    constraints_data = _load_toml(prof_dir / "constraints.toml")
    constraints = constraints_data.get("constraints", {})

    tech_list = [t.strip().lower() for t in technologies.split(",") if t.strip()]

    violations: list[str] = []
    warnings: list[str] = []
    ok: list[str] = []

    # Check forbidden
    forbidden = constraints.get("forbidden", {})
    forbidden_flat: list[str] = []
    for vals in forbidden.values():
        if isinstance(vals, list):
            forbidden_flat.extend(v.lower() for v in vals)

    # Check required
    required = constraints.get("required", {})
    required_names: list[str] = []
    for val in required.values():
        if isinstance(val, dict) and "name" in val:
            required_names.append(val["name"].lower())

    # Check allowed
    allowed = constraints.get("allowed", {})
    allowed_flat: list[str] = []
    for vals in allowed.values():
        if isinstance(vals, list):
            allowed_flat.extend(v.lower() for v in vals)

    for tech in tech_list:
        if any(tech in fb for fb in forbidden_flat):
            violations.append(f"FORBIDDEN: '{tech}' is in the forbidden list")
        elif any(tech in req for req in required_names) or any(tech in a for a in allowed_flat):
            ok.append(f"OK: '{tech}' is approved")
        else:
            warnings.append(f"WARNING: '{tech}' is not in the approved technology list")

    # Check for missing required technologies
    gaps: list[str] = []
    for key, val in required.items():
        if isinstance(val, dict):
            req_name = val.get("name", "").lower()
            if not any(req_name in t or t in req_name for t in tech_list):
                gaps.append(f"MISSING: {val.get('name', key)} ({val.get('reason', '')})")

    lines = [f"# Technology Validation against '{profile}'\n"]

    if violations:
        lines.append("## Violations\n")
        for v in violations:
            lines.append(f"- {v}")

    if gaps:
        lines.append("\n## Missing Required Technologies\n")
        for g in gaps:
            lines.append(f"- {g}")

    if warnings:
        lines.append("\n## Warnings\n")
        for w in warnings:
            lines.append(f"- {w}")

    if ok:
        lines.append("\n## Approved\n")
        for o in ok:
            lines.append(f"- {o}")

    if not violations and not gaps:
        lines.append("\n**Result: PASS** — All technologies are compliant.")
    else:
        lines.append("\n**Result: FAIL** — Violations or gaps detected.")

    return "\n".join(lines)


@mcp.tool()
def list_profiles() -> str:
    """List all available profiles with name, display_name, maturity, and description."""
    profiles = _scan_profiles()

    if not profiles:
        return "No profiles found."

    lines = ["# Forge Profiles\n"]
    for p in profiles:
        prof = p.get("profile", {})
        name = prof.get("name", p["_name"])
        display = prof.get("display_name", name)
        maturity = prof.get("maturity", "unknown")
        desc = prof.get("description", "No description")
        lines.append(f"- **{display}** (`{name}`, {maturity}) — {desc}")

    return "\n".join(lines)


@mcp.tool()
def get_tech_stack(profile: str = "rtg-default") -> str:
    """Get the STACK.md content for a profile.

    Args:
        profile: Profile name.
    """
    result = _find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    _, prof_dir = result
    content = _read_md(prof_dir / "STACK.md")
    return content if content else "No STACK.md found for this profile."


@mcp.tool()
def get_gotchas(profile: str = "rtg-default") -> str:
    """Get the GOTCHAS.md content for a profile.

    Args:
        profile: Profile name.
    """
    result = _find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    _, prof_dir = result
    content = _read_md(prof_dir / "GOTCHAS.md")
    return content if content else "No gotchas documented."


@mcp.tool()
def trigger_health_check(module: str = "") -> str:
    """Run validation on a module (or all modules). Returns JSON health report.

    Args:
        module: Module name. If empty, validates all modules.
    """
    root = _get_forge_root()
    modules_dir = root / "modules"

    if module:
        names = [module]
    else:
        names = [
            d.name for d in sorted(modules_dir.iterdir())
            if d.is_dir() and (d / "module.toml").exists()
        ] if modules_dir.is_dir() else []

    if not names:
        return json.dumps({"error": "No modules found to validate."}, indent=2)

    required_files = [
        "module.toml", "MODULE.md", "__init__.py",
        "router.py", "service.py", "models.py", "config.py",
    ]
    required_dirs = ["migrations", "tests"]

    report: dict = {"modules": {}, "summary": {"total": 0, "passing": 0, "failing": 0}}

    for name in names:
        mod_dir = modules_dir / name
        if not mod_dir.is_dir():
            report["modules"][name] = {"status": "NOT_FOUND"}
            report["summary"]["total"] += 1
            report["summary"]["failing"] += 1
            continue

        checks: dict[str, str] = {}
        all_pass = True

        for fname in required_files:
            exists = (mod_dir / fname).is_file()
            checks[fname] = "pass" if exists else "FAIL"
            if not exists:
                all_pass = False

        for dname in required_dirs:
            exists = (mod_dir / dname).is_dir()
            checks[dname + "/"] = "pass" if exists else "FAIL"
            if not exists:
                all_pass = False

        report["modules"][name] = {
            "status": "PASS" if all_pass else "FAIL",
            "checks": checks,
        }
        report["summary"]["total"] += 1
        if all_pass:
            report["summary"]["passing"] += 1
        else:
            report["summary"]["failing"] += 1

    return json.dumps(report, indent=2)


# ---------------------------------------------------------------------------
# RESOURCES — Read-only context
# ---------------------------------------------------------------------------


@mcp.resource("forge://modules/catalog")
def resource_modules_catalog() -> str:
    """JSON catalog of all forge modules."""
    modules = _scan_modules()
    catalog = []
    for m in modules:
        mod = m.get("module", {})
        catalog.append({
            "name": mod.get("name", m["_name"]),
            "description": mod.get("description", ""),
            "status": mod.get("status", "unknown"),
            "category": mod.get("category", "uncategorized"),
            "version": mod.get("version", "0.0.0"),
            "path": m["_path"],
        })
    return json.dumps(catalog, indent=2)


@mcp.resource("forge://skills/catalog")
def resource_skills_catalog() -> str:
    """JSON catalog of all forge skills."""
    skills = _scan_skills()
    catalog = []
    for s in skills:
        sk = s.get("skill", {})
        catalog.append({
            "name": sk.get("name", s["_name"]),
            "description": sk.get("description", ""),
            "tier": sk.get("tier", "unknown"),
            "category": sk.get("category", s.get("_category_dir", "uncategorized")),
            "priority_weight": sk.get("priority_weight", 0),
            "relevance_tags": sk.get("relevance_tags", []),
            "path": s["_path"],
        })
    return json.dumps(catalog, indent=2)


@mcp.resource("forge://profiles/catalog")
def resource_profiles_catalog() -> str:
    """JSON catalog of all forge profiles."""
    profiles = _scan_profiles()
    catalog = []
    for p in profiles:
        prof = p.get("profile", {})
        catalog.append({
            "name": prof.get("name", p["_name"]),
            "display_name": prof.get("display_name", p["_name"]),
            "description": prof.get("description", ""),
            "maturity": prof.get("maturity", "unknown"),
            "version": prof.get("version", "0.0.0"),
            "path": p["_path"],
        })
    return json.dumps(catalog, indent=2)


@mcp.resource("forge://docs/tech-stack")
def resource_tech_stack() -> str:
    """Tech stack reference document (STACK.md from default profile)."""
    root = _get_forge_root()
    content = _read_md(root / "profiles" / "rtg-default" / "STACK.md")
    return content if content else "No tech stack documentation found."


@mcp.resource("forge://docs/gotchas")
def resource_gotchas() -> str:
    """Gotchas document from default profile."""
    root = _get_forge_root()
    content = _read_md(root / "profiles" / "rtg-default" / "GOTCHAS.md")
    return content if content else "No gotchas documented."


# ---------------------------------------------------------------------------
# PROMPTS — Guided workflows
# ---------------------------------------------------------------------------


@mcp.prompt()
def add_module() -> str:
    """Step-by-step: extract a reusable module from a codebase."""
    return """# Add Module to RTG Forge

You are helping the user extract a reusable module from their existing codebase and add it to RTG Forge.

## Step 1: Identify the Module Boundary
- What functionality should be extracted?
- What are the inputs and outputs?
- What external services does it depend on?

## Step 2: Create the Module Structure
Use `scaffold_module` to get the required file list and template.

## Step 3: Extract Core Logic
- Move business logic into `service.py`
- Define data models in `models.py`
- Create API endpoints in `router.py`
- Set up configuration in `config.py`

## Step 4: Write module.toml
Fill in all metadata, especially the [ai] section:
- `use_when`: When should an AI agent use this module?
- `input_summary`: What does it take as input?
- `output_summary`: What does it produce?

## Step 5: Document in MODULE.md
Write clear documentation including:
- Overview and purpose
- Setup instructions
- API reference
- Examples

## Step 6: Validate
Run `validate_module` to ensure all contract files are present.

## Step 7: Add Tests
Create tests in the `tests/` directory covering core service logic.
"""


@mcp.prompt()
def use_module() -> str:
    """Step-by-step: integrate a forge module into a project."""
    return """# Use a Forge Module

You are helping the user integrate an existing forge module into their project.

## Step 1: Find the Right Module
Use `list_modules` or `search_modules` to find relevant modules.

## Step 2: Review Module Details
Use `get_module` to read the full documentation and understand:
- What the module does
- What dependencies it needs
- What services it requires

## Step 3: Check Setup Requirements
Use `get_module_setup` to get:
- Required environment variables
- Service configurations
- Python dependencies

## Step 4: Install Dependencies
Add the module's Python dependencies to your project.

## Step 5: Database Setup
If the module has database tables:
- Run the migrations from `migrations/`
- Set up RLS policies if `requires_rls = true`

## Step 6: Integrate the Router
Mount the module's FastAPI router in your application:
```python
from modules.{module_name}.router import router
app.include_router(router)
```

## Step 7: Validate Against Profile
Use `validate_against_profile` to ensure all technologies are compliant.

## Step 8: Test
Run the module's built-in tests, then write integration tests for your usage.
"""


@mcp.prompt()
def debug_module() -> str:
    """Troubleshooting flow for module issues."""
    return """# Debug a Forge Module

You are helping the user troubleshoot issues with a forge module.

## Step 1: Validate Structure
Run `validate_module` to check all required files exist.

## Step 2: Check Health
Run `trigger_health_check` to get the module's health status.

## Step 3: Review Configuration
Use `get_module` to check:
- Are all dependencies listed?
- Are service requirements met?
- Is the API prefix correct?

## Step 4: Common Issues

### Import Errors
- Check `__init__.py` exports
- Verify Python dependencies are installed
- Check for circular imports

### Database Errors
- Verify migrations have been run
- Check RLS policies if enabled
- Verify Supabase connection string

### API Errors
- Check router prefix matches module.toml
- Verify auth middleware is configured
- Check request/response model schemas

### AI Pipeline Errors
- Verify API keys (Anthropic, etc.)
- Check LangGraph state definitions
- Review input/output schemas

## Step 5: Check Gotchas
Use `get_gotchas` to review known pitfalls for the tech stack.

## Step 6: Review Related Modules
Check `related_modules` in module.toml for dependencies that might be causing issues.
"""


@mcp.prompt()
def create_profile() -> str:
    """Step-by-step: create a new stack profile."""
    return """# Create a New Stack Profile

You are helping the user create a new technology stack profile for RTG Forge.

## Step 1: Define the Profile
Decide on:
- Profile name (kebab-case, e.g. "my-stack")
- Display name
- Target maturity level (draft, beta, production)

## Step 2: Create profile.toml
```toml
[profile]
name = "my-stack"
display_name = "My Custom Stack"
version = "0.1.0"
description = "Description of this technology stack"
maturity = "draft"

[base]
extends = ""  # or "rtg-default" to inherit

[maintainer]
team = ""
last_reviewed = ""
```

## Step 3: Define Constraints (constraints.toml)
Specify required, allowed, and forbidden technologies:
```toml
[constraints]
description = "My stack constraints"

[constraints.required]
database = { name = "...", reason = "..." }

[constraints.allowed]
hosting = ["..."]

[constraints.forbidden]
orm = ["..."]
```

## Step 4: Write STACK.md
Document:
- Technology overview
- Architecture decisions
- Version requirements
- Integration patterns

## Step 5: Optional: GOTCHAS.md
Document known pitfalls and workarounds.

## Step 6: Validate
Use `list_profiles` to verify your profile appears.
Use `get_profile` to review the rendered output.
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
