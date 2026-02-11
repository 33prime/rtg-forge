"""Backend abstraction for RTG Forge data access.

Supports two backends:
- FileBackend: reads TOML/MD files from disk (default, for local dev)
- SupabaseBackend: reads from forge_* tables (for cloud deployment)

Select via FORGE_BACKEND env var: "file" (default) or "supabase".
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path

import tomli
import tomli_w


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class ForgeBackend(ABC):
    """Abstract interface for reading/writing forge knowledge."""

    # -- Modules --
    @abstractmethod
    def scan_modules(self) -> list[dict]: ...

    @abstractmethod
    def find_module(self, name: str) -> tuple[dict, str] | None: ...

    @abstractmethod
    def get_module_md(self, name: str) -> str: ...

    # -- Skills --
    @abstractmethod
    def scan_skills(self) -> list[dict]: ...

    @abstractmethod
    def find_skill(self, name: str) -> tuple[dict, str] | None: ...

    @abstractmethod
    def get_skill_md(self, name: str) -> str: ...

    # -- Profiles --
    @abstractmethod
    def scan_profiles(self) -> list[dict]: ...

    @abstractmethod
    def find_profile(self, name: str) -> tuple[dict, str] | None: ...

    @abstractmethod
    def get_stack_md(self, name: str) -> str: ...

    @abstractmethod
    def get_gotchas_md(self, name: str) -> str: ...

    @abstractmethod
    def get_constraints(self, name: str) -> dict: ...

    # -- Decisions --
    @abstractmethod
    def scan_decisions(self) -> list[dict]: ...

    @abstractmethod
    def find_decision(self, name: str) -> tuple[dict, str] | None: ...

    @abstractmethod
    def get_decision_md(self, name: str) -> str: ...

    @abstractmethod
    def record_correction(self, data: dict) -> str: ...

    # -- Validation --
    @abstractmethod
    def validate_module_files(self, name: str) -> dict | None: ...


# ---------------------------------------------------------------------------
# File backend — wraps existing disk-based helpers
# ---------------------------------------------------------------------------


def _get_forge_root() -> Path:
    """Return the forge root directory."""
    env_root = os.environ.get("FORGE_ROOT")
    if env_root:
        return Path(env_root)

    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "forge.toml").exists():
            return parent
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


class FileBackend(ForgeBackend):
    """Reads forge knowledge from TOML + Markdown files on disk."""

    def __init__(self) -> None:
        self.root = _get_forge_root()

    # -- Modules --

    def scan_modules(self) -> list[dict]:
        modules_dir = self.root / "modules"
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

    def find_module(self, name: str) -> tuple[dict, str] | None:
        mod_dir = self.root / "modules" / name
        toml_path = mod_dir / "module.toml"
        if toml_path.exists():
            return _load_toml(toml_path), str(mod_dir)
        return None

    def get_module_md(self, name: str) -> str:
        return _read_md(self.root / "modules" / name / "MODULE.md")

    # -- Skills --

    def scan_skills(self) -> list[dict]:
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            return []
        results: list[dict] = []
        for category_dir in sorted(skills_dir.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
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

    def find_skill(self, name: str) -> tuple[dict, str] | None:
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            return None
        for category_dir in skills_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            skill_dir = category_dir / name
            toml_path = skill_dir / "meta.toml"
            if toml_path.exists():
                return _load_toml(toml_path), str(skill_dir)
        return None

    def get_skill_md(self, name: str) -> str:
        result = self.find_skill(name)
        if result is None:
            return ""
        _, skill_dir = result
        return _read_md(Path(skill_dir) / "SKILL.md")

    # -- Profiles --

    def scan_profiles(self) -> list[dict]:
        profiles_dir = self.root / "profiles"
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

    def find_profile(self, name: str) -> tuple[dict, str] | None:
        prof_dir = self.root / "profiles" / name
        toml_path = prof_dir / "profile.toml"
        if toml_path.exists():
            return _load_toml(toml_path), str(prof_dir)
        return None

    def get_stack_md(self, name: str) -> str:
        return _read_md(self.root / "profiles" / name / "STACK.md")

    def get_gotchas_md(self, name: str) -> str:
        return _read_md(self.root / "profiles" / name / "GOTCHAS.md")

    def get_constraints(self, name: str) -> dict:
        return _load_toml(self.root / "profiles" / name / "constraints.toml")

    # -- Decisions --

    def scan_decisions(self) -> list[dict]:
        decisions_dir = self.root / "decisions"
        if not decisions_dir.is_dir():
            return []
        results: list[dict] = []
        for category_dir in sorted(decisions_dir.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith(("_", ".")):
                continue
            for decision_dir in sorted(category_dir.iterdir()):
                toml_path = decision_dir / "decision.toml"
                if decision_dir.is_dir() and toml_path.exists():
                    data = _load_toml(toml_path)
                    data["_path"] = str(decision_dir)
                    data["_name"] = decision_dir.name
                    data["_category_dir"] = category_dir.name
                    results.append(data)
        return results

    def find_decision(self, name: str) -> tuple[dict, str] | None:
        decisions_dir = self.root / "decisions"
        if not decisions_dir.is_dir():
            return None
        for category_dir in decisions_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith(("_", ".")):
                continue
            decision_dir = category_dir / name
            toml_path = decision_dir / "decision.toml"
            if toml_path.exists():
                return _load_toml(toml_path), str(decision_dir)
        return None

    def get_decision_md(self, name: str) -> str:
        result = self.find_decision(name)
        if result is None:
            return ""
        _, decision_dir = result
        return _read_md(Path(decision_dir) / "DECISION.md")

    def record_correction(self, data: dict) -> str:
        """Record a correction to disk. data keys mirror record_correction tool args."""
        skill_name = data["skill_name"]
        instinct_pattern = data["instinct_pattern"]
        corrected_pattern = data["corrected_pattern"]
        impact_level = data.get("impact_level", "structural")
        project = data.get("project", "")
        file = data.get("file", "")
        context = data.get("context", "")
        severity = data.get("severity", "") or impact_level
        themes = data.get("themes", "")
        origin = data.get("origin", "model-instinct")
        predictability = data.get("predictability", "medium")

        decisions_dir = self.root / "decisions" / "corrections"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()
        theme_list = [t.strip() for t in themes.split(",") if t.strip()] if themes else []

        # Slugify instinct_pattern for decision name
        slug_base = instinct_pattern.lower()[:60]
        slug = ""
        for ch in slug_base:
            if ch.isalnum():
                slug += ch
            elif ch in (" ", "_", "-"):
                if slug and slug[-1] != "-":
                    slug += "-"
        slug = slug.strip("-")
        if not slug:
            slug = skill_name
        decision_name = slug

        # Check if correction already exists
        existing = self.find_decision(decision_name)
        if existing is not None:
            edata, decision_dir = existing
            correction = edata.get("correction", {})
            freq = correction.get("frequency", {})

            total = freq.get("total_observations", 0) + 1
            observations = freq.get("observations", [])
            observations.append({"date": today, "project": project, "file": file})

            freq["total_observations"] = total
            freq["last_observed"] = today
            freq["observations"] = observations
            correction["frequency"] = freq
            edata["correction"] = correction

            dec = edata.get("decision", {})
            dec["last_observed"] = today
            edata["decision"] = dec

            toml_path = Path(decision_dir) / "decision.toml"
            toml_path.write_bytes(tomli_w.dumps(edata).encode())

            return (
                f"Updated existing correction '{decision_name}' — "
                f"now at {total} observations."
            )

        # Create new correction record
        decision_dir_path = decisions_dir / decision_name
        decision_dir_path.mkdir(parents=True, exist_ok=True)

        # Determine applies_to from skill metadata
        skill_result = self.find_skill(skill_name)
        applies_to: list[str] = []
        if skill_result:
            skill_data, _ = skill_result
            applies_to = skill_data.get("skill", {}).get("relevance_tags", [])[:5]

        record = {
            "decision": {
                "name": decision_name,
                "version": "0.1.0",
                "type": "correction",
                "status": "active",
                "severity": severity,
                "description": f"Correction: {instinct_pattern[:80]}",
                "created": today,
                "last_observed": today,
                "context": {
                    "applies_to": applies_to,
                    "profiles": ["rtg-default"],
                    "trigger": instinct_pattern,
                },
                "choice": {
                    "chosen": corrected_pattern,
                    "rejected": [
                        {"option": instinct_pattern, "reason": f"Corrected by skill {skill_name}"},
                    ],
                },
                "evidence": {
                    "skills": [skill_name],
                    "modules": [],
                    "related_decisions": [],
                },
            },
            "correction": {
                "skill_applied": skill_name,
                "instinct_pattern": instinct_pattern,
                "corrected_pattern": corrected_pattern,
                "impact_level": impact_level,
                "frequency": {
                    "total_observations": 1,
                    "first_observed": today,
                    "last_observed": today,
                    "observations": [
                        {"date": today, "project": project, "file": file},
                    ],
                },
                "classification": {
                    "themes": theme_list,
                    "origin": origin,
                    "predictability": predictability,
                },
            },
        }

        toml_path = decision_dir_path / "decision.toml"
        toml_path.write_bytes(tomli_w.dumps(record).encode())

        md_content = f"""# Decision: {decision_name}

## Summary

Claude's default instinct is to {instinct_pattern}. The skill `{skill_name}` corrects this to {corrected_pattern}.

## Context

{context or f"Observed while working on {project or 'a project'}."}

## Instinct Pattern (Before)

{instinct_pattern}

## Corrected Pattern (After)

{corrected_pattern}

## Reasoning

The corrected pattern follows the guidelines established in the `{skill_name}` skill. The instinct pattern was identified as a {origin.replace('-', ' ')} that impacts code at the {impact_level} level.

## Observations

| Date | Project | File | Notes |
|------|---------|------|-------|
| {today} | {project or 'unknown'} | {file or 'unknown'} | Initial observation |
"""
        (decision_dir_path / "DECISION.md").write_text(md_content, encoding="utf-8")

        return (
            f"Created new correction '{decision_name}' in decisions/corrections/. "
            f"Skill: {skill_name}, Impact: {impact_level}."
        )

    # -- Validation --

    def validate_module_files(self, name: str) -> dict | None:
        mod_dir = self.root / "modules" / name
        if not mod_dir.is_dir():
            return None

        required_files = [
            "module.toml", "MODULE.md", "__init__.py",
            "router.py", "service.py", "models.py", "config.py",
        ]
        required_dirs = ["migrations", "tests"]

        checks: dict[str, str] = {}
        for fname in required_files:
            checks[fname] = "pass" if (mod_dir / fname).is_file() else "FAIL"
        for dname in required_dirs:
            checks[dname + "/"] = "pass" if (mod_dir / dname).is_dir() else "FAIL"

        return checks


# ---------------------------------------------------------------------------
# Supabase backend — reads from forge_* tables
# ---------------------------------------------------------------------------


class SupabaseBackend(ForgeBackend):
    """Reads forge knowledge from Supabase forge_* tables."""

    def __init__(self) -> None:
        from supabase import Client, create_client

        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for supabase backend")
        self._client: Client = create_client(url, key)

    # -- Modules --

    def scan_modules(self) -> list[dict]:
        resp = self._client.table("forge_modules").select("*").execute()
        return [self._row_to_module(r) for r in resp.data]

    def find_module(self, name: str) -> tuple[dict, str] | None:
        resp = self._client.table("forge_modules").select("*").eq("name", name).execute()
        if not resp.data:
            return None
        row = resp.data[0]
        return self._row_to_module(row), row.get("source_path", f"modules/{name}")

    def get_module_md(self, name: str) -> str:
        resp = self._client.table("forge_modules").select("module_md").eq("name", name).execute()
        if not resp.data:
            return ""
        return resp.data[0].get("module_md", "")

    @staticmethod
    def _row_to_module(row: dict) -> dict:
        """Reconstruct the nested dict structure tools expect from a flat DB row."""
        return {
            "module": {
                "name": row["name"],
                "version": row.get("version", "0.1.0"),
                "description": row.get("description", ""),
                "status": row.get("status", "draft"),
                "category": row.get("category", "uncategorized"),
                "author": row.get("author", ""),
                "dependencies": {
                    "python": row.get("deps_python", []),
                    "services": row.get("deps_services", []),
                    "modules": row.get("deps_modules", []),
                },
                "api": {
                    "prefix": row.get("api_prefix", ""),
                    "auth_required": row.get("api_auth_required", True),
                },
                "database": {
                    "tables": row.get("db_tables", []),
                    "requires_rls": row.get("db_requires_rls", True),
                },
            },
            "ai": {
                "use_when": row.get("ai_use_when", ""),
                "input_summary": row.get("ai_input_summary", ""),
                "output_summary": row.get("ai_output_summary", ""),
                "complexity": row.get("ai_complexity", "medium"),
                "estimated_setup_minutes": row.get("ai_estimated_setup_minutes", 15),
                "related_modules": row.get("ai_related_modules", []),
            },
            "health": {
                "last_validated": row.get("health_last_validated", ""),
                "test_coverage": row.get("health_test_coverage", 0),
                "known_issues": row.get("health_known_issues", []),
            },
            "_path": row.get("source_path", f"modules/{row['name']}"),
            "_name": row["name"],
        }

    # -- Skills --

    def scan_skills(self) -> list[dict]:
        resp = self._client.table("forge_skills").select("*").execute()
        return [self._row_to_skill(r) for r in resp.data]

    def find_skill(self, name: str) -> tuple[dict, str] | None:
        resp = self._client.table("forge_skills").select("*").eq("name", name).execute()
        if not resp.data:
            return None
        row = resp.data[0]
        return self._row_to_skill(row), row.get("source_path", f"skills/{row.get('category', 'unknown')}/{name}")

    def get_skill_md(self, name: str) -> str:
        resp = self._client.table("forge_skills").select("skill_md").eq("name", name).execute()
        if not resp.data:
            return ""
        return resp.data[0].get("skill_md", "")

    @staticmethod
    def _row_to_skill(row: dict) -> dict:
        return {
            "skill": {
                "name": row["name"],
                "version": row.get("version", "0.1.0"),
                "tier": row.get("tier", "foundation"),
                "category": row.get("category", "uncategorized"),
                "priority_weight": row.get("priority_weight", 50),
                "description": row.get("description", ""),
                "relevance_tags": row.get("relevance_tags", []),
            },
            "relationships": {
                "prerequisites": row.get("prerequisites", []),
                "complements": row.get("complements", []),
                "supersedes": row.get("supersedes", []),
            },
            "tracking": {
                "common_mistakes": row.get("common_mistakes", []),
            },
            "optimization": row.get("optimization", {}),
            "_path": row.get("source_path", f"skills/{row.get('category', 'unknown')}/{row['name']}"),
            "_name": row["name"],
            "_category_dir": row.get("category", "uncategorized"),
        }

    # -- Profiles --

    def scan_profiles(self) -> list[dict]:
        resp = self._client.table("forge_profiles").select("*").execute()
        return [self._row_to_profile(r) for r in resp.data]

    def find_profile(self, name: str) -> tuple[dict, str] | None:
        resp = self._client.table("forge_profiles").select("*").eq("name", name).execute()
        if not resp.data:
            return None
        row = resp.data[0]
        return self._row_to_profile(row), row.get("source_path", f"profiles/{name}")

    def get_stack_md(self, name: str) -> str:
        resp = self._client.table("forge_profiles").select("stack_md").eq("name", name).execute()
        if not resp.data:
            return ""
        return resp.data[0].get("stack_md", "")

    def get_gotchas_md(self, name: str) -> str:
        resp = self._client.table("forge_profiles").select("gotchas_md").eq("name", name).execute()
        if not resp.data:
            return ""
        return resp.data[0].get("gotchas_md", "")

    def get_constraints(self, name: str) -> dict:
        # First look up the profile to get its ID
        prof_resp = self._client.table("forge_profiles").select("id").eq("name", name).execute()
        if not prof_resp.data:
            return {}
        profile_id = prof_resp.data[0]["id"]
        resp = self._client.table("forge_profile_constraints").select("*").eq("profile_id", profile_id).execute()
        if not resp.data:
            return {}
        row = resp.data[0]
        return {
            "constraints": {
                "description": row.get("description", ""),
                "required": row.get("required", {}),
                "allowed": row.get("allowed", {}),
                "forbidden": row.get("forbidden", {}),
            }
        }

    @staticmethod
    def _row_to_profile(row: dict) -> dict:
        return {
            "profile": {
                "name": row["name"],
                "display_name": row.get("display_name", row["name"]),
                "version": row.get("version", "0.1.0"),
                "description": row.get("description", ""),
                "maturity": row.get("maturity", "draft"),
                "vendor": row.get("vendor", ""),
                "vendor_url": row.get("vendor_url", ""),
            },
            "base": {
                "extends": row.get("extends", ""),
            },
            "maintainer": {
                "team": row.get("maintainer_team", ""),
                "last_reviewed": row.get("maintainer_last_reviewed", ""),
            },
            "_path": row.get("source_path", f"profiles/{row['name']}"),
            "_name": row["name"],
        }

    # -- Decisions --

    def scan_decisions(self) -> list[dict]:
        resp = self._client.table("forge_decisions").select("*").execute()
        return [self._row_to_decision(r) for r in resp.data]

    def find_decision(self, name: str) -> tuple[dict, str] | None:
        resp = self._client.table("forge_decisions").select("*").eq("name", name).execute()
        if not resp.data:
            return None
        row = resp.data[0]
        return self._row_to_decision(row), row.get("source_path", f"decisions/{row.get('category', 'unknown')}/{name}")

    def get_decision_md(self, name: str) -> str:
        resp = self._client.table("forge_decisions").select("decision_md").eq("name", name).execute()
        if not resp.data:
            return ""
        return resp.data[0].get("decision_md", "")

    @staticmethod
    def _row_to_decision(row: dict) -> dict:
        data: dict = {
            "decision": {
                "name": row["name"],
                "version": row.get("version", "0.1.0"),
                "type": row.get("type", "correction"),
                "status": row.get("status", "active"),
                "severity": row.get("severity", "structural"),
                "description": row.get("description", ""),
                "created": row.get("created_date", ""),
                "last_observed": row.get("last_observed", ""),
                "context": {
                    "applies_to": row.get("context_applies_to", []),
                    "profiles": row.get("context_profiles", ["rtg-default"]),
                    "trigger": row.get("context_trigger", ""),
                },
                "choice": {
                    "chosen": row.get("choice_chosen", ""),
                    "rejected": row.get("choice_rejected", []),
                },
                "evidence": {
                    "skills": row.get("evidence_skills", []),
                    "modules": row.get("evidence_modules", []),
                    "related_decisions": row.get("evidence_related_decisions", []),
                },
            },
            "_path": row.get("source_path", f"decisions/{row.get('category', 'unknown')}/{row['name']}"),
            "_name": row["name"],
            "_category_dir": row.get("category", "uncategorized"),
        }

        # Add correction section if this is a correction type
        if row.get("type") == "correction" and row.get("correction_skill_applied"):
            data["correction"] = {
                "skill_applied": row.get("correction_skill_applied", ""),
                "instinct_pattern": row.get("correction_instinct_pattern", ""),
                "corrected_pattern": row.get("correction_corrected_pattern", ""),
                "impact_level": row.get("correction_impact_level", ""),
                "frequency": {
                    "total_observations": row.get("correction_total_observations", 0),
                    "first_observed": row.get("correction_first_observed", ""),
                    "last_observed": row.get("correction_last_observed", ""),
                    "observations": row.get("correction_observations", []),
                },
                "classification": {
                    "themes": row.get("correction_themes", []),
                    "origin": row.get("correction_origin", ""),
                    "predictability": row.get("correction_predictability", ""),
                },
            }

        return data

    def record_correction(self, data: dict) -> str:
        """Record a correction to Supabase."""
        skill_name = data["skill_name"]
        instinct_pattern = data["instinct_pattern"]
        corrected_pattern = data["corrected_pattern"]
        impact_level = data.get("impact_level", "structural")
        project = data.get("project", "")
        file = data.get("file", "")
        context = data.get("context", "")
        severity = data.get("severity", "") or impact_level
        themes = data.get("themes", "")
        origin = data.get("origin", "model-instinct")
        predictability = data.get("predictability", "medium")

        today = date.today().isoformat()
        theme_list = [t.strip() for t in themes.split(",") if t.strip()] if themes else []

        # Slugify
        slug_base = instinct_pattern.lower()[:60]
        slug = ""
        for ch in slug_base:
            if ch.isalnum():
                slug += ch
            elif ch in (" ", "_", "-"):
                if slug and slug[-1] != "-":
                    slug += "-"
        slug = slug.strip("-")
        if not slug:
            slug = skill_name
        decision_name = slug

        # Check if correction already exists
        resp = self._client.table("forge_decisions").select("*").eq("name", decision_name).execute()

        if resp.data:
            row = resp.data[0]
            total = (row.get("correction_total_observations", 0) or 0) + 1
            observations = row.get("correction_observations", []) or []
            observations.append({"date": today, "project": project, "file": file})

            self._client.table("forge_decisions").update({
                "correction_total_observations": total,
                "correction_last_observed": today,
                "correction_observations": observations,
                "last_observed": today,
            }).eq("name", decision_name).execute()

            return (
                f"Updated existing correction '{decision_name}' — "
                f"now at {total} observations."
            )

        # Determine applies_to from skill metadata
        skill_resp = self._client.table("forge_skills").select("relevance_tags").eq("name", skill_name).execute()
        applies_to: list[str] = []
        if skill_resp.data:
            applies_to = (skill_resp.data[0].get("relevance_tags", []) or [])[:5]

        md_content = f"""# Decision: {decision_name}

## Summary

Claude's default instinct is to {instinct_pattern}. The skill `{skill_name}` corrects this to {corrected_pattern}.

## Context

{context or f"Observed while working on {project or 'a project'}."}

## Instinct Pattern (Before)

{instinct_pattern}

## Corrected Pattern (After)

{corrected_pattern}

## Reasoning

The corrected pattern follows the guidelines established in the `{skill_name}` skill. The instinct pattern was identified as a {origin.replace('-', ' ')} that impacts code at the {impact_level} level.

## Observations

| Date | Project | File | Notes |
|------|---------|------|-------|
| {today} | {project or 'unknown'} | {file or 'unknown'} | Initial observation |
"""

        self._client.table("forge_decisions").insert({
            "name": decision_name,
            "version": "0.1.0",
            "type": "correction",
            "status": "active",
            "severity": severity,
            "description": f"Correction: {instinct_pattern[:80]}",
            "created_date": today,
            "last_observed": today,
            "category": "corrections",
            "context_applies_to": applies_to,
            "context_profiles": ["rtg-default"],
            "context_trigger": instinct_pattern,
            "choice_chosen": corrected_pattern,
            "choice_rejected": [
                {"option": instinct_pattern, "reason": f"Corrected by skill {skill_name}"},
            ],
            "evidence_skills": [skill_name],
            "evidence_modules": [],
            "evidence_related_decisions": [],
            "correction_skill_applied": skill_name,
            "correction_instinct_pattern": instinct_pattern,
            "correction_corrected_pattern": corrected_pattern,
            "correction_impact_level": impact_level,
            "correction_total_observations": 1,
            "correction_first_observed": today,
            "correction_last_observed": today,
            "correction_observations": [
                {"date": today, "project": project, "file": file},
            ],
            "correction_themes": theme_list,
            "correction_origin": origin,
            "correction_predictability": predictability,
            "decision_md": md_content,
        }).execute()

        return (
            f"Created new correction '{decision_name}' in Supabase. "
            f"Skill: {skill_name}, Impact: {impact_level}."
        )

    # -- Validation --

    def validate_module_files(self, name: str) -> dict | None:
        """In cloud mode, we can only check that the module exists."""
        resp = self._client.table("forge_modules").select("name").eq("name", name).execute()
        if not resp.data:
            return None
        # All files are in the DB, so we report pass for content-backed checks
        checks: dict[str, str] = {}
        for fname in ["module.toml", "MODULE.md"]:
            checks[fname] = "pass"
        # Can't validate filesystem files in cloud mode
        for fname in ["__init__.py", "router.py", "service.py", "models.py", "config.py"]:
            checks[fname] = "N/A (cloud mode)"
        for dname in ["migrations/", "tests/"]:
            checks[dname] = "N/A (cloud mode)"
        return checks


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_backend() -> ForgeBackend:
    """Return the configured backend based on FORGE_BACKEND env var."""
    backend_type = os.environ.get("FORGE_BACKEND", "file").lower()
    if backend_type == "supabase":
        return SupabaseBackend()
    return FileBackend()
