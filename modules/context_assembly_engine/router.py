"""Context Assembly Engine — FastAPI router.

Endpoints for running the assembly pipeline, managing goals and memories,
and querying the decision log.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from .models import (
    AssembleRequest,
    AssembleResponse,
    DecisionOutcome,
    DecisionRecord,
    Goal,
    GoalCreate,
    GoalStatus,
    GoalUpdate,
    Memory,
    MemoryCreate,
    MemoryStage,
    MemoryUpdate,
)

router = APIRouter(prefix="/api/v1/cae", tags=["context-assembly-engine"])


# ---------------------------------------------------------------------------
# In-memory stores (replaced by Supabase when personalized)
# ---------------------------------------------------------------------------

_goals: dict[str, Goal] = {}
_memories: dict[str, Memory] = {}
_decisions: dict[str, DecisionRecord] = {}
_manifests: dict[str, dict] = {}  # entity_id → latest manifest

# The engine instance is set by the app at startup via configure_engine()
_engine = None


def configure_engine(engine: Any) -> None:
    """Set the engine instance used by the router."""
    global _engine
    _engine = engine


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


@router.post("/assemble", response_model=AssembleResponse)
def assemble_context(req: AssembleRequest) -> AssembleResponse:
    """Run the full assembly pipeline for an entity."""
    if _engine is None:
        raise HTTPException(status_code=503, detail="Engine not configured")

    entity_goals = [g for g in _goals.values() if g.entity_id == req.entity_id]
    entity_memories = [m for m in _memories.values() if m.entity_id == req.entity_id]

    assembled_text, manifest = _engine.assemble(
        entity_id=req.entity_id,
        data=req.data,
        mode=req.mode,
        goals=entity_goals,
        memories=entity_memories,
    )

    _manifests[req.entity_id] = manifest.model_dump()
    return AssembleResponse(assembled_text=assembled_text, manifest=manifest)


@router.get("/manifest/{entity_id}")
def get_latest_manifest(entity_id: str) -> dict:
    """Get the most recent manifest for an entity."""
    m = _manifests.get(entity_id)
    if not m:
        raise HTTPException(status_code=404, detail="No manifest found")
    return m


# ---------------------------------------------------------------------------
# Goals CRUD
# ---------------------------------------------------------------------------


@router.post("/goals", response_model=Goal)
def create_goal(body: GoalCreate) -> Goal:
    goal = Goal(
        id=str(uuid4()),
        entity_id=body.entity_id,
        name=body.name,
        description=body.description,
        priority_adjustments=body.priority_adjustments,
        target_date=body.target_date,
        metadata=body.metadata,
    )
    _goals[goal.id] = goal
    return goal


@router.get("/goals", response_model=list[Goal])
def list_goals(entity_id: str = "") -> list[Goal]:
    goals = list(_goals.values())
    if entity_id:
        goals = [g for g in goals if g.entity_id == entity_id]
    return goals


@router.get("/goals/{goal_id}", response_model=Goal)
def get_goal(goal_id: str) -> Goal:
    goal = _goals.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/goals/{goal_id}", response_model=Goal)
def update_goal(goal_id: str, body: GoalUpdate) -> Goal:
    goal = _goals.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(goal, field, value)
    goal.updated_at = datetime.now(timezone.utc)
    return goal


# ---------------------------------------------------------------------------
# Memories CRUD
# ---------------------------------------------------------------------------


@router.post("/memories", response_model=Memory)
def create_memory(body: MemoryCreate) -> Memory:
    memory = Memory(
        id=str(uuid4()),
        entity_id=body.entity_id,
        category=body.category,
        summary=body.summary,
        detail=body.detail,
        tags=body.tags,
        metadata=body.metadata,
    )
    _memories[memory.id] = memory
    return memory


@router.get("/memories", response_model=list[Memory])
def list_memories(entity_id: str = "", category: str = "") -> list[Memory]:
    memories = list(_memories.values())
    if entity_id:
        memories = [m for m in memories if m.entity_id == entity_id]
    if category:
        memories = [m for m in memories if m.category.value == category]
    return memories


@router.get("/memories/{memory_id}", response_model=Memory)
def get_memory(memory_id: str) -> Memory:
    memory = _memories.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/memories/{memory_id}", response_model=Memory)
def update_memory(memory_id: str, body: MemoryUpdate) -> Memory:
    memory = _memories.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(memory, field, value)
    memory.updated_at = datetime.now(timezone.utc)
    return memory


@router.post("/memories/{memory_id}/reinforce", response_model=Memory)
def reinforce_memory(memory_id: str) -> Memory:
    """Record another observation of this memory pattern."""
    from .service import advance_memory_lifecycle

    memory = _memories.get(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return advance_memory_lifecycle(memory, reinforced=True)


# ---------------------------------------------------------------------------
# Decision Log
# ---------------------------------------------------------------------------


@router.post("/decisions", response_model=DecisionRecord)
def record_decision(
    entity_id: str,
    mode: str = "default",
    recommendation: str = "",
) -> DecisionRecord:
    """Record a recommendation for later outcome tracking."""
    record = DecisionRecord(
        id=str(uuid4()),
        entity_id=entity_id,
        mode=mode,
        recommendation=recommendation,
        manifest_summary=_manifests.get(entity_id, {}),
        memories_used=[m.id for m in _memories.values() if m.entity_id == entity_id and m.id],
        active_goals=[
            g.id for g in _goals.values()
            if g.entity_id == entity_id and g.status == GoalStatus.active and g.id
        ],
    )
    _decisions[record.id] = record
    return record


@router.patch("/decisions/{decision_id}/outcome", response_model=DecisionRecord)
def record_outcome(decision_id: str, outcome: DecisionOutcome) -> DecisionRecord:
    """Attach an outcome to a previous decision."""
    record = _decisions.get(decision_id)
    if not record:
        raise HTTPException(status_code=404, detail="Decision not found")

    record.outcome = outcome
    return record


@router.get("/decisions", response_model=list[DecisionRecord])
def list_decisions(entity_id: str = "") -> list[DecisionRecord]:
    decisions = list(_decisions.values())
    if entity_id:
        decisions = [d for d in decisions if d.entity_id == entity_id]
    return decisions
