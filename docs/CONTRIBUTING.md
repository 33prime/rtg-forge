# Contributing to RTG Forge

## Development Setup

```bash
# Clone the repo
git clone <repo-url> rtg-forge
cd rtg-forge

# Install Python dependencies
uv sync

# Install Node dependencies
pnpm install

# Run Python tests
uv run pytest

# Run Explorer tests
cd explorer && pnpm test
```

## Code Style

### Python

- **Formatter/Linter**: ruff (configured in root pyproject.toml)
- **Target**: Python 3.12+
- **Line length**: 100 characters
- **Style**: Type hints everywhere, dataclasses over dicts, small functions, explicit error handling

Run checks:
```bash
uv run ruff check .
uv run ruff format --check .
```

### TypeScript

- **Linter**: eslint
- **Formatter**: prettier
- **Target**: ES2022, strict mode
- **Style**: Functional components, proper interfaces (not `any`), named exports

Run checks:
```bash
cd explorer && pnpm lint && pnpm format
```

## Adding a Module

Every module must comply with `modules/MODULE_CONTRACT.md`. Required files:

| File | Purpose |
|---|---|
| `module.toml` | Machine manifest — name, version, deps, API config, AI metadata |
| `MODULE.md` | Human+AI docs — what, when, how, gotchas, examples |
| `__init__.py` | Exports `ModuleInfo` dataclass |
| `router.py` | FastAPI `APIRouter` with all endpoints |
| `service.py` | Business logic (no FastAPI imports) |
| `models.py` | Pydantic request/response schemas |
| `config.py` | Module config extending `CoreConfig` |
| `migrations/` | SQL migration files, numbered sequentially |
| `tests/` | Minimum: contract tests |

### Module Checklist

- [ ] `module.toml` has all required sections: `[module]`, `[module.dependencies]`, `[module.api]`, `[module.database]`, `[ai]`, `[health]`
- [ ] `MODULE.md` covers: What, When, When Not, Architecture, Setup, API Reference, Gotchas, Examples
- [ ] `__init__.py` exports `ModuleInfo` with correct prefix and tags
- [ ] `router.py` uses `Depends()` for service injection
- [ ] `service.py` has no FastAPI imports
- [ ] `models.py` uses Pydantic v2 BaseModel
- [ ] `config.py` extends `CoreConfig` with env prefix
- [ ] `migrations/` has numbered SQL files
- [ ] `tests/` has contract tests that verify exports, routes, and models
- [ ] `ruff check` passes
- [ ] `pytest` passes

## Adding a Skill

Every skill must comply with `skills/SKILL_CONTRACT.md`. Required files:

| File | Purpose |
|---|---|
| `SKILL.md` | The skill content that Claude Code reads |
| `meta.toml` | Machine metadata — name, tier, category, tags, relationships |
| `examples/good/` | At least one file showing correct patterns |
| `examples/bad/` | At least one file showing anti-patterns |

### Skill Tiers

- **Foundation** — Core practices everyone needs. Priority weight 85-95.
- **Specialized** — Technology-specific. Priority weight 75-90.
- **Workflow** — Multi-step processes. Priority weight 65-75.

### Skill Categories

- `stack/` — Technology-specific patterns (FastAPI, Supabase, React, etc.)
- `practices/` — Cross-cutting concerns (error handling, testing, API design)
- `workflows/` — Multi-step processes (module extraction, code review)

## Adding a Profile

Every profile must comply with `profiles/PROFILE_CONTRACT.md`. Required files:

| File | Purpose |
|---|---|
| `profile.toml` | Profile identity — name, maturity, vendor, extends |
| `STACK.md` | Tech stack reference document |
| `constraints.toml` | Required/allowed/forbidden technologies |

Start from the template:
```bash
cp -r profiles/_template profiles/my-profile
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all checks pass:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest
   cd explorer && pnpm lint && pnpm test
   ```
4. Write a clear PR description explaining what and why
5. The CI workflow will run: lint, test, type-check, and manifest validation

## Config Format

All configuration files use **TOML** (not YAML). Use `tomli` for reading and `tomli-w` for writing.

## File Naming

- Python: `snake_case.py`
- TypeScript components: `PascalCase.tsx`
- TypeScript utilities: `camelCase.ts`
- TOML configs: `snake_case.toml`
- Contract/reference docs: `UPPER_CASE.md`
- Skill/module/profile directories: `kebab-case`
