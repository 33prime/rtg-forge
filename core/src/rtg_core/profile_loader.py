"""Profile loading and technology validation."""

from pathlib import Path
from typing import Any

from rtg_core.errors import NotFoundError
from rtg_core.toml_utils import load_toml


def load_profile(name: str, profiles_dir: Path | str = "profiles") -> dict[str, Any]:
    """Load a profile by name, merging with base profile if extends is set.

    Args:
        name: Profile directory name (e.g., "rtg-default").
        profiles_dir: Root directory containing all profiles.

    Returns:
        Merged profile dict with keys: profile, constraints, stack_md.
    """
    profiles_dir = Path(profiles_dir)
    profile_dir = profiles_dir / name
    if not profile_dir.is_dir():
        raise NotFoundError(f"Profile not found: {name}")

    profile_toml = load_toml(profile_dir / "profile.toml")
    constraints_path = profile_dir / "constraints.toml"
    constraints = load_toml(constraints_path) if constraints_path.exists() else {}

    stack_md_path = profile_dir / "STACK.md"
    stack_md = stack_md_path.read_text() if stack_md_path.exists() else ""

    gotchas_path = profile_dir / "gotchas" / "GOTCHAS.md"
    gotchas_md = gotchas_path.read_text() if gotchas_path.exists() else ""

    result = {
        "profile": profile_toml.get("profile", {}),
        "constraints": constraints.get("constraints", {}),
        "stack_md": stack_md,
        "gotchas_md": gotchas_md,
        "_path": str(profile_dir),
    }

    # Merge with base profile if extends is set
    extends = profile_toml.get("base", {}).get("extends", "")
    if extends:
        base = load_profile(extends, profiles_dir)
        result = _merge_profiles(base, result)

    return result


def _merge_profiles(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override profile onto base. Override wins for overlapping keys."""
    merged = {**base}
    merged["profile"] = {**base.get("profile", {}), **override.get("profile", {})}

    base_constraints = base.get("constraints", {})
    override_constraints = override.get("constraints", {})
    merged_constraints = {**base_constraints}
    for key, value in override_constraints.items():
        if isinstance(value, dict) and isinstance(merged_constraints.get(key), dict):
            merged_constraints[key] = {**merged_constraints[key], **value}
        else:
            merged_constraints[key] = value
    merged["constraints"] = merged_constraints

    # Override stack_md and gotchas_md only if non-empty
    if override.get("stack_md"):
        merged["stack_md"] = override["stack_md"]
    if override.get("gotchas_md"):
        merged["gotchas_md"] = override["gotchas_md"]

    merged["_path"] = override["_path"]
    return merged


def validate_against_profile(
    technologies: list[str],
    profile: dict[str, Any],
) -> dict[str, list[str]]:
    """Check a list of technology names against profile constraints.

    Args:
        technologies: List of technology names to validate.
        profile: Loaded profile dict (from load_profile).

    Returns:
        Dict with 'violations' (using forbidden tech) and 'gaps' (missing required tech).
    """
    constraints = profile.get("constraints", {})
    forbidden = constraints.get("forbidden", {})
    required = constraints.get("required", {})

    # Flatten forbidden into a set of lowercase names
    forbidden_names = set()
    for _category, names in forbidden.items():
        if isinstance(names, list):
            forbidden_names.update(n.lower() for n in names)

    # Flatten required into a set of lowercase names
    required_names = set()
    for _category, info in required.items():
        if isinstance(info, dict) and "name" in info:
            required_names.add(info["name"].lower())

    tech_lower = [t.lower() for t in technologies]

    violations = [t for t in technologies if t.lower() in forbidden_names]
    gaps = [name for name in required_names if not any(name in t for t in tech_lower)]

    return {"violations": violations, "gaps": gaps}
