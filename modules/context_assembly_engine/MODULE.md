# Context Assembly Engine (CAE)

> RAG retrieves. CAE assembles. The LLM is commodity. The context engine is the product.

## What It Does

The Context Assembly Engine is a **deterministic context curation layer** for LLM systems. Instead of stuffing everything into the prompt or relying on probabilistic vector search, the CAE assembles precisely the right context for every LLM call.

It operates on **four primitives** across **three layers**, unified by a **temporal dimension**:

### Four Primitives
| Primitive | Purpose |
|-----------|---------|
| **Block** | Atomic unit of knowledge with metadata for scoring, budgeting, and auditability |
| **Situation** | Typed diagnosis: "What is happening with this entity right now?" |
| **Scoring Rule** | Deterministic function: `(Block, Situation) → priority adjustment` |
| **Budget** | Token ceiling that forces prioritization — signal over noise |

### Three Layers
| Layer | Question | Time Scale |
|-------|----------|------------|
| **Goals** | WHY — what matters most right now? | Weekly |
| **Memory** | WHO — what do we know about this entity? | Months |
| **Context** | WHAT NOW — what's the current situation? | Per-call |

### Assembly Pipeline
Every LLM call runs through:
```
Gather → Analyze → Score → Select → Format → Manifest
```
The **Manifest** is a complete record of what was included, excluded, and why — full transparency.

## When To Use It

- Building an AI that needs to **know its user over time** (coaching, advising, tutoring)
- Any domain where context relevance must be **deterministic and explainable**
- Systems where **token budgets matter** — you can't dump everything into the prompt
- When RAG's probabilistic retrieval isn't reliable enough for production
- Multi-mode systems: same entity, different interaction types, different context assemblies

## When NOT To Use It

- Simple single-turn Q&A with no user state
- Open-ended document search (use RAG directly)
- Systems where the LLM itself should decide what context to use

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ASSEMBLY PIPELINE                 │
│                                                     │
│  ┌──────────┐  ┌─────────┐  ┌───────┐  ┌────────┐ │
│  │  GATHER  │→ │ ANALYZE │→ │ SCORE │→ │ SELECT │ │
│  │ (data)   │  │ (sit.)  │  │(rules)│  │(budget)│ │
│  └──────────┘  └─────────┘  └───────┘  └────────┘ │
│       ↓                                     ↓       │
│  ┌────────────────────┐    ┌──────────────────────┐│
│  │    FORMAT (LLM)    │    │   MANIFEST (debug)   ││
│  └────────────────────┘    └──────────────────────┘│
│                                                     │
│  Layer 1: Goals ────── priority function            │
│  Layer 2: Memory ───── persistent knowledge         │
│  Layer 3: Context ──── real-time blocks             │
│  Temporal ──────────── time-series across all       │
└─────────────────────────────────────────────────────┘
```

## Setup

### 1. Install dependencies

```bash
pip install fastapi pydantic pydantic-settings
```

### 2. Run database migrations

Apply `migrations/001_create_cae_tables.sql` to create the four core tables:
- `cae_goals` — entity goals with priority adjustments
- `cae_memories` — persistent memories with lifecycle stages
- `cae_decision_log` — recommendation vs outcome tracking
- `cae_manifests` — stored assembly manifests

### 3. Configure an engine

```python
from context_assembly_engine import (
    RuntimeBlockDef, ScoringRule, Situation, ModeConfig, create_engine,
)
from context_assembly_engine.models import Tier

engine = create_engine(
    name="my_domain",
    block_defs=[
        RuntimeBlockDef(
            key="recent_performance",
            tier=Tier.always,
            format_fn=lambda data, sit: format_performance(data),
        ),
        RuntimeBlockDef(
            key="risk_factors",
            tier=Tier.conditional,
            format_fn=lambda data, sit: format_risks(data),
            should_include=lambda data, sit: sit.has_flag("elevated_risk"),
        ),
        RuntimeBlockDef(
            key="deep_history",
            tier=Tier.strong_signal,
            format_fn=lambda data, sit: format_history(data),
            should_include=lambda data, sit: sit.has_flag("regression"),
        ),
    ],
    scoring_rules=[
        ScoringRule(
            name="crisis_boost",
            condition=lambda sit: sit.flag_value("severity", 0) >= 8,
            adjustments={"risk_factors": +30, "deep_history": +20},
        ),
    ],
    modes={
        "realtime": ModeConfig(name="realtime", budget=500),
        "review": ModeConfig(name="review", budget=1800),
        "conversation": ModeConfig(name="conversation", budget=800),
    },
    budget=1800,
)
```

### 4. Run the pipeline

```python
text, manifest = engine.assemble(
    entity_id="user-123",
    data={
        "recent_performance": fetch_recent_performance(user_id),
        "risk_factors": fetch_risk_factors(user_id),
        "deep_history": fetch_history(user_id),
    },
    mode="review",
    goals=user_goals,
    memories=user_memories,
)

# text → curated prompt section for the LLM
# manifest → full transparency into assembly decisions
```

### 5. Mount the API

```python
from context_assembly_engine.router import router, configure_engine

configure_engine(engine)
app.include_router(router)
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/cae/assemble` | Run the full assembly pipeline |
| GET | `/api/v1/cae/manifest/{entity_id}` | Get latest manifest |
| POST | `/api/v1/cae/goals` | Create a goal |
| GET | `/api/v1/cae/goals?entity_id=X` | List goals |
| PATCH | `/api/v1/cae/goals/{id}` | Update a goal |
| POST | `/api/v1/cae/memories` | Create a memory |
| GET | `/api/v1/cae/memories?entity_id=X` | List memories |
| PATCH | `/api/v1/cae/memories/{id}` | Update a memory |
| POST | `/api/v1/cae/memories/{id}/reinforce` | Reinforce a memory pattern |
| POST | `/api/v1/cae/decisions` | Record a decision |
| PATCH | `/api/v1/cae/decisions/{id}/outcome` | Attach outcome to decision |
| GET | `/api/v1/cae/decisions?entity_id=X` | Query decision log |

## Memory Lifecycle

Memories evolve through stages that mirror how human experts accumulate understanding:

```
draft (0.2) → reinforced (0.4) → mature (0.7+) → decaying → revised/archived
```

Each reinforcement bumps confidence +0.15. Stage transitions happen at confidence thresholds. Unreinforced memories decay -0.05 per check. Decaying memories can be revived by new evidence.

## Multi-Mode Operation

Same entity, same data, different assembly:

| Mode | Budget | Focus |
|------|--------|-------|
| Training Plan | 1,800 | Module progress, practice gaps, KPI proximity |
| On-Course | 500 | Hole history, club data, momentum |
| Post-Round | 1,200 | Round detail vs practice, goal tracking |
| Conversation | 800 | Memories, goals, motivation style |

## Gotchas

1. **The engine is not the LLM.** The engine decides what context matters. The LLM's only job is to be articulate with what it receives.
2. **Scoring rules encode domain expertise.** Start with human-authored priors, then tune empirically using the decision log.
3. **Budget is a feature, not a constraint.** A tight budget forces prioritization. The best coaching isn't "here's everything" — it's "here's what matters right now."
4. **CAE complements RAG.** RAG can populate individual blocks. CAE determines whether those blocks should be included and at what priority.

## Examples

### Golf Training Plan
```python
engine = create_engine(
    name="golf_training",
    block_defs=[
        RuntimeBlockDef(key="recent_rounds", tier=Tier.always,
            format_fn=format_recent_rounds),
        RuntimeBlockDef(key="module_progress", tier=Tier.always,
            format_fn=format_module_progress),
        RuntimeBlockDef(key="swing_faults", tier=Tier.conditional,
            format_fn=format_swing_faults,
            should_include=lambda d, s: s.has_flag("has_fault_match")),
        RuntimeBlockDef(key="practice_gap", tier=Tier.conditional,
            format_fn=format_practice_gap,
            should_include=lambda d, s: s.flag_value("days_since_practice", 0) > 7),
    ],
    scoring_rules=[
        ScoringRule(
            name="bad_round_boost",
            condition=lambda sit: sit.flag_value("last_round_over_par", 0) >= 8,
            adjustments={"swing_faults": +30, "practice_gap": +20},
        ),
        ScoringRule(
            name="plateau_boost",
            condition=lambda sit: sit.has_flag("kpi_plateau"),
            adjustments={"swing_faults": +20, "module_progress": +15},
        ),
    ],
    budget=1800,
)
```

### Sales CRM
```python
engine = create_engine(
    name="deal_coaching",
    block_defs=[
        RuntimeBlockDef(key="deal_state", tier=Tier.always,
            format_fn=format_deal_state),
        RuntimeBlockDef(key="champion_intel", tier=Tier.always,
            format_fn=format_champion_intel),
        RuntimeBlockDef(key="competitor_mentions", tier=Tier.conditional,
            format_fn=format_competitor,
            should_include=lambda d, s: s.has_flag("competitor_active")),
        RuntimeBlockDef(key="objection_history", tier=Tier.strong_signal,
            format_fn=format_objections,
            should_include=lambda d, s: s.has_flag("deal_stalling")),
    ],
    scoring_rules=[
        ScoringRule(
            name="stall_response",
            condition=lambda sit: sit.has_flag("deal_stalling"),
            adjustments={"objection_history": +40, "champion_intel": +15},
        ),
    ],
    budget=1200,
)
```
