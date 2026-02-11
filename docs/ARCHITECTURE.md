# RTG Forge Architecture

## Overview

RTG Forge is an AI-native monorepo containing five interconnected systems that work together to provide reusable backend modules, living coding standards, and intelligent self-maintenance.

```
┌─────────────────────────────────────────────────────────────┐
│                     Forge Explorer (UI)                      │
│                  Vite + React + TypeScript                    │
└─────────────┬───────────────────────────────┬───────────────┘
              │ reads JSON indexes             │ (Phase 3: API)
              ▼                                ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│    MCP Server        │         │      Forge API              │
│    (FastMCP)         │         │      (FastAPI)              │
└──────────┬──────────┘         └──────────────┬──────────────┘
           │                                    │
           ▼                                    ▼
┌──────────────────────────────────────────────────────────────┐
│                        Core Package                           │
│   config · db · module_loader · profile_loader · models       │
│   auth · errors · toml_utils                                  │
└──────┬──────────┬──────────────┬──────────────┬──────────────┘
       │          │              │              │
       ▼          ▼              ▼              ▼
   Modules     Skills       Profiles     Intelligence
```

## System Breakdown

### 1. Module Registry (`modules/`)

Backend modules are self-contained FastAPI applications with standardized contracts. Each module directory contains:

- `module.toml` — Machine-readable manifest with dependencies, API config, and AI metadata
- `MODULE.md` — Human+AI documentation
- `router.py` — FastAPI router with endpoints
- `service.py` — Business logic (no framework imports)
- `models.py` — Pydantic request/response schemas
- `config.py` — Environment-based configuration
- `migrations/` — SQL migration files
- `tests/` — Contract and integration tests

Modules are **copy-pasted into projects**, not installed as packages. This enables per-project customization while maintaining a canonical reference in the forge.

### 2. Skills Engine (`skills/`)

Skills are living AI coding standards organized into three tiers:

- **Foundation** — Core practices every project needs (error handling, testing, clean architecture)
- **Specialized** — Technology-specific patterns (FastAPI, Supabase, React, LangGraph)
- **Workflow** — Multi-step processes (module extraction, code review, parallel execution)

Each skill has a `SKILL.md` (what Claude Code reads) and `meta.toml` (machine metadata for ranking and resolution). Skills are resolved per-profile: profile-specific skills override global ones, and forbidden technologies are filtered out.

### 3. Stack Profiles (`profiles/`)

Profiles define technology constraints for a specific vendor ecosystem or project type. The `rtg-default` profile is the root — all others extend it.

Profile resolution is recursive: load profile → check `extends` → merge with base. Child values override parent values.

Constraints have three levels:
- **Required** — Must be present in the stack
- **Allowed** — May be used if needed
- **Forbidden** — Must not appear anywhere

### 4. Intelligence Layer (`intelligence/`)

Self-maintaining GitHub Actions that keep the forge healthy:

- **Skill Optimizer** (weekly) — Monitors upstream project releases, proposes skill updates via PR
- **Module Health Checker** (daily) — Validates module contracts, runs tests, reports issues
- **CI** (on PR) — Lint, test, type-check, validate all manifests

### 5. Forge Explorer (`explorer/`)

Read-only web UI built with Vite + React + TypeScript + Tailwind CSS. Dark mode only.

Phase 1: Static site reading from prebuild JSON indexes (generated from TOML/Markdown files).
Phase 3: Connected to live Forge API for real-time data.

## Core Package (`core/`)

Shared Python utilities imported by all other packages:

| Module | Purpose |
|---|---|
| `config.py` | Base configuration with pydantic-settings |
| `db.py` | Supabase client factory |
| `module_loader.py` | Module discovery and FastAPI mounting |
| `profile_loader.py` | Profile loading with recursive merging |
| `models.py` | Base Pydantic models with common config |
| `auth.py` | API key and JWT authentication dependencies |
| `errors.py` | Error hierarchy and exception handlers |
| `toml_utils.py` | TOML loading and validation |

## Access Layers

### MCP Server (`mcp-server/`)

FastMCP server providing tools, resources, and prompts for AI interaction. Supports stdio transport (Claude Code) and SSE (remote access).

### CLI (`cli/`)

Typer-based CLI for local operations: listing, validating, scaffolding, syncing skills.

### Claude Code Commands (`.claude/commands/`)

Slash commands for common forge workflows: `/add-module`, `/use-module`, `/sync-skills`, `/health-check`, `/optimize`.

## Data Flow

```
TOML + Markdown files (source of truth)
        │
        ├──► MCP Server (reads files directly)
        ├──► CLI (reads files directly)
        ├──► Prebuild script (generates JSON indexes)
        │         │
        │         ▼
        │    Explorer (reads JSON indexes)
        │
        └──► Intelligence Layer (reads + proposes changes via PR)
```

## Key Decisions

1. **TOML over YAML** — Python ecosystem standard, no implicit type coercion
2. **Copy-paste modules** — Each project customizes its copy
3. **No ORM** — Raw SQL via Supabase client
4. **No SSR** — Vite SPA, not Next.js
5. **Profile-scoped everything** — MCP tools accept profile parameter
6. **Static Explorer first** — JSON indexes at build time, live API in Phase 3
