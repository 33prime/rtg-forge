"""Sync forge knowledge from disk (TOML + MD files) to Supabase tables.

Reads all skills, modules, profiles, and decisions from the forge root
and upserts them into the corresponding forge_* tables.

Usage:
    python -m forge_intelligence.sync_to_supabase [--forge-root /path/to/forge]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import tomli
from supabase import Client, create_client


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


def _get_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


def sync_skills(forge_root: Path, client: Client) -> int:
    """Sync skills/<category>/<name>/ to forge_skills table. Returns count."""
    skills_dir = forge_root / "skills"
    if not skills_dir.is_dir():
        return 0

    count = 0
    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("_"):
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            meta_path = skill_dir / "meta.toml"
            if not skill_dir.is_dir() or not meta_path.exists():
                continue

            data = _load_toml(meta_path)
            sk = data.get("skill", {})
            rels = data.get("relationships", {})
            tracking = data.get("tracking", {})
            optimization = data.get("optimization", {})
            skill_md = _read_md(skill_dir / "SKILL.md")

            row = {
                "name": sk.get("name", skill_dir.name),
                "version": sk.get("version", "0.1.0"),
                "tier": sk.get("tier", "foundation"),
                "category": sk.get("category", category_dir.name),
                "priority_weight": sk.get("priority_weight", 50),
                "description": sk.get("description", ""),
                "relevance_tags": sk.get("relevance_tags", []),
                "prerequisites": rels.get("prerequisites", []),
                "complements": rels.get("complements", []),
                "supersedes": rels.get("supersedes", []),
                "common_mistakes": tracking.get("common_mistakes", []),
                "optimization": optimization,
                "skill_md": skill_md,
                "source_path": str(skill_dir.relative_to(forge_root)),
                "synced_at": _now_iso(),
            }

            client.table("forge_skills").upsert(
                row, on_conflict="name"
            ).execute()
            count += 1
            print(f"  [skill] {row['name']}")

    return count


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------


def sync_modules(forge_root: Path, client: Client) -> int:
    """Sync modules/<name>/ to forge_modules table. Returns count."""
    modules_dir = forge_root / "modules"
    if not modules_dir.is_dir():
        return 0

    count = 0
    for mod_dir in sorted(modules_dir.iterdir()):
        toml_path = mod_dir / "module.toml"
        if not mod_dir.is_dir() or not toml_path.exists():
            continue

        data = _load_toml(toml_path)
        mod = data.get("module", {})
        deps = mod.get("dependencies", {})
        api = mod.get("api", {})
        db = mod.get("database", {})
        ai = data.get("ai", {})
        health = data.get("health", {})
        module_md = _read_md(mod_dir / "MODULE.md")

        row = {
            "name": mod.get("name", mod_dir.name),
            "version": mod.get("version", "0.1.0"),
            "description": mod.get("description", ""),
            "status": mod.get("status", "draft"),
            "category": mod.get("category", "uncategorized"),
            "author": mod.get("author", ""),
            "deps_python": deps.get("python", []),
            "deps_services": deps.get("services", []),
            "deps_modules": deps.get("modules", []),
            "api_prefix": api.get("prefix", ""),
            "api_auth_required": api.get("auth_required", True),
            "db_tables": db.get("tables", []),
            "db_requires_rls": db.get("requires_rls", True),
            "ai_use_when": ai.get("use_when", ""),
            "ai_input_summary": ai.get("input_summary", ""),
            "ai_output_summary": ai.get("output_summary", ""),
            "ai_complexity": ai.get("complexity", "medium"),
            "ai_estimated_setup_minutes": ai.get("estimated_setup_minutes", 15),
            "ai_related_modules": ai.get("related_modules", []),
            "health_last_validated": health.get("last_validated", ""),
            "health_test_coverage": health.get("test_coverage", 0),
            "health_known_issues": health.get("known_issues", []),
            "module_md": module_md,
            "source_path": str(mod_dir.relative_to(forge_root)),
            "synced_at": _now_iso(),
        }

        client.table("forge_modules").upsert(
            row, on_conflict="name"
        ).execute()
        count += 1
        print(f"  [module] {row['name']}")

    return count


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


def sync_profiles(forge_root: Path, client: Client) -> int:
    """Sync profiles/<name>/ to forge_profiles + forge_profile_constraints. Returns count."""
    profiles_dir = forge_root / "profiles"
    if not profiles_dir.is_dir():
        return 0

    count = 0
    for prof_dir in sorted(profiles_dir.iterdir()):
        profile_toml = prof_dir / "profile.toml"
        if not prof_dir.is_dir() or not profile_toml.exists() or prof_dir.name.startswith("_"):
            continue

        data = _load_toml(profile_toml)
        prof = data.get("profile", {})
        base = data.get("base", {})
        maintainer = data.get("maintainer", {})
        stack_md = _read_md(prof_dir / "STACK.md")
        gotchas_md = _read_md(prof_dir / "GOTCHAS.md")
        if not gotchas_md:
            gotchas_md = _read_md(prof_dir / "gotchas" / "GOTCHAS.md")

        profile_row = {
            "name": prof.get("name", prof_dir.name),
            "display_name": prof.get("display_name", prof_dir.name),
            "version": prof.get("version", "0.1.0"),
            "description": prof.get("description", ""),
            "maturity": prof.get("maturity", "draft"),
            "vendor": prof.get("vendor", ""),
            "vendor_url": prof.get("vendor_url", ""),
            "extends": base.get("extends", ""),
            "maintainer_team": maintainer.get("team", ""),
            "maintainer_last_reviewed": maintainer.get("last_reviewed", ""),
            "stack_md": stack_md,
            "gotchas_md": gotchas_md,
            "source_path": str(prof_dir.relative_to(forge_root)),
            "synced_at": _now_iso(),
        }

        resp = client.table("forge_profiles").upsert(
            profile_row, on_conflict="name"
        ).execute()

        # Get the profile ID for constraints
        profile_id = resp.data[0]["id"] if resp.data else None

        if profile_id:
            # Sync constraints
            constraints_data = _load_toml(prof_dir / "constraints.toml")
            constraints = constraints_data.get("constraints", {})
            if constraints:
                constraint_row = {
                    "profile_id": profile_id,
                    "description": constraints.get("description", ""),
                    "required": constraints.get("required", {}),
                    "allowed": constraints.get("allowed", {}),
                    "forbidden": constraints.get("forbidden", {}),
                    "overrides": constraints.get("overrides", {}),
                    "source_path": str((prof_dir / "constraints.toml").relative_to(forge_root)),
                    "synced_at": _now_iso(),
                }

                # Upsert by profile_id — delete existing and insert fresh
                client.table("forge_profile_constraints").delete().eq(
                    "profile_id", profile_id
                ).execute()
                client.table("forge_profile_constraints").insert(
                    constraint_row
                ).execute()

        count += 1
        print(f"  [profile] {profile_row['name']}")

    return count


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


def sync_decisions(forge_root: Path, client: Client) -> int:
    """Sync decisions/<category>/<name>/ to forge_decisions table. Returns count."""
    decisions_dir = forge_root / "decisions"
    if not decisions_dir.is_dir():
        return 0

    count = 0
    for category_dir in sorted(decisions_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith(("_", ".")):
            continue
        for decision_dir in sorted(category_dir.iterdir()):
            toml_path = decision_dir / "decision.toml"
            if not decision_dir.is_dir() or not toml_path.exists():
                continue

            data = _load_toml(toml_path)
            dec = data.get("decision", {})
            ctx = dec.get("context", {})
            choice = dec.get("choice", {})
            evidence = dec.get("evidence", {})
            correction = data.get("correction", {})
            freq = correction.get("frequency", {})
            classification = correction.get("classification", {})
            decision_md = _read_md(decision_dir / "DECISION.md")

            row = {
                "name": dec.get("name", decision_dir.name),
                "version": dec.get("version", "0.1.0"),
                "type": dec.get("type", "correction"),
                "status": dec.get("status", "active"),
                "severity": dec.get("severity", "structural"),
                "description": dec.get("description", ""),
                "created_date": dec.get("created", ""),
                "last_observed": dec.get("last_observed", ""),
                "category": category_dir.name,
                "context_applies_to": ctx.get("applies_to", []),
                "context_profiles": ctx.get("profiles", ["rtg-default"]),
                "context_trigger": ctx.get("trigger", ""),
                "choice_chosen": choice.get("chosen", ""),
                "choice_rejected": choice.get("rejected", []),
                "evidence_skills": evidence.get("skills", []),
                "evidence_modules": evidence.get("modules", []),
                "evidence_related_decisions": evidence.get("related_decisions", []),
                "correction_skill_applied": correction.get("skill_applied"),
                "correction_instinct_pattern": correction.get("instinct_pattern"),
                "correction_corrected_pattern": correction.get("corrected_pattern"),
                "correction_impact_level": correction.get("impact_level"),
                "correction_total_observations": freq.get("total_observations", 0),
                "correction_first_observed": freq.get("first_observed"),
                "correction_last_observed": freq.get("last_observed"),
                "correction_observations": freq.get("observations", []),
                "correction_themes": classification.get("themes", []),
                "correction_origin": classification.get("origin"),
                "correction_predictability": classification.get("predictability"),
                "decision_md": decision_md,
                "source_path": str(decision_dir.relative_to(forge_root)),
                "synced_at": _now_iso(),
            }

            client.table("forge_decisions").upsert(
                row, on_conflict="name"
            ).execute()
            count += 1
            print(f"  [decision] {row['name']} ({category_dir.name})")

    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def sync_all(forge_root: Path) -> dict[str, int]:
    """Run full sync from disk to Supabase. Returns counts per entity type."""
    client = _get_client()
    print(f"Syncing forge knowledge from {forge_root} to Supabase...\n")

    counts = {}
    counts["skills"] = sync_skills(forge_root, client)
    counts["modules"] = sync_modules(forge_root, client)
    counts["profiles"] = sync_profiles(forge_root, client)
    counts["decisions"] = sync_decisions(forge_root, client)

    print(f"\nSync complete: {counts}")
    return counts


def _resolve_forge_root(path: str | None) -> Path:
    if path:
        return Path(path)
    env = os.environ.get("FORGE_ROOT")
    if env:
        return Path(env)
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "forge.toml").exists():
            return parent
    return current


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync forge knowledge to Supabase")
    parser.add_argument("--forge-root", help="Path to forge root directory")
    args = parser.parse_args()

    forge_root = _resolve_forge_root(args.forge_root)
    if not (forge_root / "forge.toml").exists():
        print(f"Error: forge.toml not found in {forge_root}", file=sys.stderr)
        sys.exit(1)

    sync_all(forge_root)


if __name__ == "__main__":
    main()
