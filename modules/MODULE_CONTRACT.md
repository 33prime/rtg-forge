# RTG Forge Module Contract

Every module in RTG Forge MUST adhere to this contract. This document defines the required structure, files, and conventions that make modules discoverable, testable, and composable.

---

## Required Files

### 1. `module.toml` -- Machine Manifest

The machine-readable manifest that declares the module's identity, dependencies, API surface, database requirements, and AI metadata.

**Required sections:**

| Section | Purpose |
|---------|---------|
| `[module]` | Name, version, description, status (`stable`, `beta`, `experimental`), category, author |
| `[module.dependencies]` | Python packages, external services, and other RTG modules this depends on |
| `[module.api]` | URL prefix and auth requirements |
| `[module.database]` | Table names and RLS requirements |
| `[ai]` | When to use this module, input/output summaries, complexity, setup time, related modules |
| `[health]` | Last validated date, test coverage percentage, known issues |

### 2. `MODULE.md` -- Human + AI Documentation

Structured documentation that serves both human developers and AI agents. Must include these sections:

- **What It Does** -- One-paragraph summary of the module's purpose
- **When To Use It** -- Bullet list of appropriate use cases
- **When NOT To Use It** -- Bullet list of anti-patterns and inappropriate use cases
- **Architecture** -- Description of internal structure, data flow, pipeline nodes (if applicable)
- **Setup** -- Environment variables, migrations, configuration steps
- **API Reference** -- All endpoints with methods, paths, request/response schemas
- **Gotchas** -- Known limitations, rate limits, cost considerations
- **Examples** -- Complete curl or code examples for primary workflows

### 3. `__init__.py` -- Module Exports

Must export a `module_info` instance of the `ModuleInfo` dataclass. This is the primary entry point for module discovery and registration.

```python
from dataclasses import dataclass
from fastapi import APIRouter

@dataclass
class ModuleInfo:
    name: str          # Unique module identifier (snake_case)
    version: str       # Semantic version (e.g., "0.1.0")
    description: str   # One-line description
    router: APIRouter  # FastAPI router with all endpoints
    prefix: str        # URL prefix (e.g., "/api/v1/enrichment")
    tags: list[str]    # OpenAPI tags for grouping
```

**Example:**

```python
from .router import router

module_info = ModuleInfo(
    name="stakeholder_enrichment",
    version="0.1.0",
    description="Multi-source stakeholder profile enrichment with AI synthesis",
    router=router,
    prefix="/api/v1/enrichment",
    tags=["enrichment"],
)
```

### 4. `router.py` -- FastAPI APIRouter

Contains the FastAPI `APIRouter` instance with all endpoint definitions. Rules:

- Use `APIRouter()` (not `FastAPI()`)
- All endpoints are relative to the module's prefix (defined in `module.toml` and `ModuleInfo`)
- Use `Depends()` for service injection
- Use proper HTTP status codes (201 for creation, 404 for not found, etc.)
- Use Pydantic response models for all endpoints

### 5. `service.py` -- Business Logic

Contains all business logic. Rules:

- **No FastAPI imports allowed.** This file must be framework-agnostic.
- Use plain Python classes and functions
- Accept and return Pydantic models or standard Python types
- Handle errors by raising domain-specific exceptions
- Include full type hints and docstrings on all public methods

### 6. `models.py` -- Pydantic Schemas

Contains all Pydantic models for:

- Request bodies
- Response bodies
- Internal data transfer objects
- Database row representations

All models must use `pydantic.BaseModel` with proper field types, validators, and descriptions.

### 7. `config.py` -- Module Configuration

Extends `CoreConfig` from `rtg_core` to add module-specific settings. Uses Pydantic Settings with environment variable support.

```python
from rtg_core.config import CoreConfig

class MyModuleConfig(CoreConfig):
    my_setting: int = 10
    model_config = {"env_prefix": "MY_MODULE_", "env_file": ".env", "extra": "ignore"}
```

### 8. `migrations/` -- SQL Migration Files

Directory containing numbered SQL migration files:

- Files are numbered sequentially: `001_create_tables.sql`, `002_add_indexes.sql`, etc.
- Each file contains idempotent SQL (use `IF NOT EXISTS` where possible)
- All tables MUST have RLS enabled
- All tables MUST have `created_at timestamptz default now()`
- Foreign keys must specify `ON DELETE` behavior

### 9. `tests/` -- Test Suite

Directory containing test files. Minimum requirement:

- `__init__.py` (can be empty)
- `test_contract.py` -- Contract tests that verify the module adheres to this contract:
  - Module exports `ModuleInfo` with all required fields
  - Router has the expected routes
  - Models validate correctly
  - Config can be instantiated

Additional recommended test files:

- `test_service.py` -- Unit tests for business logic
- `test_router.py` -- Integration tests for API endpoints
- `test_models.py` -- Validation edge cases

---

## Optional Files

### `graph/` -- LangGraph Pipeline

For modules that use LangGraph for AI orchestration:

- `graph.py` -- Graph definition with nodes and edges
- `nodes.py` -- Individual node functions
- `state.py` -- TypedDict or Pydantic model for graph state

### `pyproject.toml` -- Package Metadata

If the module is independently installable, include a `pyproject.toml` with dependencies.

---

## Module Registration

Modules are discovered and registered by the core application. The core scans the `modules/` directory, imports each module's `__init__.py`, reads the `module_info` attribute, and mounts the router at the specified prefix.

```python
# Core application registration (simplified)
from importlib import import_module

def register_module(module_path: str, app: FastAPI):
    mod = import_module(module_path)
    info = mod.module_info
    app.include_router(info.router, prefix=info.prefix, tags=info.tags)
```

---

## Conventions

1. **Naming**: Module directories use `snake_case`. Module names in `module.toml` match the directory name.
2. **Versioning**: Use semantic versioning. Bump minor for new features, patch for fixes.
3. **Status lifecycle**: `experimental` -> `beta` -> `stable` -> `deprecated`
4. **Error handling**: Raise domain exceptions in `service.py`; convert to HTTP errors in `router.py`.
5. **Database**: All tables are prefixed implicitly by their module context. Use RLS on every table.
6. **AI metadata**: The `[ai]` section in `module.toml` helps AI agents decide when and how to use the module.
