"""Tests for the RTG Forge MCP server tools and helpers.

Uses temporary forge directory structures to test scanning, searching,
and validation without depending on the real forge content.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# Import helpers and tools directly from server module
from forge_mcp.server import (
    _find_module,
    _find_profile,
    _find_skill,
    _get_forge_root,
    _keyword_score,
    _load_toml,
    _scan_modules,
    _scan_profiles,
    _scan_skills,
    get_module,
    get_skill,
    list_modules,
    list_profiles,
    list_skills,
    recommend_skills,
    search_modules,
    validate_module,
)


# ---------------------------------------------------------------------------
# Fixtures — create temp forge structures
# ---------------------------------------------------------------------------


@pytest.fixture()
def forge_root(tmp_path: Path) -> Path:
    """Create a minimal forge directory structure for testing."""
    root = tmp_path / "forge"
    root.mkdir()
    (root / "forge.toml").write_text('[forge]\nname = "test-forge"\n')

    # --- Module: test_module ---
    mod_dir = root / "modules" / "test_module"
    mod_dir.mkdir(parents=True)

    (mod_dir / "module.toml").write_text(
        '[module]\n'
        'name = "test_module"\n'
        'version = "0.1.0"\n'
        'description = "A test module for enrichment"\n'
        'status = "stable"\n'
        'category = "enrichment"\n'
        '\n'
        '[module.dependencies]\n'
        'python = ["httpx"]\n'
        'services = ["supabase"]\n'
        'modules = []\n'
        '\n'
        '[ai]\n'
        'use_when = "Need to enrich stakeholder profiles from LinkedIn"\n'
        'input_summary = "LinkedIn URL"\n'
        'output_summary = "Structured profile with AI synthesis"\n'
        'complexity = "high"\n'
        'estimated_setup_minutes = 30\n'
        'related_modules = []\n'
    )

    (mod_dir / "MODULE.md").write_text(
        "# Test Module\n\n"
        "## Overview\n\nA test module.\n\n"
        "## Setup\n\nInstall dependencies and configure env vars.\n\n"
        "## API Reference\n\nGET /api/v1/test\n"
    )
    (mod_dir / "__init__.py").write_text("")
    (mod_dir / "router.py").write_text("")
    (mod_dir / "service.py").write_text("")
    (mod_dir / "models.py").write_text("")
    (mod_dir / "config.py").write_text("")
    (mod_dir / "migrations").mkdir()
    (mod_dir / "tests").mkdir()
    (mod_dir / "tests" / "__init__.py").write_text("")

    # --- Module: analytics (different category) ---
    analytics_dir = root / "modules" / "analytics"
    analytics_dir.mkdir(parents=True)

    (analytics_dir / "module.toml").write_text(
        '[module]\n'
        'name = "analytics"\n'
        'version = "0.1.0"\n'
        'description = "Analytics dashboard module"\n'
        'status = "draft"\n'
        'category = "reporting"\n'
        '\n'
        '[module.dependencies]\n'
        'python = []\n'
        'services = []\n'
        'modules = []\n'
        '\n'
        '[ai]\n'
        'use_when = "Need to build analytics dashboards"\n'
        'input_summary = "Raw event data"\n'
        'output_summary = "Dashboard metrics and charts"\n'
        'complexity = "medium"\n'
    )
    (analytics_dir / "MODULE.md").write_text("# Analytics\n\nAnalytics module.\n")
    # Intentionally incomplete — missing some contract files

    # --- Skill: python-patterns ---
    skill_dir = root / "skills" / "stack" / "python-patterns"
    skill_dir.mkdir(parents=True)

    (skill_dir / "meta.toml").write_text(
        '[skill]\n'
        'name = "python-patterns"\n'
        'version = "0.1.0"\n'
        'tier = "foundation"\n'
        'category = "stack"\n'
        'relevance_tags = ["python", "backend", "architecture", "clean-code"]\n'
        'priority_weight = 95\n'
        'description = "Python clean code patterns for backend development"\n'
        '\n'
        '[relationships]\n'
        'prerequisites = []\n'
        'complements = ["testing-strategy"]\n'
        'supersedes = []\n'
        '\n'
        '[tracking]\n'
        'common_mistakes = ["Using bare except"]\n'
    )
    (skill_dir / "SKILL.md").write_text(
        "# Python Patterns\n\nClean code patterns for Python.\n"
    )

    # --- Skill: react-patterns (different category) ---
    react_dir = root / "skills" / "stack" / "react-patterns"
    react_dir.mkdir(parents=True)

    (react_dir / "meta.toml").write_text(
        '[skill]\n'
        'name = "react-patterns"\n'
        'version = "0.1.0"\n'
        'tier = "applied"\n'
        'category = "stack"\n'
        'relevance_tags = ["react", "frontend", "typescript", "components"]\n'
        'priority_weight = 80\n'
        'description = "React component patterns with TypeScript"\n'
        '\n'
        '[relationships]\n'
        'prerequisites = []\n'
        'complements = []\n'
        'supersedes = []\n'
    )
    (react_dir / "SKILL.md").write_text(
        "# React Patterns\n\nReact component patterns.\n"
    )

    # --- Skill: testing-strategy (practices category) ---
    testing_dir = root / "skills" / "practices" / "testing-strategy"
    testing_dir.mkdir(parents=True)

    (testing_dir / "meta.toml").write_text(
        '[skill]\n'
        'name = "testing-strategy"\n'
        'version = "0.1.0"\n'
        'tier = "foundation"\n'
        'category = "practices"\n'
        'relevance_tags = ["testing", "pytest", "quality", "backend"]\n'
        'priority_weight = 90\n'
        'description = "Testing strategy with pytest for backend services"\n'
        '\n'
        '[relationships]\n'
        'prerequisites = []\n'
        'complements = ["python-patterns"]\n'
        'supersedes = []\n'
    )
    (testing_dir / "SKILL.md").write_text(
        "# Testing Strategy\n\nPytest-based testing patterns.\n"
    )

    # --- Profile: test-profile ---
    prof_dir = root / "profiles" / "test-profile"
    prof_dir.mkdir(parents=True)

    (prof_dir / "profile.toml").write_text(
        '[profile]\n'
        'name = "test-profile"\n'
        'display_name = "Test Stack"\n'
        'version = "0.1.0"\n'
        'description = "A test technology stack"\n'
        'maturity = "production"\n'
        '\n'
        '[maintainer]\n'
        'team = "test"\n'
    )

    (prof_dir / "constraints.toml").write_text(
        '[constraints]\n'
        'description = "Test stack constraints"\n'
        '\n'
        '[constraints.required]\n'
        'database = { name = "Supabase (Postgres)", reason = "Core data layer" }\n'
        'api = { name = "FastAPI", reason = "Python API framework" }\n'
        '\n'
        '[constraints.allowed]\n'
        'hosting = ["railway", "render"]\n'
        '\n'
        '[constraints.forbidden]\n'
        'orm = ["sqlalchemy", "prisma"]\n'
        'database = ["mongodb", "dynamodb"]\n'
    )

    (prof_dir / "STACK.md").write_text(
        "# Test Stack\n\nThis is the test technology stack.\n"
    )

    return root


@pytest.fixture(autouse=True)
def _set_forge_root(forge_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set FORGE_ROOT env var to the temp forge directory for all tests."""
    monkeypatch.setenv("FORGE_ROOT", str(forge_root))


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelpers:
    """Tests for internal helper functions."""

    def test_get_forge_root_from_env(self, forge_root: Path) -> None:
        """FORGE_ROOT env var should be respected."""
        assert _get_forge_root() == forge_root

    def test_load_toml(self, forge_root: Path) -> None:
        """_load_toml should parse valid TOML files."""
        data = _load_toml(forge_root / "modules" / "test_module" / "module.toml")
        assert data["module"]["name"] == "test_module"
        assert data["module"]["status"] == "stable"

    def test_load_toml_missing_file(self, tmp_path: Path) -> None:
        """_load_toml should return empty dict for missing files."""
        data = _load_toml(tmp_path / "nonexistent.toml")
        assert data == {}

    def test_keyword_score(self) -> None:
        """_keyword_score should count matching words."""
        assert _keyword_score("python backend architecture", ["python", "backend"]) == 2
        assert _keyword_score("python backend architecture", ["react"]) == 0
        assert _keyword_score("Python Backend", ["python"]) == 1  # case insensitive

    def test_keyword_score_empty(self) -> None:
        """_keyword_score should handle empty inputs."""
        assert _keyword_score("", ["python"]) == 0
        assert _keyword_score("python", []) == 0


# ---------------------------------------------------------------------------
# Scanner tests
# ---------------------------------------------------------------------------


class TestScanners:
    """Tests for _scan_modules, _scan_skills, _scan_profiles."""

    def test_scan_modules(self, forge_root: Path) -> None:
        """Should find all modules with module.toml."""
        modules = _scan_modules(forge_root)
        names = [m["_name"] for m in modules]
        assert "test_module" in names
        assert "analytics" in names
        assert len(modules) == 2

    def test_scan_modules_returns_metadata(self, forge_root: Path) -> None:
        """Scanned modules should contain parsed TOML data."""
        modules = _scan_modules(forge_root)
        test_mod = next(m for m in modules if m["_name"] == "test_module")
        assert test_mod["module"]["status"] == "stable"
        assert test_mod["module"]["category"] == "enrichment"

    def test_scan_skills(self, forge_root: Path) -> None:
        """Should find all skills across category directories."""
        skills = _scan_skills(forge_root)
        names = [s["_name"] for s in skills]
        assert "python-patterns" in names
        assert "react-patterns" in names
        assert "testing-strategy" in names
        assert len(skills) == 3

    def test_scan_skills_preserves_category(self, forge_root: Path) -> None:
        """Scanned skills should track their category directory."""
        skills = _scan_skills(forge_root)
        testing = next(s for s in skills if s["_name"] == "testing-strategy")
        assert testing["_category_dir"] == "practices"

    def test_scan_profiles(self, forge_root: Path) -> None:
        """Should find all profiles with profile.toml."""
        profiles = _scan_profiles(forge_root)
        names = [p["_name"] for p in profiles]
        assert "test-profile" in names
        assert len(profiles) == 1

    def test_scan_modules_empty_dir(self, tmp_path: Path) -> None:
        """Should return empty list for missing modules directory."""
        empty_root = tmp_path / "empty"
        empty_root.mkdir()
        assert _scan_modules(empty_root) == []


# ---------------------------------------------------------------------------
# Module tool tests
# ---------------------------------------------------------------------------


class TestModuleTools:
    """Tests for module-related tools."""

    def test_list_modules(self) -> None:
        """list_modules should return markdown with module names."""
        result = list_modules()
        assert "test_module" in result
        assert "analytics" in result
        assert "enrichment" in result

    def test_list_modules_filter_category(self) -> None:
        """list_modules with category filter should only return matching modules."""
        result = list_modules(category="enrichment")
        assert "test_module" in result
        assert "analytics" not in result

    def test_list_modules_empty_category(self) -> None:
        """list_modules with non-matching category should return no modules."""
        result = list_modules(category="nonexistent")
        assert "No modules found." in result

    def test_get_module(self) -> None:
        """get_module should return MODULE.md content and metadata."""
        result = get_module("test_module")
        assert "test_module" in result
        assert "stable" in result
        assert "enrichment" in result
        # MODULE.md content
        assert "Test Module" in result
        assert "Setup" in result

    def test_get_module_not_found(self) -> None:
        """get_module for nonexistent module should return not found."""
        result = get_module("nonexistent_module")
        assert "not found" in result.lower()

    def test_get_module_includes_ai_metadata(self) -> None:
        """get_module should include the [ai] section data."""
        result = get_module("test_module")
        assert "LinkedIn" in result
        assert "Use when" in result
        assert "high" in result  # complexity

    def test_search_modules(self) -> None:
        """search_modules should find modules matching query words."""
        result = search_modules("enrichment stakeholder")
        assert "test_module" in result

    def test_search_modules_by_ai_fields(self) -> None:
        """search_modules should match against [ai] section fields."""
        result = search_modules("LinkedIn")
        assert "test_module" in result

    def test_search_modules_by_description(self) -> None:
        """search_modules should match against module description."""
        result = search_modules("dashboard")
        assert "analytics" in result

    def test_search_modules_no_match(self) -> None:
        """search_modules with unmatched query should return no results."""
        result = search_modules("zzz_nonexistent_xyz")
        assert "No modules matched" in result

    def test_validate_module_complete(self) -> None:
        """validate_module on complete module should pass all checks."""
        result = validate_module("test_module")
        assert "PASS" in result
        # All files should show pass
        assert "FAIL" not in result or result.count("PASS") > 0

    def test_validate_module_incomplete(self) -> None:
        """validate_module on incomplete module should report failures."""
        result = validate_module("analytics")
        assert "FAIL" in result
        # analytics is missing router.py, service.py, etc.

    def test_validate_module_not_found(self) -> None:
        """validate_module on nonexistent module should report error."""
        result = validate_module("nonexistent_module")
        assert "does not exist" in result


# ---------------------------------------------------------------------------
# Skill tool tests
# ---------------------------------------------------------------------------


class TestSkillTools:
    """Tests for skill-related tools."""

    def test_list_skills(self) -> None:
        """list_skills should return markdown with all skills."""
        result = list_skills()
        assert "python-patterns" in result
        assert "react-patterns" in result
        assert "testing-strategy" in result

    def test_list_skills_filter_tier(self) -> None:
        """list_skills with tier filter should only return matching skills."""
        result = list_skills(tier="foundation")
        assert "python-patterns" in result
        assert "testing-strategy" in result
        assert "react-patterns" not in result

    def test_list_skills_includes_weight(self) -> None:
        """list_skills should show priority_weight."""
        result = list_skills()
        assert "95" in result  # python-patterns weight
        assert "80" in result  # react-patterns weight

    def test_get_skill(self) -> None:
        """get_skill should return SKILL.md content and metadata."""
        result = get_skill("python-patterns")
        assert "python-patterns" in result
        assert "foundation" in result
        assert "Python Patterns" in result  # from SKILL.md
        assert "Clean code patterns" in result

    def test_get_skill_not_found(self) -> None:
        """get_skill for nonexistent skill should return not found."""
        result = get_skill("nonexistent_skill")
        assert "not found" in result.lower()

    def test_get_skill_includes_relationships(self) -> None:
        """get_skill should include relationship data."""
        result = get_skill("python-patterns")
        assert "testing-strategy" in result  # complements

    def test_get_skill_includes_common_mistakes(self) -> None:
        """get_skill should include common mistakes from tracking."""
        result = get_skill("python-patterns")
        assert "bare except" in result

    def test_recommend_skills(self) -> None:
        """recommend_skills should rank skills by relevance."""
        result = recommend_skills("python backend testing")
        # python-patterns and testing-strategy should rank high
        assert "python-patterns" in result
        assert "testing-strategy" in result

    def test_recommend_skills_ranking(self) -> None:
        """recommend_skills should rank by match_count * priority_weight."""
        result = recommend_skills("python backend")
        lines = result.strip().split("\n")
        # python-patterns should be #1 since it matches "python" and "backend"
        # with weight 95
        ranked_lines = [l for l in lines if l.startswith("1.")]
        assert len(ranked_lines) == 1
        assert "python-patterns" in ranked_lines[0]

    def test_recommend_skills_no_match(self) -> None:
        """recommend_skills with unmatched task should return no results."""
        result = recommend_skills("zzz_nonexistent_xyz")
        assert "No skills matched" in result


# ---------------------------------------------------------------------------
# Profile tool tests
# ---------------------------------------------------------------------------


class TestProfileTools:
    """Tests for profile-related tools."""

    def test_list_profiles(self) -> None:
        """list_profiles should return markdown with all profiles."""
        result = list_profiles()
        assert "Test Stack" in result
        assert "test-profile" in result
        assert "production" in result

    def test_list_profiles_includes_description(self) -> None:
        """list_profiles should include profile descriptions."""
        result = list_profiles()
        assert "test technology stack" in result.lower()
