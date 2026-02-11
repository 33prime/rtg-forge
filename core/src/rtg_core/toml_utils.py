"""TOML loading and validation utilities."""

from pathlib import Path
from typing import Any

import tomli

from rtg_core.errors import ConfigError, ValidationError


def load_toml(path: Path | str) -> dict[str, Any]:
    """Load and parse a TOML file, returning its contents as a dict."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"TOML file not found: {path}")
    if not path.suffix == ".toml":
        raise ConfigError(f"Expected .toml file, got: {path}")
    try:
        with open(path, "rb") as f:
            return tomli.load(f)
    except tomli.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in {path}: {e}") from e


def validate_toml(
    data: dict[str, Any],
    required_keys: dict[str, type | list[type]],
    context: str = "",
) -> list[str]:
    """Validate a TOML dict has expected keys with correct types.

    Args:
        data: Parsed TOML data.
        required_keys: Mapping of dotted key paths to expected type(s).
            e.g. {"module.name": str, "module.version": str, "module.status": str}
        context: Description of what's being validated (for error messages).

    Returns:
        List of validation error strings. Empty list means valid.
    """
    errors = []
    for dotted_key, expected_types in required_keys.items():
        parts = dotted_key.split(".")
        current = data
        found = True
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                errors.append(f"Missing required key '{dotted_key}'{f' in {context}' if context else ''}")
                found = False
                break
            current = current[part]
        if found:
            if isinstance(expected_types, list):
                if not any(isinstance(current, t) for t in expected_types):
                    type_names = ", ".join(t.__name__ for t in expected_types)
                    errors.append(
                        f"Key '{dotted_key}' should be one of ({type_names}), "
                        f"got {type(current).__name__}"
                    )
            elif not isinstance(current, expected_types):
                errors.append(
                    f"Key '{dotted_key}' should be {expected_types.__name__}, "
                    f"got {type(current).__name__}"
                )
    if errors:
        raise ValidationError(
            f"TOML validation failed{f' for {context}' if context else ''}: "
            + "; ".join(errors)
        )
    return errors
