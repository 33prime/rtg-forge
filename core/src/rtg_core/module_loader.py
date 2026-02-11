"""Module discovery and mounting for FastAPI."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, FastAPI

from rtg_core.toml_utils import load_toml


@dataclass
class ModuleInfo:
    """Standard module info exported by every module's __init__.py."""

    name: str
    version: str
    description: str
    router: APIRouter
    prefix: str
    tags: list[str]


def discover_modules(path: Path | str) -> list[dict]:
    """Scan a directory for module.toml files and return module metadata.

    Args:
        path: Directory to scan (e.g., "modules/").

    Returns:
        List of dicts with module manifest data + directory path.
    """
    path = Path(path)
    modules = []
    if not path.is_dir():
        return modules
    for module_dir in sorted(path.iterdir()):
        manifest_path = module_dir / "module.toml"
        if module_dir.is_dir() and manifest_path.exists():
            data = load_toml(manifest_path)
            data["_path"] = str(module_dir)
            modules.append(data)
    return modules


def mount_modules(app: FastAPI, modules: list[ModuleInfo]) -> None:
    """Mount a list of ModuleInfo routers onto a FastAPI app."""
    for module in modules:
        app.include_router(
            module.router,
            prefix=module.prefix,
            tags=module.tags,
        )
