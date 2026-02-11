"""Tests for profile loading and validation."""

from pathlib import Path

import pytest

from rtg_core.errors import NotFoundError
from rtg_core.profile_loader import load_profile, validate_against_profile


@pytest.fixture
def profiles_dir(tmp_path: Path) -> Path:
    """Create a temporary profiles directory with a test profile."""
    profile_dir = tmp_path / "test-profile"
    profile_dir.mkdir()

    (profile_dir / "profile.toml").write_text(
        '[profile]\nname = "test-profile"\ndisplay_name = "Test Profile"\n'
        'version = "0.1.0"\ndescription = "A test profile"\n'
        'maturity = "seed"\n\n[base]\nextends = ""\n'
    )
    (profile_dir / "constraints.toml").write_text(
        "[constraints]\n"
        'description = "Test constraints"\n\n'
        "[constraints.required]\n"
        'database = { name = "Supabase (Postgres)", reason = "Core data" }\n\n'
        "[constraints.allowed]\n"
        'hosting = ["railway", "fly"]\n\n'
        "[constraints.forbidden]\n"
        'orm = ["sqlalchemy", "prisma"]\n'
    )
    (profile_dir / "STACK.md").write_text("# Test Stack\n\nThis is a test stack.\n")
    return tmp_path


def test_load_profile_success(profiles_dir: Path):
    profile = load_profile("test-profile", profiles_dir)
    assert profile["profile"]["name"] == "test-profile"
    assert profile["profile"]["display_name"] == "Test Profile"
    assert "Supabase" in profile["constraints"]["required"]["database"]["name"]
    assert "# Test Stack" in profile["stack_md"]


def test_load_profile_not_found(profiles_dir: Path):
    with pytest.raises(NotFoundError, match="Profile not found"):
        load_profile("nonexistent", profiles_dir)


def test_validate_against_profile_violations(profiles_dir: Path):
    profile = load_profile("test-profile", profiles_dir)
    result = validate_against_profile(["sqlalchemy", "fastapi"], profile)
    assert "sqlalchemy" in result["violations"]
    assert len(result["violations"]) == 1


def test_validate_against_profile_gaps(profiles_dir: Path):
    profile = load_profile("test-profile", profiles_dir)
    result = validate_against_profile(["fastapi"], profile)
    assert len(result["gaps"]) > 0  # Missing Supabase


def test_validate_against_profile_clean(profiles_dir: Path):
    profile = load_profile("test-profile", profiles_dir)
    result = validate_against_profile(["Supabase (Postgres)", "fastapi"], profile)
    assert result["violations"] == []
    assert result["gaps"] == []


@pytest.fixture
def extending_profiles_dir(tmp_path: Path) -> Path:
    """Profiles directory with a base and child profile."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "profile.toml").write_text(
        '[profile]\nname = "base"\nversion = "0.1.0"\n\n[base]\nextends = ""\n'
    )
    (base_dir / "constraints.toml").write_text(
        "[constraints]\n"
        "[constraints.required]\n"
        'database = { name = "Postgres", reason = "SQL" }\n'
        "[constraints.forbidden]\n"
        'orm = ["prisma"]\n'
    )
    (base_dir / "STACK.md").write_text("# Base Stack\n")

    child_dir = tmp_path / "child"
    child_dir.mkdir()
    (child_dir / "profile.toml").write_text(
        '[profile]\nname = "child"\nversion = "0.1.0"\n\n[base]\nextends = "base"\n'
    )
    (child_dir / "constraints.toml").write_text(
        "[constraints]\n"
        "[constraints.required]\n"
        'api = { name = "FastAPI", reason = "API framework" }\n'
        "[constraints.forbidden]\n"
        'css = ["emotion"]\n'
    )
    (child_dir / "STACK.md").write_text("# Child Stack\n")

    return tmp_path


def test_profile_extends_merges(extending_profiles_dir: Path):
    profile = load_profile("child", extending_profiles_dir)
    required = profile["constraints"]["required"]
    # Should have both base and child required techs
    assert "database" in required
    assert "api" in required
    # Child stack_md overrides base
    assert "# Child Stack" in profile["stack_md"]
