# Extract Module to RTG Forge

Extract a reusable pattern from the current codebase into the rtg-forge module registry.

## Prerequisites
Run `/prepare-module` first if you don't know which files make up the module. It will search the codebase and produce a Module Map.

## Steps
1. If no Module Map exists yet, run the discovery process:
   - Ask the user to describe what the module does
   - Search the codebase for relevant files (routes, services, models, graphs, migrations, configs, tests)
   - Present the Module Map for confirmation
2. Analyze dependencies (imports, configs, DB tables, external services)
3. Create module directory under /Users/matt/rtg-forge/modules/{name}/
4. Extract and restructure into contract files:
   - `router.py` — FastAPI APIRouter with all endpoints
   - `service.py` — Business logic (NO FastAPI imports)
   - `models.py` — Pydantic request/response schemas
   - `config.py` — Module config extending CoreConfig from rtg_core
   - `graph/` — LangGraph pipeline (if module uses AI)
   - `migrations/` — SQL migration files, numbered sequentially
5. Write MODULE.md following the template:
   - What It Does, When To Use It, When NOT To Use It
   - Architecture (flow diagram), Setup, API Reference, Gotchas, Examples
6. Write module.toml with all sections including [ai] (use_when, input_summary, output_summary, complexity)
7. Create __init__.py with ModuleInfo dataclass export
8. Write contract tests in tests/ (imports work, router mounts, models validate)
9. Validate: check all required files exist per /Users/matt/rtg-forge/modules/MODULE_CONTRACT.md
10. Commit directly to main in rtg-forge, push, and notify:
    - Stage all new module files: `git add modules/{name}/`
    - Commit to main with message: "Add {name} module — {short description}"
    - Push to origin: `git push`
    - Send a Slack notification to #forge (channel ID: C0AEEF9UM1D) using the Slack MCP tool:
      "🧱 New forge module: *{module_name}* v{version}
      _{description}_
      Category: {category} | Tables: {tables} | Status: {status}
      Added by: {author}"

## The Forge Module Contract
Required files: module.toml, MODULE.md, __init__.py, router.py, service.py, models.py, config.py, migrations/, tests/
See /Users/matt/rtg-forge/modules/MODULE_CONTRACT.md for full details.

## Arguments
Module name: $ARGUMENTS
