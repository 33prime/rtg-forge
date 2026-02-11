"""Tests for TOML loading and validation utilities."""

from pathlib import Path

import pytest

from rtg_core.errors import ConfigError, ValidationError
from rtg_core.toml_utils import load_toml, validate_toml


@pytest.fixture
def tmp_toml(tmp_path: Path) -> Path:
    toml_file = tmp_path / "test.toml"
    toml_file.write_text('[module]\nname = "test"\nversion = "0.1.0"\n')
    return toml_file


def test_load_toml_success(tmp_toml: Path):
    data = load_toml(tmp_toml)
    assert data["module"]["name"] == "test"
    assert data["module"]["version"] == "0.1.0"


def test_load_toml_not_found():
    with pytest.raises(ConfigError, match="not found"):
        load_toml(Path("/nonexistent/file.toml"))


def test_load_toml_wrong_extension(tmp_path: Path):
    wrong_file = tmp_path / "test.json"
    wrong_file.write_text("{}")
    with pytest.raises(ConfigError, match="Expected .toml"):
        load_toml(wrong_file)


def test_load_toml_invalid_syntax(tmp_path: Path):
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text("this is not [valid toml }{")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_toml(bad_file)


def test_validate_toml_success():
    data = {"module": {"name": "test", "version": "0.1.0"}}
    errors = validate_toml(data, {"module.name": str, "module.version": str})
    assert errors == []


def test_validate_toml_missing_key():
    data = {"module": {"name": "test"}}
    with pytest.raises(ValidationError, match="Missing required key"):
        validate_toml(data, {"module.name": str, "module.version": str})


def test_validate_toml_wrong_type():
    data = {"module": {"name": 42}}
    with pytest.raises(ValidationError, match="should be str"):
        validate_toml(data, {"module.name": str})


def test_validate_toml_multiple_types():
    data = {"value": "hello"}
    errors = validate_toml(data, {"value": [str, int]})
    assert errors == []

    data2 = {"value": 42}
    errors2 = validate_toml(data2, {"value": [str, int]})
    assert errors2 == []
