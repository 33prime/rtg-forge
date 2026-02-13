# ICP Signal Extraction

## What It Does

Extracts ICP (Ideal Customer Profile) signals from call transcripts and enriched beta applications using Claude, generates embeddings with OpenAI, routes signals to existing profiles by cosine similarity, clusters outlier signals with DBSCAN to detect emerging patterns, and surfaces items for human review via a dashboard API. The entire extraction-to-routing flow runs as a 5-node LangGraph pipeline triggered by webhooks.

## When To Use It

- You have call transcripts or enriched beta application data and need to extract structured ICP signals (pain points, goals, triggers, objections, demographics, surprises)
- You want automatic routing of signals to existing ICP profiles based on semantic similarity
- You need to detect emerging customer patterns from outlier signals via clustering
- You want a human-in-the-loop review queue for borderline signals
- You need dashboard metrics for signal volume, routing status, and cluster health

## When NOT To Use It

- For initial stakeholder enrichment (use `stakeholder_enrichment` module instead)
- For simple keyword-based categorization — this module uses embedding similarity, which is overkill for rule-based routing
- If you don't have pgvector enabled on your Supabase project (required for HNSW indexes)
- For real-time, synchronous signal processing — the pipeline runs as a background task

## Architecture

```
Webhook (call-analyzed / beta-enriched)
  │
  ▼
run_pipeline() [BackgroundTask]
  │
  ├── create_pipeline_run row
  │
  ▼
LangGraph Pipeline:
  extract_signals ──► generate_embeddings ──► route_signals
                                                  │
                                          ┌───────┴───────┐
                                          │               │
                                    has_outliers?    no outliers
                                          │               │
                                   handle_outliers        │
                                          │               │
                                          └───────┬───────┘
                                                  │
                                               notify
                                                  │
                                                 END
```

**Routing thresholds:**
- >= 0.85 similarity → auto-routed (no human review needed)
- 0.65 - 0.85 → review_required (human must approve)
- < 0.65 → outlier (unmatched, candidate for clustering)

**Clustering:** Periodic DBSCAN on outlier signals (eps=0.3 cosine distance, min_samples=3). Clusters can be promoted to new profiles or dismissed.

## Setup

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `SUPABASE_DB_URL` | Yes | Direct Postgres connection string (for asyncpg/pgvector) |
| `ANTHROPIC_API_KEY` | Yes | For Claude signal extraction |
| `OPENAI_API_KEY` | Yes | For text-embedding-3-small |
| `SLACK_WEBHOOK_URL` | No | Slack incoming webhook for review notifications |

### Database Migration

Run `migrations/001_create_tables.sql` against your Supabase project. Creates the `icp_intelligence` schema with 6 tables, HNSW vector indexes, and RLS policies.

### Host Integration

```python
from modules.icp_signal_extraction import module_info
from modules.icp_signal_extraction.graph.runner import set_db

# Mount the router
app.include_router(module_info.router, prefix=module_info.prefix, tags=module_info.tags)

# Inject the database client
set_db(your_db_instance)
```

## API Reference

### Webhooks

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/webhooks/call-analyzed` | `CallAnalyzedPayload` | `WebhookAccepted` |
| POST | `/webhooks/beta-enriched` | `BetaEnrichedPayload` | `WebhookAccepted` |

### Profiles

| Method | Path | Response |
|--------|------|----------|
| GET | `/profiles` | `list[Profile]` |
| GET | `/profiles/{id}` | `Profile` |
| GET | `/profiles/{id}/detail` | `ProfileDetail` |
| POST | `/profiles` | `Profile` (201) |
| POST | `/profiles/{id}/activate` | `Profile` |

### Signals

| Method | Path | Response |
|--------|------|----------|
| GET | `/signals/review-queue` | `list[SignalWithContext]` |
| GET | `/signals/recent` | `list[SignalWithContext]` |
| POST | `/signals/{id}/review` | `ReviewResponse` |
| GET | `/signals/similar?text=...` | `list[dict]` |

### Clusters

| Method | Path | Response |
|--------|------|----------|
| GET | `/clusters` | `list[Cluster]` |
| GET | `/clusters/{id}` | `ClusterDetail` |
| POST | `/clusters/{id}/promote` | `PromoteResponse` |
| POST | `/clusters/{id}/dismiss` | `DismissResponse` |
| POST | `/clusters/recompute` | `RecomputeResponse` |

### Metrics

| Method | Path | Response |
|--------|------|----------|
| GET | `/metrics` | `MetricsResponse` |

## Gotchas

- **pgvector required**: The `<=>` cosine distance operator and HNSW indexes require the pgvector extension. PostgREST can't use these operators — that's why this module uses direct asyncpg connections instead of the Supabase REST API.
- **Background task failures**: Unhandled exceptions in background tasks silently die. The runner wraps everything in try/except and marks pipeline_runs as failed. Always check pipeline_runs for error_message.
- **Embedding dimensions**: Hardcoded to 1536 (text-embedding-3-small). If you change models, update both config and migration column types.
- **Confidence asymptotic growth**: Profile confidence uses `new = old + (1 - old) * 0.15`, so it approaches but never reaches 1.0. This is intentional.
- **DBSCAN eps=0.3**: This means cosine *distance* threshold, which corresponds to similarity > 0.7 for cluster membership.

## Examples

### Trigger pipeline from call transcript

```bash
curl -X POST https://your-api/api/v1/icp/webhooks/call-analyzed \
  -H "Content-Type: application/json" \
  -d '{
    "call_recording_id": "550e8400-e29b-41d4-a716-446655440000",
    "transcript": "The client mentioned struggling with...",
    "summary": "Discovery call about AI adoption challenges"
  }'
```

### Review a signal

```bash
curl -X POST https://your-api/api/v1/icp/signals/550e8400.../review \
  -H "Content-Type: application/json" \
  -d '{"action": "accepted", "reviewed_by": "admin"}'
```

### Promote a cluster to a profile

```bash
curl -X POST https://your-api/api/v1/icp/clusters/550e8400.../promote \
  -H "Content-Type: application/json" \
  -d '{"profile_name": "Enterprise AI Adopter"}'
```

### Get dashboard metrics

```bash
curl https://your-api/api/v1/icp/metrics
```
