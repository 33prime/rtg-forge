# RTG Default Stack

## Overview

RTG builds AI-powered B2B SaaS tools using a modern Python + TypeScript stack. The architecture follows a clear separation: Python handles the API layer and AI orchestration, TypeScript powers the frontend SPA, and Supabase provides the entire backend-as-a-service layer (database, auth, storage, realtime).

This stack is optimized for small teams shipping AI-heavy products quickly. Every technology choice prioritizes developer velocity, operational simplicity, and AI-native patterns.

---

## Core Technologies

| Technology | Version | Role | Notes |
|---|---|---|---|
| Python | 3.12+ | API and AI backend | All server-side logic |
| FastAPI | Latest | API framework | Async-first, Pydantic validation |
| Supabase (Postgres) | Latest | Database + Auth + Storage | Managed Postgres with built-in auth, storage, and realtime |
| Vite + React | React 18 | Frontend SPA | Fast dev server, optimized builds |
| TypeScript | 5.x | Frontend language | Strict mode enabled |
| Tailwind CSS | 3 | Styling | Utility-first, no custom CSS unless necessary |

---

## AI/ML Stack

| Technology | Role | Notes |
|---|---|---|
| Anthropic Claude | Primary LLM | Claude as the default model for all AI features |
| LangGraph | Pipeline orchestration | Stateful, graph-based AI workflows with cycles and branching |
| LangChain | Tools + chains | Used for tool calling, retrieval chains, and LLM integrations |
| Langfuse | Observability | Tracing, evaluation, prompt management, and cost tracking |

### AI Architecture Principles

- Use LangGraph for any multi-step AI workflow. Do not hand-roll state machines.
- Instrument every LLM call with Langfuse tracing from day one.
- Prefer tool-calling patterns over free-form text parsing.
- Store prompts in version-controlled files, not in database rows.

---

## Infrastructure

| Service | Role | Notes |
|---|---|---|
| Railway | API hosting | Deploys FastAPI containers from Dockerfile |
| Netlify | Frontend hosting | Deploys Vite builds from git push |
| Supabase | DB + Auth + Storage | Managed Postgres, Row Level Security, S3-compatible storage |
| Upstash QStash | Message queues | HTTP-based async job queue for background tasks |

### Infrastructure Principles

- No self-managed servers. Everything is managed/serverless.
- Railway for anything that needs a long-running process.
- Netlify for static frontends with edge functions if needed.
- Supabase handles auth -- do not build custom auth.

---

## Development Tools

| Tool | Purpose | Notes |
|---|---|---|
| uv | Python package management | Fast, replaces pip + pip-tools + virtualenv |
| pnpm | Node package management | Fast, disk-efficient, strict by default |
| ruff | Python linting + formatting | Replaces black + isort + flake8 + pylint |
| pytest | Python testing | With pytest-asyncio for async tests |
| vitest | Frontend testing | Vite-native, fast, Jest-compatible API |
| pre-commit | Git hooks | Runs ruff, type checks, and tests before commit |

### Development Principles

- Use `uv` for all Python dependency management. Do not use pip directly.
- Use `pnpm` for all Node dependency management. Do not use npm or yarn.
- Ruff is the single Python linting and formatting tool. No exceptions.
- All code must pass `ruff check` and `ruff format --check` before merge.

---

## Key Decisions

### No ORM

We use raw SQL via the Supabase client libraries (Python `supabase-py`, TypeScript `@supabase/supabase-js`). No SQLAlchemy, no Prisma, no Drizzle.

**Why:** ORMs add abstraction that fights Postgres. Supabase's client gives us a query builder that maps cleanly to SQL. Row Level Security policies live in the database, not in application code. Migrations are plain SQL files managed through Supabase CLI.

### No SSR Framework

We use Vite + React as a single-page application. No Next.js, no Nuxt, no Remix.

**Why:** Our products are B2B dashboards and tools behind authentication. SEO is irrelevant. SSR adds deployment complexity (Node server) that we avoid by serving static builds from Netlify. API calls go directly to FastAPI.

### TOML for Configuration

All configuration files use TOML format. No YAML, no JSON for config.

**Why:** TOML is unambiguous, has a clear spec, supports comments, and is native to Python tooling (pyproject.toml, ruff.toml). It avoids YAML's footguns (Norway problem, implicit typing) and JSON's lack of comments.

### Copy-Paste Modules, Not Packages

Shared code is distributed as copy-paste modules within RTG Forge, not as published pip/npm packages.

**Why:** Internal packages create versioning hell for small teams. Copy-paste modules can be customized per project, reviewed in full, and don't require package registry infrastructure. When a module improves, you pull the update and review the diff.

---

## Gotchas

### Supabase

- **RLS is on by default.** If a query returns empty results unexpectedly, check that Row Level Security policies are configured for the table and the user's role.
- **Service role key bypasses RLS.** Never expose the service role key to the frontend. Use it only in server-side code.
- **Realtime requires explicit enable.** Tables do not broadcast changes until you enable realtime in the Supabase dashboard or via migration.
- **Storage policies are separate from table RLS.** Configuring table access does not automatically grant storage bucket access.

### FastAPI

- **Async endpoints need async DB calls.** Do not use synchronous Supabase calls inside `async def` endpoints -- it blocks the event loop. Use `httpx` or run sync calls in a thread pool.
- **Pydantic V2 is the default.** FastAPI now uses Pydantic V2. Do not use Pydantic V1 patterns (`class Config`, `.dict()`). Use `model_config` and `.model_dump()`.
- **Dependency injection for auth.** Use FastAPI `Depends()` for auth verification, not middleware. This gives you per-route control.

### React + Vite

- **Environment variables must start with `VITE_`.** Any env var not prefixed with `VITE_` is invisible to the frontend build.
- **No `process.env` in Vite.** Use `import.meta.env.VITE_MY_VAR` instead.
- **React 18 strict mode double-renders in dev.** Effects fire twice in development. This is intentional. Do not "fix" it by removing StrictMode.

### LangGraph

- **State must be serializable.** Everything in graph state must be JSON-serializable. No Python objects, no database connections in state.
- **Checkpointing needs a store.** If you want graph persistence or human-in-the-loop, configure a checkpoint store (Postgres via Supabase is the default choice).
- **Streaming requires async generators.** Use `astream_events` for real-time token streaming to the frontend.

### Deployment

- **Railway sleeps free-tier services.** If response times spike after idle periods, the service is waking from sleep. Use a paid plan or a health check ping for production.
- **Netlify build minutes are shared.** Large frontend builds eat into the team's monthly quota. Keep builds lean and cache aggressively.
- **Supabase connection limits.** Free tier has limited connections. Use connection pooling (Supavisor) in production and do not open connections per request.
