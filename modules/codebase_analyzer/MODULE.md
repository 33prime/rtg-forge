# Codebase Analyzer Module

## What It Does

Connects to a GitHub repository via API, reads key files and directory listings, then uses Claude to generate a structured codebase context document. The context document covers architecture, file registry, data models, patterns, feature checklists, and environment config. Supports two modes: full analysis (Sonnet, reads all key files) and incremental updates (Haiku, reads only files changed since last analysis). Results are persisted to Supabase with status tracking. The POST /refresh endpoint is fire-and-forget (background task).

## When To Use It

- **AI instruction generation** -- Feed the context document to Claude when generating implementation instructions so it understands the codebase structure.
- **Onboarding documentation** -- Auto-generate up-to-date codebase summaries for new team members.
- **Change tracking** -- Incremental mode detects what changed and patches the context efficiently.
- **Pre-meeting context** -- Refresh before planning sessions to ensure the AI has current codebase knowledge.

## When NOT To Use It

- **Real-time code search** -- This produces a summary document, not a search index. Use grep/ripgrep for code search.
- **Very large repos** -- Reads files sequentially via GitHub API. Repos with 100+ key files will be slow.
- **Without GitHub access** -- Requires a GitHub token with repo read access.
- **Sub-second responses** -- Full analysis takes ~30s, incremental ~10s. Not for real-time use.

## Architecture

```
POST /refresh (fire-and-forget)
    | BackgroundTask
    |
check for existing context (status=current)
    |
[existing found?]
    |               |
    YES             NO
    |               |
get commits         |
since last          |
    |               |
[code changed?]     |
    |       |       |
    YES     NO      |
    |       |       |
read only   return  read all KEY_FILES
changed     early   + KEY_DIRS
files               |
    |               |
    v               v
Claude Haiku    Claude Sonnet
(incremental)   (full analysis)
    |               |
    +-------+-------+
            |
    mark existing → stale
    store new → current
```

### Data Flow

| Step | Action | Details |
|------|--------|---------|
| 1 | Check existing | Query `codebase_context` for `status=current` |
| 2a | Full analysis | Read KEY_FILES + KEY_DIRS from GitHub, send to Sonnet |
| 2b | Incremental | Get commits since `generated_at`, read changed files, send to Haiku |
| 3 | Store result | Mark old rows `stale`, insert new row as `current` |

### Claude Synthesis

| Mode | Model | Max Tokens | Input |
|------|-------|------------|-------|
| Full | claude-sonnet-4 | 8192 | All key files + directory listings |
| Incremental | claude-haiku-4.5 | 8192 | Changed files + existing context |

## Setup

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with repo read access |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for synthesis |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `GITHUB_REPO_OWNER` | Yes | GitHub repository owner (e.g., "33prime") |
| `GITHUB_REPO_NAME` | Yes | GitHub repository name (e.g., "rtg2026site") |
| `CODEBASE_FULL_ANALYSIS_MODEL` | No | Claude model for full analysis (default: `claude-sonnet-4-20250514`) |
| `CODEBASE_INCREMENTAL_MODEL` | No | Claude model for incremental updates (default: `claude-haiku-4-5-20251001`) |

### Database

Run the migration to create the required table:

```bash
psql $DATABASE_URL -f modules/codebase_analyzer/migrations/001_create_tables.sql
```

## API Reference

### GET /api/v1/codebase-context

Returns the current codebase context document.

**Response (200):**
```json
{
  "content": "## 1. Architecture Overview\n...",
  "generated_at": "2026-02-11T12:00:00Z",
  "status": "current"
}
```

**Response (404):**
```json
{ "detail": "No codebase context found. Run a refresh first." }
```

### POST /api/v1/codebase-context/refresh

Trigger a codebase context refresh (runs in background).

**Response (200):**
```json
{
  "status": "accepted",
  "message": "Codebase context refresh started. Incremental updates take ~10s, full analysis ~30s."
}
```

## Gotchas

- **GitHub API rate limits**: Authenticated requests get 5,000/hour. A full analysis reads ~30 files + ~7 dir listings = ~40 API calls. Incremental reads fewer. Watch rate limits if refreshing frequently.
- **File truncation**: Files over 8,000 chars are truncated. Components are limited to first 80 lines. This keeps Claude context manageable but may miss details in very large files.
- **KEY_FILES/KEY_DIRS are project-specific**: The default lists target the RTG2026 project structure. For other projects, update these lists in service.py.
- **Background task crashes**: `run_refresh_pipeline` wraps everything in try/except. Failures are logged but don't surface to the API caller.
- **httpx non-2xx**: GitHub API errors are logged and return None — they don't crash the pipeline. Missing files are skipped gracefully.
- **Status check constraint**: `codebase_context.status` must be one of: `current`, `stale`, `generating`.
- **Token costs**: Full analysis uses ~5k-10k Claude tokens. Incremental uses ~3k-8k depending on how many files changed.

## Examples

### Get current context

```bash
curl https://your-api.example.com/api/v1/codebase-context
```

### Trigger a refresh

```bash
curl -X POST https://your-api.example.com/api/v1/codebase-context/refresh
```

## Source File Mapping

| Module File | Production Source |
|-------------|-----------------|
| `router.py` | `icp-service/app/api/codebase_context.py` |
| `service.py` | `icp-service/app/services/codebase_analyzer.py` |
| `models.py` | `icp-service/app/models/codebase_context.py` |
| `config.py` | `icp-service/app/config.py` (5 fields extracted) |
| `migrations/` | `supabase/migrations/006_codebase_context.sql` |
