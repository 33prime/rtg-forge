"""RTG Forge MCP Server — AI interface to modules, skills, profiles, and decisions.

Provides tools, resources, and prompts for browsing and managing
the RTG Forge module/skill/profile/decision ecosystem.

Supports two backends via FORGE_BACKEND env var:
- "file" (default): reads from local TOML/MD files
- "supabase": reads from Supabase forge_* tables

Supports two transports via MCP_TRANSPORT env var:
- "stdio" (default): local stdio (for dev)
- "sse": HTTP/SSE (for Railway deployment)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from forge_mcp.backends import get_backend

mcp = FastMCP(
    "rtg-forge",
    host=os.environ.get("MCP_HOST", "0.0.0.0") if os.environ.get("MCP_TRANSPORT") == "sse" else "127.0.0.1",
    port=int(os.environ.get("PORT", "8000")),
)

_backend = get_backend()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    modules = _backend.scan_modules()

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
    result = _backend.find_module(name)
    if result is None:
        return f"Module '{name}' not found."

    data, _ = result
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
    md_content = _backend.get_module_md(name)
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

    modules = _backend.scan_modules()
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
    result = _backend.find_module(name)
    if result is None:
        return f"Module '{name}' not found."

    data, _ = result
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
    md_content = _backend.get_module_md(name)
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
    checks = _backend.validate_module_files(name)
    if checks is None:
        return f"Module directory '{name}' does not exist."

    all_pass = all(v == "pass" for v in checks.values())

    lines = [f"# Validation: {name}\n"]
    lines.append(f"**Overall:** {'PASS' if all_pass else 'FAIL'}\n")

    for fname, status in checks.items():
        icon = "pass" if status == "pass" else status
        lines.append(f"- [{icon}] `{fname}`")

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
    skills = _backend.scan_skills()

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
    result = _backend.find_skill(name)
    if result is None:
        return f"Skill '{name}' not found."

    data, _ = result
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
    md_content = _backend.get_skill_md(name)
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

    skills = _backend.scan_skills()
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
    result = _backend.find_profile(name)
    if result is None:
        return f"Profile '{name}' not found."

    data, _ = result
    prof = data.get("profile", {})

    lines = [f"# Profile: {prof.get('display_name', name)}\n"]
    lines.append(f"- **Name:** {prof.get('name', name)}")
    lines.append(f"- **Version:** {prof.get('version', 'unknown')}")
    lines.append(f"- **Maturity:** {prof.get('maturity', 'unknown')}")
    lines.append(f"- **Description:** {prof.get('description', 'N/A')}")

    # Constraints
    constraints_data = _backend.get_constraints(name)
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
    stack_content = _backend.get_stack_md(name)
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
    result = _backend.find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    constraints_data = _backend.get_constraints(profile)
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
    profiles = _backend.scan_profiles()

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
    result = _backend.find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    content = _backend.get_stack_md(profile)
    return content if content else "No STACK.md found for this profile."


@mcp.tool()
def get_gotchas(profile: str = "rtg-default") -> str:
    """Get the GOTCHAS.md content for a profile.

    Args:
        profile: Profile name.
    """
    result = _backend.find_profile(profile)
    if result is None:
        return f"Profile '{profile}' not found."

    content = _backend.get_gotchas_md(profile)
    return content if content else "No gotchas documented."


@mcp.tool()
def trigger_health_check(module: str = "") -> str:
    """Run validation on a module (or all modules). Returns JSON health report.

    Args:
        module: Module name. If empty, validates all modules.
    """
    if module:
        names = [module]
    else:
        modules = _backend.scan_modules()
        names = [m["_name"] for m in modules]

    if not names:
        return json.dumps({"error": "No modules found to validate."}, indent=2)

    report: dict = {"modules": {}, "summary": {"total": 0, "passing": 0, "failing": 0}}

    for name in names:
        checks = _backend.validate_module_files(name)
        if checks is None:
            report["modules"][name] = {"status": "NOT_FOUND"}
            report["summary"]["total"] += 1
            report["summary"]["failing"] += 1
            continue

        all_pass = all(v == "pass" for v in checks.values())
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
# TOOLS — Decision tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_decisions(
    type: str = "",
    severity: str = "",
    profile: str = "rtg-default",
) -> str:
    """List all decisions with name, type, severity, status, and description.

    Args:
        type: Filter by type (correction, architectural, pattern, tradeoff). Empty = all.
        severity: Filter by severity (architectural, structural, style, correctness). Empty = all.
        profile: Profile context.
    """
    decisions = _backend.scan_decisions()

    if type:
        decisions = [
            d for d in decisions
            if d.get("decision", {}).get("type", "") == type
        ]
    if severity:
        decisions = [
            d for d in decisions
            if d.get("decision", {}).get("severity", "") == severity
        ]

    if not decisions:
        return "No decisions found."

    lines = ["# Forge Decisions\n"]
    for d in decisions:
        dec = d.get("decision", {})
        name = dec.get("name", d["_name"])
        dec_type = dec.get("type", "unknown")
        sev = dec.get("severity", "unknown")
        status = dec.get("status", "unknown")
        desc = dec.get("description", "No description")
        category = d.get("_category_dir", "uncategorized")
        lines.append(
            f"- **{name}** (`{dec_type}`, {sev}, {status}) [{category}] — {desc}"
        )

    return "\n".join(lines)


@mcp.tool()
def get_decision(name: str, profile: str = "rtg-default") -> str:
    """Get full details for a decision: decision.toml metadata + DECISION.md content.

    Args:
        name: Decision directory name (e.g. "direct-api-in-components").
        profile: Profile context.
    """
    result = _backend.find_decision(name)
    if result is None:
        return f"Decision '{name}' not found."

    data, _ = result
    dec = data.get("decision", {})

    lines = [f"# Decision: {dec.get('name', name)}\n"]
    lines.append(f"- **Type:** {dec.get('type', 'unknown')}")
    lines.append(f"- **Status:** {dec.get('status', 'unknown')}")
    lines.append(f"- **Severity:** {dec.get('severity', 'unknown')}")
    lines.append(f"- **Description:** {dec.get('description', 'N/A')}")
    lines.append(f"- **Created:** {dec.get('created', 'unknown')}")
    lines.append(f"- **Last Observed:** {dec.get('last_observed', 'unknown')}")

    # Context
    ctx = dec.get("context", {})
    if ctx:
        lines.append("\n## Context")
        if ctx.get("applies_to"):
            lines.append(f"- **Applies to:** {', '.join(ctx['applies_to'])}")
        if ctx.get("trigger"):
            lines.append(f"- **Trigger:** {ctx['trigger']}")

    # Choice
    choice = dec.get("choice", {})
    if choice:
        lines.append("\n## Choice")
        lines.append(f"- **Chosen:** {choice.get('chosen', 'N/A')}")
        rejected = choice.get("rejected", [])
        if rejected:
            lines.append("- **Rejected:**")
            for r in rejected:
                lines.append(f"  - {r.get('option', '?')} — {r.get('reason', '?')}")

    # Evidence
    evidence = dec.get("evidence", {})
    if evidence:
        lines.append("\n## Evidence")
        if evidence.get("skills"):
            lines.append(f"- **Skills:** {', '.join(evidence['skills'])}")
        if evidence.get("modules"):
            lines.append(f"- **Modules:** {', '.join(evidence['modules'])}")
        if evidence.get("related_decisions"):
            lines.append(
                f"- **Related Decisions:** {', '.join(evidence['related_decisions'])}"
            )

    # Correction data
    correction = data.get("correction", {})
    if correction:
        lines.append("\n## Correction")
        lines.append(f"- **Skill Applied:** {correction.get('skill_applied', 'N/A')}")
        lines.append(
            f"- **Instinct Pattern:** {correction.get('instinct_pattern', 'N/A')}"
        )
        lines.append(
            f"- **Corrected Pattern:** {correction.get('corrected_pattern', 'N/A')}"
        )
        lines.append(
            f"- **Impact Level:** {correction.get('impact_level', 'N/A')}"
        )

        freq = correction.get("frequency", {})
        if freq:
            lines.append(
                f"- **Total Observations:** {freq.get('total_observations', 0)}"
            )
            lines.append(
                f"- **First Observed:** {freq.get('first_observed', 'unknown')}"
            )
            lines.append(
                f"- **Last Observed:** {freq.get('last_observed', 'unknown')}"
            )

        classification = correction.get("classification", {})
        if classification:
            if classification.get("themes"):
                lines.append(
                    f"- **Themes:** {', '.join(classification['themes'])}"
                )
            lines.append(
                f"- **Origin:** {classification.get('origin', 'unknown')}"
            )
            lines.append(
                f"- **Predictability:** {classification.get('predictability', 'unknown')}"
            )

    # Append DECISION.md content
    md_content = _backend.get_decision_md(name)
    if md_content:
        lines.append("\n---\n")
        lines.append(md_content)

    return "\n".join(lines)


@mcp.tool()
def search_decisions(query: str, profile: str = "rtg-default") -> str:
    """Search decisions by matching query against descriptions, patterns, and themes.

    Args:
        query: Search query (keywords).
        profile: Profile context.
    """
    query_words = [w.lower() for w in query.split() if w]
    if not query_words:
        return "Please provide a search query."

    decisions = _backend.scan_decisions()
    scored: list[tuple[int, dict]] = []

    for d in decisions:
        dec = d.get("decision", {})
        correction = d.get("correction", {})
        classification = correction.get("classification", {})

        searchable = " ".join([
            dec.get("name", ""),
            dec.get("description", ""),
            dec.get("context", {}).get("trigger", ""),
            dec.get("choice", {}).get("chosen", ""),
            correction.get("instinct_pattern", ""),
            correction.get("corrected_pattern", ""),
            " ".join(classification.get("themes", [])),
            " ".join(dec.get("context", {}).get("applies_to", [])),
        ])

        score = _keyword_score(searchable, query_words)
        if score > 0:
            scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return f"No decisions matched query: '{query}'"

    lines = [f"# Decision Search Results for '{query}'\n"]
    for score, d in scored:
        dec = d.get("decision", {})
        name = dec.get("name", d["_name"])
        desc = dec.get("description", "No description")
        dec_type = dec.get("type", "unknown")
        lines.append(f"- **{name}** ({dec_type}, relevance: {score}) — {desc}")

    return "\n".join(lines)


@mcp.tool()
def record_correction(
    skill_name: str,
    instinct_pattern: str,
    corrected_pattern: str,
    impact_level: str = "structural",
    project: str = "",
    file: str = "",
    context: str = "",
    severity: str = "",
    themes: str = "",
    origin: str = "model-instinct",
    predictability: str = "medium",
) -> str:
    """Record a correction — what Claude got wrong and what a skill fixed.

    Creates a new correction record or increments frequency on an existing one.

    Args:
        skill_name: The skill that prompted the correction.
        instinct_pattern: What Claude does by default without the skill.
        corrected_pattern: What the skill teaches Claude to do instead.
        impact_level: architectural | structural | style | correctness.
        project: Project where this was observed.
        file: File where this was observed.
        context: Additional context about the observation.
        severity: Override severity (defaults to impact_level).
        themes: Comma-separated themes (e.g. "separation-of-concerns,type-safety").
        origin: model-instinct | convention-mismatch | outdated-pattern.
        predictability: high | medium | low.
    """
    return _backend.record_correction({
        "skill_name": skill_name,
        "instinct_pattern": instinct_pattern,
        "corrected_pattern": corrected_pattern,
        "impact_level": impact_level,
        "project": project,
        "file": file,
        "context": context,
        "severity": severity,
        "themes": themes,
        "origin": origin,
        "predictability": predictability,
    })


@mcp.tool()
def get_correction_stats(
    skill_name: str = "",
    min_frequency: int = 1,
    profile: str = "rtg-default",
) -> str:
    """Get aggregate correction statistics ranked by frequency.

    Args:
        skill_name: Filter to corrections for a specific skill. Empty = all.
        min_frequency: Minimum observation count to include.
        profile: Profile context.
    """
    decisions = _backend.scan_decisions()

    corrections: list[dict] = []
    for d in decisions:
        dec = d.get("decision", {})
        if dec.get("type") != "correction":
            continue

        correction = d.get("correction", {})
        freq = correction.get("frequency", {})
        total = freq.get("total_observations", 0)

        if total < min_frequency:
            continue

        if skill_name and correction.get("skill_applied") != skill_name:
            continue

        corrections.append({
            "name": dec.get("name", d["_name"]),
            "skill": correction.get("skill_applied", "unknown"),
            "instinct": correction.get("instinct_pattern", ""),
            "corrected": correction.get("corrected_pattern", ""),
            "impact": correction.get("impact_level", "unknown"),
            "total_observations": total,
            "first_observed": freq.get("first_observed", ""),
            "last_observed": freq.get("last_observed", ""),
            "predictability": correction.get("classification", {}).get(
                "predictability", "unknown"
            ),
            "themes": correction.get("classification", {}).get("themes", []),
            "origin": correction.get("classification", {}).get("origin", "unknown"),
        })

    # Sort by frequency descending
    corrections.sort(key=lambda c: c["total_observations"], reverse=True)

    if not corrections:
        msg = "No corrections found"
        if skill_name:
            msg += f" for skill '{skill_name}'"
        if min_frequency > 1:
            msg += f" with {min_frequency}+ observations"
        return msg + "."

    lines = ["# Correction Statistics\n"]

    if skill_name:
        lines.append(f"**Skill filter:** {skill_name}\n")

    # Summary stats
    total_corrections = len(corrections)
    total_observations = sum(c["total_observations"] for c in corrections)
    lines.append(f"- **Total corrections:** {total_corrections}")
    lines.append(f"- **Total observations:** {total_observations}")

    # By skill breakdown
    by_skill: dict[str, int] = {}
    for c in corrections:
        by_skill[c["skill"]] = by_skill.get(c["skill"], 0) + c["total_observations"]

    if len(by_skill) > 1:
        lines.append("\n## By Skill\n")
        for sk, count in sorted(by_skill.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{sk}:** {count} observations")

    # Individual corrections
    lines.append("\n## Corrections (by frequency)\n")
    for c in corrections:
        lines.append(f"### {c['name']} ({c['total_observations']}x)")
        lines.append(f"- **Skill:** {c['skill']}")
        lines.append(f"- **Instinct:** {c['instinct']}")
        lines.append(f"- **Corrected:** {c['corrected']}")
        lines.append(f"- **Impact:** {c['impact']}")
        lines.append(f"- **Predictability:** {c['predictability']}")
        if c["themes"]:
            lines.append(f"- **Themes:** {', '.join(c['themes'])}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def validate_decision(name: str) -> str:
    """Validate a decision has all required contract files and fields.

    Args:
        name: Decision directory name.
    """
    result = _backend.find_decision(name)
    if result is None:
        return f"Decision '{name}' not found."

    data, decision_dir = result
    checks: list[dict] = []
    all_pass = True

    # File checks — in cloud mode we check for non-empty content
    decision_dir_path = Path(decision_dir)
    for fname in ["decision.toml", "DECISION.md"]:
        if os.environ.get("FORGE_BACKEND", "file") == "supabase":
            # In cloud mode, if we found the decision the data exists
            exists = True
        else:
            exists = (decision_dir_path / fname).exists()
        checks.append({"check": f"File: {fname}", "status": "pass" if exists else "FAIL"})
        if not exists:
            all_pass = False

    # Required decision fields
    dec = data.get("decision", {})
    required_fields = ["name", "version", "type", "status", "severity", "description", "created"]
    for field in required_fields:
        has_field = field in dec
        checks.append({
            "check": f"Field: decision.{field}",
            "status": "pass" if has_field else "FAIL",
        })
        if not has_field:
            all_pass = False

    # Valid enum values
    valid_types = {"correction", "architectural", "pattern", "tradeoff"}
    valid_statuses = {"active", "superseded", "deprecated"}
    valid_severities = {"architectural", "structural", "style", "correctness"}

    dec_type = dec.get("type", "")
    type_ok = dec_type in valid_types
    checks.append({
        "check": f"Enum: type='{dec_type}'",
        "status": "pass" if type_ok else "FAIL",
    })
    if not type_ok:
        all_pass = False

    status = dec.get("status", "")
    status_ok = status in valid_statuses
    checks.append({
        "check": f"Enum: status='{status}'",
        "status": "pass" if status_ok else "FAIL",
    })
    if not status_ok:
        all_pass = False

    sev = dec.get("severity", "")
    sev_ok = sev in valid_severities
    checks.append({
        "check": f"Enum: severity='{sev}'",
        "status": "pass" if sev_ok else "FAIL",
    })
    if not sev_ok:
        all_pass = False

    # Correction-specific checks
    if dec_type == "correction":
        correction = data.get("correction", {})
        has_correction = bool(correction)
        checks.append({
            "check": "Section: [correction]",
            "status": "pass" if has_correction else "FAIL",
        })
        if not has_correction:
            all_pass = False
        else:
            for field in ["skill_applied", "instinct_pattern", "corrected_pattern", "impact_level"]:
                has_field = field in correction
                checks.append({
                    "check": f"Field: correction.{field}",
                    "status": "pass" if has_field else "FAIL",
                })
                if not has_field:
                    all_pass = False

            freq = correction.get("frequency", {})
            has_freq = bool(freq)
            checks.append({
                "check": "Section: [correction.frequency]",
                "status": "pass" if has_freq else "FAIL",
            })
            if not has_freq:
                all_pass = False

    lines = [f"# Validation: {name}\n"]
    lines.append(f"**Overall:** {'PASS' if all_pass else 'FAIL'}\n")

    for c in checks:
        icon = "pass" if c["status"] == "pass" else "FAIL"
        lines.append(f"- [{icon}] `{c['check']}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RESOURCES — Read-only context
# ---------------------------------------------------------------------------


@mcp.resource("forge://modules/catalog")
def resource_modules_catalog() -> str:
    """JSON catalog of all forge modules."""
    modules = _backend.scan_modules()
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
    skills = _backend.scan_skills()
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
    profiles = _backend.scan_profiles()
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
    content = _backend.get_stack_md("rtg-default")
    return content if content else "No tech stack documentation found."


@mcp.resource("forge://docs/gotchas")
def resource_gotchas() -> str:
    """Gotchas document from default profile."""
    content = _backend.get_gotchas_md("rtg-default")
    return content if content else "No gotchas documented."


@mcp.resource("forge://decisions/catalog")
def resource_decisions_catalog() -> str:
    """JSON catalog of all forge decisions."""
    decisions = _backend.scan_decisions()
    catalog = []
    for d in decisions:
        dec = d.get("decision", {})
        catalog.append({
            "name": dec.get("name", d["_name"]),
            "description": dec.get("description", ""),
            "type": dec.get("type", "unknown"),
            "status": dec.get("status", "unknown"),
            "severity": dec.get("severity", "unknown"),
            "category": d.get("_category_dir", "uncategorized"),
            "created": dec.get("created", ""),
            "last_observed": dec.get("last_observed", ""),
            "path": d["_path"],
        })
    return json.dumps(catalog, indent=2)


@mcp.resource("forge://decisions/corrections-summary")
def resource_corrections_summary() -> str:
    """Corrections ranked by observation frequency."""
    decisions = _backend.scan_decisions()
    corrections = []
    for d in decisions:
        dec = d.get("decision", {})
        if dec.get("type") != "correction":
            continue
        correction = d.get("correction", {})
        freq = correction.get("frequency", {})
        corrections.append({
            "name": dec.get("name", d["_name"]),
            "skill": correction.get("skill_applied", "unknown"),
            "instinct_pattern": correction.get("instinct_pattern", ""),
            "corrected_pattern": correction.get("corrected_pattern", ""),
            "impact_level": correction.get("impact_level", "unknown"),
            "total_observations": freq.get("total_observations", 0),
            "predictability": correction.get("classification", {}).get(
                "predictability", "unknown"
            ),
            "themes": correction.get("classification", {}).get("themes", []),
        })
    corrections.sort(key=lambda c: c["total_observations"], reverse=True)
    return json.dumps(corrections, indent=2)


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


@mcp.prompt()
def capture_correction() -> str:
    """Step-by-step: record a before/after correction from a skill application."""
    return """# Capture Correction

You are helping the user record a correction — the delta between what Claude wrote
without a skill and what the skill fixed. This data feeds the learning loop.

## Step 1: Identify the Delta
- What code did Claude write before reading the skill? (instinct pattern)
- What did the code look like after applying the skill? (corrected pattern)
- Which skill prompted the change?

## Step 2: Classify the Correction
- **Impact level:** architectural (system-level) | structural (file/component) | style (conventions) | correctness (bugs)
- **Origin:** model-instinct (Claude default) | convention-mismatch (valid but wrong for stack) | outdated-pattern (once correct, now superseded)
- **Predictability:** high (happens every time) | medium (often) | low (occasional)
- **Themes:** e.g., separation-of-concerns, type-safety, caching, error-handling

## Step 3: Check for Duplicates
Use `search_decisions` to see if this correction already exists.

## Step 4: Record
If duplicate exists: use `record_correction` — it will increment the frequency counter.
If new: use `record_correction` — it will create the full decision record.

Required args:
- `skill_name`: The skill that prompted the correction
- `instinct_pattern`: What Claude does without the skill
- `corrected_pattern`: What the skill teaches

Optional but valuable:
- `project`: Where this was observed
- `file`: Which file
- `themes`: Comma-separated theme tags
- `context`: Additional context

## Step 5: Verify
Use `validate_decision` to ensure the record is contract-compliant.
Use `get_decision` to review the full record.
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
