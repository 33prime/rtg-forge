"""Context Assembly Engine — Deterministic context curation for LLM systems.

A three-layer architecture (Goals, Memory, Context) that assembles precisely
the right context for every LLM call, governed by explicit goals, enriched by
persistent memory, and grounded in temporal awareness.
"""

from dataclasses import dataclass


@dataclass
class ModuleInfo:
    name: str = "context_assembly_engine"
    version: str = "0.1.0"
    description: str = (
        "Deterministic context assembly engine for LLM systems — "
        "goal-directed, memory-persistent, temporally-aware"
    )
    category: str = "ai-infrastructure"
    author: str = "RTG"


# Re-export key types for convenience
from .models import (  # noqa: E402
    Block,
    BlockDef,
    Budget,
    Goal,
    Manifest,
    Memory,
    ModeConfig,
    Situation,
    TemporalMetadata,
)
from .service import (  # noqa: E402
    ContextAssemblyEngine,
    RuntimeBlockDef,
    ScoringRule,
    compute_temporal,
    create_engine,
)

__all__ = [
    "Block",
    "BlockDef",
    "Budget",
    "ContextAssemblyEngine",
    "Goal",
    "Manifest",
    "Memory",
    "ModeConfig",
    "ModuleInfo",
    "RuntimeBlockDef",
    "ScoringRule",
    "Situation",
    "TemporalMetadata",
    "compute_temporal",
    "create_engine",
]
