# Call Intelligence Module

## What It Does

End-to-end meeting recording, transcription, and AI-powered analysis pipeline. Sends a recording bot (Recall.ai) to Google Meet, Zoom, or Teams meetings, transcribes the audio (Deepgram nova-2 with speaker diarization), then runs a configurable multi-dimensional analysis using Claude. Analysis is driven by **dimension packs** — not hardcoded prompts — so you can customize what gets extracted without touching code. Results (engagement scores, feature reactions, sales signals, coaching moments, competitive intel, content nuggets) are persisted to Supabase and optionally notified via Slack.

## When To Use It

- **Recording sales/demo calls** — Schedule a bot before the meeting. It joins, records, and triggers the full pipeline automatically via webhooks.
- **Post-call analysis** — Extract structured intelligence from any call: engagement scores, feature reactions, ICP signals, coaching feedback.
- **Custom analysis dimensions** — Add your own analysis dimensions via config (e.g., compliance flags, technical depth scoring) without writing code.
- **Re-analysis** — Re-run analysis with different dimension packs or updated prompts on existing transcripts.
- **Call library** — Browse all recordings with scores, drill into detail views with video playback and synchronized transcripts.

## When NOT To Use It

- **Real-time transcription** — This is a post-call pipeline. The bot records the full meeting, then processes afterward. Not for live captions.
- **Without API keys** — Requires at minimum RECALL_API_KEY and ANTHROPIC_API_KEY. DEEPGRAM_API_KEY is needed for transcription.
- **Phone calls** — Recall.ai supports Google Meet, Zoom, and Teams only. Not PSTN/phone.
- **Bulk historical imports** — Designed for one-at-a-time recording + analysis. Not optimized for batch processing thousands of recordings.

## Architecture

```
POST /recordings/schedule
    |
    v
Recall.ai Bot Created (bot_scheduled)
    |
    v  [Recall webhook: bot.done]
POST /webhooks/recall → BackgroundTask
    |
    v
Fetch media URLs from Recall API (transcribing)
    |
    v
Deepgram transcription (nova-2, diarize, utterances)
    |
    v
Save transcript to call_transcripts (analyzing)
    |
    v
Analysis Engine:
    1. Resolve active dimension packs (core, sales, coaching, research)
    2. Build combined JSON schema from all dimensions
    3. Assemble prompt: system + context_blocks + transcript + dimension instructions
    4. Single Claude API call → structured JSON
    5. Parse response → AnalysisResult model
    |
    v
Save to call_analyses + child tables (complete)
    |
    v
Slack notification (optional)
```

### Key Files

| File | Purpose |
|------|---------|
| `router.py` | 6 FastAPI endpoints |
| `service.py` | Pipeline orchestration (framework-agnostic) |
| `models.py` | 25+ Pydantic schemas for all data types |
| `config.py` | Settings extending CoreConfig |
| `analysis/dimensions.py` | 4 preset dimension packs + custom dimension support |
| `analysis/engine.py` | Prompt assembly, Claude API call, response parsing |
| `providers/recall.py` | Recall.ai REST client (create bot, fetch media, verify webhooks) |
| `providers/deepgram.py` | Deepgram transcription via httpx |
| `providers/notifications.py` | Slack webhook + generic webhook sender |
| `call-intelligence.config.json` | Runtime config (packs, custom dimensions, templates) |

### Database Tables (8 total)

| Table | Purpose |
|-------|---------|
| `call_recordings` | Recording metadata, status, media URLs |
| `call_transcripts` | Full text + speaker-diarized segments |
| `call_analyses` | Scores, summary, timeline, custom dimensions |
| `call_feature_insights` | Feature reactions, aha moments, feature requests |
| `call_signals` | ICP/market signals (pain points, goals, budget, timeline) |
| `call_coaching_moments` | Strengths, improvements, missed opportunities, objections |
| `call_content_nuggets` | Reusable quotes, pain framings, terminology |
| `call_competitive_mentions` | Competitor tracking with sentiment |

## Setup

### 1. Environment Variables

```bash
# Required
RECALL_API_KEY=your-recall-api-key
ANTHROPIC_API_KEY=your-anthropic-key
DEEPGRAM_API_KEY=your-deepgram-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Optional
RECALL_WEBHOOK_SECRET=your-webhook-hmac-secret
RECALL_REGION=us-west-2
RECALL_BOT_NAME=Meeting Notetaker
DEEPGRAM_MODEL=nova-2
ANALYSIS_MODEL=claude-sonnet-4-20250514
ANALYSIS_MAX_TOKENS=16384
ACTIVE_PACKS=core,sales,coaching,research
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 2. Database Migration

Run `migrations/001_create_tables.sql` against your Supabase project:

```bash
psql $DATABASE_URL -f migrations/001_create_tables.sql
```

Or apply via Supabase dashboard SQL editor.

### 3. Recall.ai Webhook

Configure your Recall.ai webhook URL in the dashboard:
```
https://your-api-domain.com/api/v1/call-intelligence/webhooks/recall
```

### 4. Mount the Router

```python
from modules.call_intelligence import module_info

app.include_router(
    module_info.router,
    prefix=module_info.prefix,
    tags=module_info.tags,
)
```

## API Reference

### `POST /recordings/schedule`

Schedule a recording bot for a meeting.

**Request:**
```json
{
  "meeting_url": "https://meet.google.com/abc-def-ghi",
  "contact_name": "Jane Smith",
  "contact_email": "jane@example.com",
  "contact_metadata": {"company": "Acme Corp"}
}
```

**Response:**
```json
{
  "success": true,
  "recording_id": "uuid",
  "recall_bot_id": "bot-123",
  "status": "bot_scheduled",
  "message": ""
}
```

### `POST /webhooks/recall`

Recall.ai webhook receiver. Configure this URL in your Recall dashboard. Returns 200 immediately and processes in background.

### `POST /recordings/{recording_id}/analyze`

Manually trigger (re-)analysis. Optional body with context blocks:

```json
{
  "recording_id": "uuid",
  "context_blocks": {
    "## Company Info": "Acme Corp, Series B, 50 employees"
  }
}
```

### `GET /recordings`

List all recordings, most recent first.

### `GET /recordings/{recording_id}`

Get a single recording by ID.

### `GET /recordings/{recording_id}/details`

Get full analysis details (transcript, analysis, features, signals, coaching moments).

## Customization

### Dimension Packs

The analysis engine is config-driven. Edit `call-intelligence.config.json` to control which dimensions are active:

```json
{
  "analysis": {
    "active_packs": ["core", "sales", "coaching", "research"]
  }
}
```

Or set via environment variable: `ACTIVE_PACKS=core,sales`

**Available packs:**

| Pack | Dimensions |
|------|-----------|
| `core` | executive_summary, engagement_score, engagement_timeline, talk_ratio |
| `sales` | feature_insights, signals, prospect_readiness |
| `coaching` | coaching_moments (strengths, improvements, missed opportunities, objection handling) |
| `research` | content_nuggets, competitive_intel |

### Custom Dimensions

Add your own analysis dimensions in `call-intelligence.config.json`:

```json
{
  "analysis": {
    "custom_dimensions": [
      {
        "key": "compliance_flags",
        "instruction": "Flag any compliance, regulatory, or legal concerns. Include quote and severity.",
        "schema": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "concern": { "type": "string" },
              "severity": { "enum": ["low", "medium", "high"] },
              "quote": { "type": "string" }
            }
          }
        }
      }
    ]
  }
}
```

Custom dimensions are stored in `call_analyses.custom_dimensions` (JSONB column).

### Notifications

Configure Slack notifications with template variables:

```json
{
  "notifications": {
    "slack_template": "Call with {contact_name} analyzed — Engagement: {engagement_score}/10, Readiness: {readiness_score}/10"
  }
}
```

## Gotchas

- **Recall.ai webhook timeout**: Recall expects a response within 15 seconds. The webhook handler returns immediately and processes in a BackgroundTask.
- **Recall.ai has no Python SDK**: All Recall interactions use httpx REST calls. The RecallClient in `providers/recall.py` wraps this.
- **Webhook signature verification**: Uses Svix HMAC-SHA256. Set `RECALL_WEBHOOK_SECRET` to enable. Without it, signature verification is skipped.
- **Deepgram via httpx**: Uses raw httpx POST to Deepgram's REST API (not the official SDK), keeping dependencies minimal.
- **Single Claude call**: All dimensions are analyzed in one API call. The prompt assembles instructions from all active dimensions + a combined JSON schema. This is more cost-effective than multiple calls.
- **Background task safety**: All background tasks (webhook processing, analysis) are wrapped in try/except with status-update fallbacks. Unhandled exceptions won't silently die.
- **Analysis cost**: A typical 30-minute call transcript uses ~4K input tokens + ~8K output tokens with all 4 packs active. Roughly $0.05-0.10 per analysis with Sonnet.

## Examples

### Schedule a recording

```bash
curl -X POST https://your-api.com/api/v1/call-intelligence/recordings/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/abc-def-ghi",
    "contact_name": "Jane Smith",
    "contact_email": "jane@example.com"
  }'
```

### Re-analyze with custom context

```bash
curl -X POST https://your-api.com/api/v1/call-intelligence/recordings/{id}/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "recording_id": "uuid",
    "context_blocks": {
      "## ICP Definition": "Target: Series A-C SaaS companies, 20-200 employees, using legacy tools"
    }
  }'
```

### Get full call details

```bash
curl https://your-api.com/api/v1/call-intelligence/recordings/{id}/details
```

## Frontend

The `frontend/` directory contains reference React components:

| File | Portability | Purpose |
|------|-------------|---------|
| `types.ts` | Copy directly | TypeScript interfaces mirroring `models.py` |
| `utils.ts` | Copy directly | Status colors, formatters, highlight styles |
| `useCallIntelligence.ts` | Adjust API_BASE | React hook for all data fetching |
| `CallIntelligenceTab.tsx` | Reference | List view with stats table |
| `CallDetailView.tsx` | Reference | Detail view with video player, transcript, analysis tabs |

Dependencies: `react`, `recharts`, `lucide-react`. Components use Tailwind CSS classes.
