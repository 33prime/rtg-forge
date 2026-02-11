# Stakeholder Enrichment Module

## What It Does

Multi-source stakeholder profile enrichment with AI synthesis. This module pulls data from LinkedIn profiles, company websites, and other public sources, then uses an AI pipeline (LangGraph + Anthropic) to produce structured stakeholder profiles with confidence scores, ICP signals, and suggested project ideas. It is designed for async enrichment workflows where depth of insight matters more than speed.

## When To Use It

- **Building account intelligence** -- Enrich stakeholder profiles before outreach or account planning.
- **Enriching CRM data** -- Fill in gaps in your CRM with structured, AI-synthesized profile data.
- **Pre-meeting research** -- Generate a comprehensive profile before a stakeholder meeting.
- **ICP scoring** -- Extract signals that indicate how well a stakeholder matches your Ideal Customer Profile.
- **Suggested project identification** -- Discover potential project ideas based on stakeholder context.

## When NOT To Use It

- **Simple contact lookup** -- If you just need a name or email, use a dedicated contacts API instead.
- **Real-time lookups** -- This module runs an async enrichment pipeline. It is not suitable for synchronous, sub-second lookups.
- **Bulk data import** -- For importing thousands of contacts, use a batch ETL pipeline. This module is designed for individual or small-batch enrichment.
- **Guaranteed data freshness** -- Scraped data may be cached. If you need real-time accuracy, verify against the source directly.

## Architecture

The enrichment pipeline is implemented as a LangGraph graph with the following nodes:

```
fetch_sources -> extract_data -> synthesize_profile -> score_confidence -> generate_signals
```

### Pipeline Nodes

1. **fetch_sources** -- Given a LinkedIn URL and/or company website URL, fetches the raw HTML/data from each source. Uses `httpx` with rate limiting and retry logic.

2. **extract_data** -- Parses the raw data from each source into structured fields (name, title, company, bio, recent activity, etc.). Uses a combination of HTML parsing and LLM extraction.

3. **synthesize_profile** -- Takes the extracted data from all sources and synthesizes a unified profile narrative. Resolves conflicts between sources and produces a coherent summary. Powered by Anthropic Claude.

4. **score_confidence** -- Assigns a confidence score (0.0 to 1.0) to the synthesized profile based on source agreement, data completeness, and recency.

5. **generate_signals** -- Extracts ICP signals and suggests potential project ideas based on the synthesized profile. Produces structured lists for downstream consumption.

### Data Flow

```
EnrichmentRequest
    |
    v
[fetch_sources] -- raw HTML/JSON per source
    |
    v
[extract_data] -- structured EnrichmentSource objects
    |
    v
[synthesize_profile] -- unified narrative text
    |
    v
[score_confidence] -- confidence float
    |
    v
[generate_signals] -- icp_signals[], suggested_projects[]
    |
    v
EnrichmentProfile (persisted to Supabase)
```

### Storage

All profiles and sources are stored in Supabase (PostgreSQL) with Row Level Security enabled. Profiles are cached for a configurable TTL (default: 24 hours).

## Setup

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Anthropic Claude |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key (for RLS bypass in server context) |
| `ENRICHMENT_MAX_SOURCES` | No | Maximum number of sources to fetch per enrichment (default: 5) |
| `ENRICHMENT_CACHE_TTL_HOURS` | No | Hours to cache enrichment profiles (default: 24) |
| `ENRICHMENT_MAX_CONCURRENT` | No | Maximum concurrent enrichment pipelines (default: 3) |

### Database Migrations

Run the migration to create required tables:

```bash
# Apply from the module's migrations directory
psql $DATABASE_URL -f modules/stakeholder_enrichment/migrations/001_create_tables.sql
```

### Configuration

The module extends `CoreConfig` via `EnrichmentConfig` in `config.py`. All settings can be overridden via environment variables with the `ENRICHMENT_` prefix.

## API Reference

### POST /api/v1/enrichment/enrich

Trigger a stakeholder enrichment pipeline.

**Request Body:**

```json
{
  "stakeholder_name": "Jane Smith",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "company_url": "https://acmecorp.com/about",
  "additional_context": "CTO, interested in AI/ML infrastructure"
}
```

**Response (201 Created):**

```json
{
  "profile": {
    "id": "a1b2c3d4-...",
    "stakeholder_name": "Jane Smith",
    "sources": [
      {
        "source_type": "linkedin",
        "url": "https://linkedin.com/in/janesmith",
        "raw_data": {},
        "extracted_at": "2026-02-11T10:00:00Z",
        "confidence": 0.85
      }
    ],
    "synthesis": "Jane Smith is the CTO of Acme Corp...",
    "confidence_score": 0.82,
    "icp_signals": ["technical-leader", "ai-ml-interest", "enterprise-scale"],
    "suggested_projects": ["ML infrastructure audit", "AI strategy workshop"],
    "created_at": "2026-02-11T10:00:00Z",
    "updated_at": "2026-02-11T10:00:00Z"
  },
  "status": "completed"
}
```

### GET /api/v1/enrichment/profiles/{profile_id}

Retrieve an enrichment profile by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile_id` | UUID | The profile's unique identifier |

**Response (200 OK):** Returns `EnrichmentProfile` object.

**Response (404 Not Found):** Profile does not exist.

### GET /api/v1/enrichment/profiles

List enrichment profiles with pagination.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Number of profiles to return (max 100) |
| `offset` | int | 0 | Offset for pagination |

**Response (200 OK):**

```json
{
  "profiles": [...],
  "total": 42
}
```

### DELETE /api/v1/enrichment/profiles/{profile_id}

Delete an enrichment profile and all associated sources.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile_id` | UUID | The profile's unique identifier |

**Response (204 No Content):** Profile deleted successfully.

**Response (404 Not Found):** Profile does not exist.

## Gotchas

- **LinkedIn rate limits**: LinkedIn aggressively blocks scrapers. The module uses configurable delays and respects rate limits, but enrichment from LinkedIn may fail or return partial data. Always check the `confidence` score on LinkedIn sources.
- **LinkedIn authentication**: Direct scraping of LinkedIn requires authentication. Phase 1 uses stub data; Phase 2 will integrate with a LinkedIn data provider API.
- **Cache management**: Profiles are cached for `ENRICHMENT_CACHE_TTL_HOURS`. If a stakeholder's profile changes, you may need to delete and re-enrich.
- **Token costs**: The synthesis and signal generation steps use Anthropic Claude. Each enrichment costs approximately 2,000-5,000 tokens depending on source richness. Monitor usage.
- **RLS policies**: The migration enables RLS but does not create policies. You must create appropriate RLS policies for your auth scheme before deploying.
- **Concurrent limits**: The `ENRICHMENT_MAX_CONCURRENT` setting controls how many pipelines run simultaneously. Exceeding this will queue requests.

## Examples

### Trigger an enrichment

```bash
curl -X POST https://your-api.example.com/api/v1/enrichment/enrich \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{
    "stakeholder_name": "Jane Smith",
    "linkedin_url": "https://linkedin.com/in/janesmith",
    "company_url": "https://acmecorp.com/about",
    "additional_context": "CTO, interested in AI/ML infrastructure"
  }'
```

### Get a profile

```bash
curl https://your-api.example.com/api/v1/enrichment/profiles/a1b2c3d4-5678-9abc-def0-123456789abc \
  -H "Authorization: Bearer $API_TOKEN"
```

### List profiles with pagination

```bash
curl "https://your-api.example.com/api/v1/enrichment/profiles?limit=10&offset=0" \
  -H "Authorization: Bearer $API_TOKEN"
```

### Delete a profile

```bash
curl -X DELETE https://your-api.example.com/api/v1/enrichment/profiles/a1b2c3d4-5678-9abc-def0-123456789abc \
  -H "Authorization: Bearer $API_TOKEN"
```
