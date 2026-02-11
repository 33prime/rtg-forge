"""Tests for module discovery."""

from pathlib import Path

from rtg_core.module_loader import discover_modules


def test_discover_modules(tmp_path: Path):
    """Test that discover_modules finds module.toml files."""
    mod1 = tmp_path / "module_a"
    mod1.mkdir()
    (mod1 / "module.toml").write_text(
        '[module]\nname = "module_a"\nversion = "0.1.0"\ndescription = "Module A"\n'
    )

    mod2 = tmp_path / "module_b"
    mod2.mkdir()
    (mod2 / "module.toml").write_text(
        '[module]\nname = "module_b"\nversion = "0.1.0"\ndescription = "Module B"\n'
    )

    # Directory without module.toml should be skipped
    not_module = tmp_path / "not_a_module"
    not_module.mkdir()

    modules = discover_modules(tmp_path)
    assert len(modules) == 2
    names = [m["module"]["name"] for m in modules]
    assert "module_a" in names
    assert "module_b" in names


def test_discover_modules_empty_dir(tmp_path: Path):
    modules = discover_modules(tmp_path)
    assert modules == []


def test_discover_modules_nonexistent():
    modules = discover_modules(Path("/nonexistent"))
    assert modules == []
