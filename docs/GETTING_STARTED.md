# Getting Started with RTG Forge

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [pnpm](https://pnpm.io/) — Node package manager
- Node.js 20+

## Initial Setup

### 1. Clone and Install

```bash
git clone <repo-url> rtg-forge
cd rtg-forge

# Install Python dependencies (all workspace packages)
uv sync

# Install Node dependencies (explorer)
pnpm install
```

### 2. Environment Variables

Create a `.env` file in the root:

```env
# Required for modules that use Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Required for AI-powered modules
ANTHROPIC_API_KEY=sk-ant-...

# MCP server (auto-detected if running from repo root)
FORGE_ROOT=/path/to/rtg-forge
```

### 3. Build the Explorer

```bash
cd explorer
pnpm run prebuild   # generates JSON indexes from repo data
pnpm run dev         # starts dev server at http://localhost:5173
```

## Using the Forge

### Browse with the Explorer

Open `http://localhost:5173` to browse:
- **Modules** — Reusable backend modules with docs and API references
- **Skills** — AI coding standards organized by tier and category
- **Profiles** — Technology constraint sets
- **Search** — Full-text search across everything (⌘K)

### Use with Claude Code (MCP Server)

Add the forge MCP server to your Claude Code config:

```json
{
  "mcpServers": {
    "rtg-forge": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/rtg-forge/mcp-server", "python", "-m", "forge_mcp.server"],
      "env": {
        "FORGE_ROOT": "/path/to/rtg-forge"
      }
    }
  }
}
```

Now Claude Code can:
- List and search modules
- Read module documentation and setup instructions
- Get skill recommendations for a task
- Validate technology choices against profiles

### Use the CLI

```bash
# List modules
uv run forge list modules

# Show module details
uv run forge show module stakeholder_enrichment

# Validate everything
uv run forge validate all

# Sync skills to local Claude Code
uv run forge sync-skills --target ~/.claude/skills/
```

### Use Slash Commands

From within Claude Code in the rtg-forge repo:

- `/add-module <name>` — Extract a reusable module from a codebase
- `/use-module <name>` — Integrate a forge module into a project
- `/sync-skills` — Pull latest skills from the forge
- `/health-check` — Validate modules and skills
- `/optimize <skill>` — Check for upstream updates to a skill

## Adding a New Module

1. Create the module directory:
   ```bash
   uv run forge new module my_module --category enrichment
   ```

2. Implement the contract files (see `modules/MODULE_CONTRACT.md`):
   - `module.toml` — Manifest
   - `MODULE.md` — Documentation
   - `router.py` — FastAPI endpoints
   - `service.py` — Business logic
   - `models.py` — Pydantic schemas
   - `config.py` — Configuration
   - `migrations/` — SQL files
   - `tests/` — Contract tests

3. Validate:
   ```bash
   uv run forge validate module my_module
   ```

## Adding a New Skill

1. Create the skill directory:
   ```bash
   uv run forge new skill my-skill --category practices --tier foundation
   ```

2. Write the content:
   - `SKILL.md` — The skill content Claude Code reads
   - `meta.toml` — Machine metadata
   - `examples/good/` — At least one correct pattern
   - `examples/bad/` — At least one anti-pattern

3. Validate:
   ```bash
   uv run forge validate skill my-skill
   ```

## Project Structure

```
rtg-forge/
├── core/           # Shared Python utilities
├── modules/        # Backend modules (FastAPI)
├── skills/         # AI coding standards
├── profiles/       # Technology constraints
├── mcp-server/     # MCP interface for AI tools
├── cli/            # Local CLI tool
├── intelligence/   # Self-healing GitHub Actions
├── explorer/       # Web UI (Vite + React)
└── docs/           # This documentation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.
