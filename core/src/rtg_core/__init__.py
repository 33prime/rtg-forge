"""RTG Forge Core — Shared utilities for all forge packages."""

from rtg_core.auth import get_api_key, get_current_user
from rtg_core.config import CoreConfig
from rtg_core.db import get_supabase_client
from rtg_core.errors import ConfigError, ForgeError, NotFoundError, ValidationError
from rtg_core.models import BaseModel, ProjectMixin, TimestampMixin
from rtg_core.module_loader import ModuleInfo, discover_modules, mount_modules
from rtg_core.profile_loader import load_profile, validate_against_profile
from rtg_core.toml_utils import load_toml, validate_toml

__all__ = [
    "CoreConfig",
    "get_supabase_client",
    "discover_modules",
    "mount_modules",
    "ModuleInfo",
    "load_profile",
    "validate_against_profile",
    "BaseModel",
    "TimestampMixin",
    "ProjectMixin",
    "get_api_key",
    "get_current_user",
    "ForgeError",
    "NotFoundError",
    "ValidationError",
    "ConfigError",
    "load_toml",
    "validate_toml",
]
