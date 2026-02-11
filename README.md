# RTG Forge

AI-native module registry, skills engine, and intelligence platform.

## What Is This

RTG Forge is a monorepo containing five systems:

1. **Module Registry** — Reusable Python/FastAPI backend modules with standardized contracts
2. **Skills Engine** — Living AI coding standards (SKILL.md files) with metadata
3. **Stack Profiles** — Configurable technology constraints that scope the entire Forge to a vendor ecosystem
4. **Intelligence Layer** — GitHub Actions that auto-optimize skills and validate modules
5. **Forge Explorer** — Read-only Vite+React frontend to browse modules, skills, profiles, and components

Plus an MCP Server for AI access, a CLI for local operations, and Claude Code slash commands.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node package manager)
- Node.js 20+

### Setup

```bash
# Clone the repo
git clone <repo-url> rtg-forge
cd rtg-forge

# Install Python dependencies
uv sync

# Install Node dependencies
pnpm install

# Build the Explorer
cd explorer && pnpm build
```

### Project Structure

```
rtg-forge/
├── core/           # Shared Python utilities
├── modules/        # Backend modules (FastAPI routers)
├── skills/         # AI coding standards (SKILL.md files)
├── profiles/       # Stack profiles (technology constraints)
├── mcp-server/     # MCP interface for AI tools
├── cli/            # Local CLI tool
├── intelligence/   # Self-healing GitHub Actions agents
├── explorer/       # Forge Explorer frontend (Vite+React)
└── docs/           # Documentation
```

### Quick Commands

```bash
# List all modules
forge list modules

# Validate everything
forge validate all

# Run health checks
forge health

# Sync skills to local Claude Code
forge sync-skills --target ~/.claude/skills/
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Getting Started Guide](docs/GETTING_STARTED.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## License

MIT
