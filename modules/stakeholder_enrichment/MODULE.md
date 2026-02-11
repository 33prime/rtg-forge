# Stakeholder Enrichment Module

## What It Does

Multi-source enrichment pipeline that takes a beta applicant's LinkedIn URL and company website, pulls data from three external APIs in parallel (PeopleDataLabs, Bright Data LinkedIn scraper, Firecrawl website extractor), then uses Claude to synthesize a deep consultant assessment, psychographic profile, sales intelligence, ICP fit score, and personalized demo project ideas. Results are persisted to Supabase. Both endpoints are fire-and-forget background tasks.

## When To Use It

- **Enriching beta applicants** -- After a consultant submits a beta application form, trigger enrichment to build a full intelligence profile before outreach.
- **ICP scoring** -- Automatically score applicants against the active ICP definition (0-100 with fit_category).
- **Demo project generation** -- Auto-generate 3 personalized project ideas for qualified leads (score >= 50) to use in sales demos.
- **Pre-meeting research** -- Generate psychographic profiles and sales intelligence before discovery calls.

## When NOT To Use It

- **Simple contact lookup** -- If you just need a name or email, use PDL directly.
- **Real-time lookups** -- The pipeline takes 30-120 seconds (parallel API polling + Claude synthesis). Not for sub-second responses.
- **Bulk imports** -- Designed for individual enrichment, not batch ETL of thousands.
- **Without API keys** -- Requires ANTHROPIC_API_KEY, PDL_API_KEY, BRIGHTDATA_API_KEY, and FIRECRAWL_API_KEY.

## Architecture

Two execution modes (feature-flagged via `use_langgraph_enrichment`):

### Legacy Pipeline (default)

Sequential async pipeline in `service.py`:

```
POST /enrich (beta_application_id)
    | BackgroundTask
fetch beta_applications row
    |
create/reset enrichment_profiles (status: enriching)
    |
+-- enrich_pdl --------+
|-- enrich_brightdata --|  asyncio.gather (parallel)
+-- enrich_firecrawl ---+
    |
store raw data to enrichment_profiles
    |
synthesize_consultant (Claude) -> consultant_assessment
    |
generate_psychographic_sales_intel (Claude, non-fatal)
    |
score_icp_fit (Claude) -> icp_fit_assessments insert
    |
finalize status (scored | failed | enriching)
    |
[if scored && score >= 50] -> run_ideas_pipeline
    |
generate_project_ideas (Claude) -> demo_project_ideas[3]
    |
status -> ideas_ready
```

### LangGraph Pipeline (feature-flagged)

StateGraph with parallel enrichment fan-out in `graph/`:

```
fetch_application -> init_profile -+-> enrich_pdl ------+
                                   |-> enrich_brightdata |-> store_enrichment
                                   +-> enrich_firecrawl -+
                                                            |
                                                      synthesize -> score -> finalize
                                                              |           |
                                                    generate_ideas       END
```

### Data Sources

| Source | API | Returns |
|--------|-----|---------|
| **PeopleDataLabs** | `POST /v5/person/enrich` | job_title, company, industry, skills, experience, education |
| **Bright Data** | `POST /datasets/v3/trigger` then poll snapshot | headline, about, posts, recommendations, followers, experience |
| **Firecrawl** | `POST /v1/extract` then poll job | services, industries_served, case_study_topics, differentiators |

### Claude Synthesis Stages

| Stage | Model | Max Tokens | Output |
|-------|-------|------------|--------|
| Consultant Assessment | claude-sonnet-4 | 2048 | practice_maturity, ai_readiness, seniority_tier, summary, strengths |
| Psychographic + Sales Intel | claude-sonnet-4 | 2048 | communication_style, risk_tolerance, ideal_pitch_angle, objections |
| ICP Pre-Score | claude-sonnet-4 | 1024 | overall_score (0-100), fit_category, attribute_scores |
| Project Ideas | claude-sonnet-4 | 4096 | 3 project ideas with fictional_client, wow_factor |

## Setup

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for synthesis |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `PDL_API_KEY` | Yes | PeopleDataLabs API key |
| `BRIGHTDATA_API_KEY` | Yes | Bright Data API key |
| `FIRECRAWL_API_KEY` | Yes | Firecrawl API key |
| `USE_LANGGRAPH_ENRICHMENT` | No | `true` to use LangGraph pipeline (default: `false`) |
| `SYNTHESIS_MODEL` | No | Claude model for synthesis (default: `claude-sonnet-4-20250514`) |

### Database

Run the migration to create required tables:

```bash
psql $DATABASE_URL -f modules/stakeholder_enrichment/migrations/001_create_tables.sql
```

**Prerequisite tables**: `beta_applications` and `icp_definitions` must already exist.

## API Reference

### POST /api/v1/enrichment/enrich

Trigger full enrichment pipeline (fire-and-forget).

**Request:**
```json
{ "beta_application_id": "uuid-string" }
```

**Response (200):**
```json
{ "status": "accepted", "message": "Enrichment started" }
```

Results are written asynchronously to `enrichment_profiles`, `icp_fit_assessments`, and `demo_project_ideas` tables.

### POST /api/v1/enrichment/generate-ideas

Generate personalized project ideas from stored enrichment data.

**Request:**
```json
{ "enrichment_profile_id": "uuid-string" }
```

**Response (200):**
```json
{ "status": "accepted", "message": "Idea generation started" }
```

Results are written to `demo_project_ideas` table (deletes existing ideas first for idempotency).

## Gotchas

- **BrightData schema quirks**: Uses `position` (not `headline`), `followers` (not `followers_count`), posts have `title` + `attribution` (not `text`). The `_parse_brightdata_profile` function normalizes these.
- **BrightData trigger+poll**: `/datasets/v3/trigger` returns `snapshot_id`, must poll `/datasets/v3/snapshot/{id}`. NOT truly synchronous despite docs.
- **Firecrawl async**: `/v1/extract` returns `{success, id}`, must poll `GET /v1/extract/{id}`. Sometimes returns data directly.
- **DB check constraints**: `enrichment_status` must be one of: `pending`, `enriching`, `scored`, `accepted`, `ideas_ready`, `booked`, `content_ready`, `seeded`, `failed`. `fit_category` must be: `strong_fit`, `moderate_fit`, `weak_fit`, `anti_pattern`.
- **Background task crashes**: Unhandled exceptions in FastAPI background tasks silently die. All pipelines wrap in try/except with status fallback to `failed`.
- **httpx non-2xx**: `httpx` does NOT raise on non-2xx status codes. Must check `res.status_code` manually.
- **JSONB columns**: Supabase PostgREST accepts raw dicts for JSONB -- do NOT `json.dumps()` them.
- **Token costs**: Each full enrichment uses ~10k-15k Claude tokens across 3-4 synthesis calls.
- **pydantic-settings v2**: Cannot parse `list[str]` from env vars. Use `str` type + manual parsing (see `_parse_origins` in config.py).

## Examples

### Trigger an enrichment

```bash
curl -X POST https://your-api.example.com/api/v1/enrichment/enrich \
  -H "Content-Type: application/json" \
  -d '{ "beta_application_id": "a1b2c3d4-5678-9abc-def0-123456789abc" }'
```

### Generate ideas for an enriched profile

```bash
curl -X POST https://your-api.example.com/api/v1/enrichment/generate-ideas \
  -H "Content-Type: application/json" \
  -d '{ "enrichment_profile_id": "a1b2c3d4-5678-9abc-def0-123456789abc" }'
```

## Source File Mapping

| Module File | Production Source |
|-------------|------------------|
| `router.py` | `icp-service/app/api/enrichment.py` |
| `service.py` (data sources) | `icp-service/app/services/enrichment.py` |
| `service.py` (synthesis) | `icp-service/app/services/synthesis.py` |
| `service.py` (pipelines) | `icp-service/app/api/enrichment.py` |
| `models.py` | `icp-service/app/models/enrichment.py` |
| `config.py` | `icp-service/app/config.py` |
| `graph/` | `icp-service/app/graph/enrichment/` |
