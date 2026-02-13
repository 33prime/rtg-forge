"""Context Assembly Engine — Core engine and services.

The engine runs a deterministic pipeline:
  Gather → Analyze → Score → Select → Format → Manifest

Domain-specific behavior is injected through configuration:
- Block definitions describe what blocks exist and how to format them
- Scoring rules adjust priorities based on the current situation
- The situation analyzer produces a typed diagnosis from raw data
- Modes define different budget/block configs for the same entity
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .models import (
    Block,
    Budget,
    Goal,
    GoalStatus,
    Manifest,
    ManifestEntry,
    Memory,
    MemoryStage,
    ModeConfig,
    Situation,
    TemporalMetadata,
    Tier,
    TIER_BASE_PRIORITY,
    Trend,
)

# Type aliases
SituationAnalyzer = Callable[[dict[str, Any]], Situation]
BlockFormatter = Callable[[Any, Situation], str]
ShouldInclude = Callable[[Any, Situation], bool]
RuleCondition = Callable[[Situation], bool]


# ---------------------------------------------------------------------------
# Runtime Scoring Rule
# ---------------------------------------------------------------------------


class ScoringRule:
    """Scoring rule with a callable condition and block-key adjustments."""

    def __init__(
        self,
        name: str,
        condition: RuleCondition,
        adjustments: dict[str, float],
        description: str = "",
    ):
        self.name = name
        self.condition = condition
        self.adjustments = adjustments
        self.description = description

    def apply(self, situation: Situation) -> dict[str, float]:
        """Return adjustments if condition is met, else empty dict."""
        if self.condition(situation):
            return self.adjustments
        return {}


# ---------------------------------------------------------------------------
# Runtime Block Definition
# ---------------------------------------------------------------------------


class RuntimeBlockDef:
    """Block definition with callable format and inclusion logic."""

    def __init__(
        self,
        key: str,
        tier: Tier = Tier.conditional,
        base_priority: float | None = None,
        category: str = "context",
        gatherer_key: str | None = None,
        format_fn: BlockFormatter | None = None,
        should_include: ShouldInclude | None = None,
        token_estimate: int = 100,
    ):
        self.key = key
        self.tier = tier
        self.base_priority = base_priority or TIER_BASE_PRIORITY.get(tier, 60)
        self.category = category
        self.gatherer_key = gatherer_key or key
        self.format_fn = format_fn or _default_format
        self.should_include = should_include or _always_include
        self.token_estimate = token_estimate


def _default_format(data: Any, situation: Situation) -> str:
    return str(data) if data else ""


def _always_include(data: Any, situation: Situation) -> bool:
    return True


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Context Assembly Engine
# ---------------------------------------------------------------------------


class ContextAssemblyEngine:
    """The core engine. Runs the deterministic assembly pipeline."""

    def __init__(
        self,
        name: str,
        block_defs: list[RuntimeBlockDef],
        scoring_rules: list[ScoringRule] | None = None,
        analyze_situation: SituationAnalyzer | None = None,
        modes: dict[str, ModeConfig] | None = None,
        default_budget: int = 1800,
    ):
        self.name = name
        self.block_defs = {bd.key: bd for bd in block_defs}
        self.scoring_rules = scoring_rules or []
        self.analyze_situation = analyze_situation or _default_analyzer
        self.modes = modes or {"default": ModeConfig(name="default", budget=default_budget)}
        self.default_budget = default_budget

    def assemble(
        self,
        entity_id: str,
        data: dict[str, Any],
        mode: str = "default",
        goals: list[Goal] | None = None,
        memories: list[Memory] | None = None,
    ) -> tuple[str, Manifest]:
        """Run the full pipeline. Returns (assembled_text, manifest)."""
        mode_config = self.modes.get(mode, ModeConfig(name=mode, budget=self.default_budget))
        budget_limit = mode_config.budget

        # Phase 1: ANALYZE — produce situation diagnosis
        situation = self.analyze_situation(data)
        situation.entity_id = entity_id
        situation.mode = mode

        # Phase 2: BUILD BLOCKS from data + definitions
        blocks = self._build_blocks(data, situation, mode_config)

        # Phase 3: APPLY GOAL ADJUSTMENTS
        if goals:
            self._apply_goal_adjustments(blocks, goals)

        # Phase 4: APPLY SCORING RULES
        self._apply_scoring_rules(blocks, situation)

        # Phase 5: INJECT MEMORY BLOCKS
        if memories:
            blocks.extend(self._build_memory_blocks(memories, situation))

        # Phase 6: SELECT WITHIN BUDGET
        included, excluded = self._select_within_budget(blocks, budget_limit)

        # Phase 7: FORMAT for LLM
        assembled_text = self._format_for_llm(included, situation, goals)

        # Phase 8: BUILD MANIFEST
        budget = Budget(
            total_tokens=budget_limit,
            used_tokens=sum(b.estimated_tokens for b in included),
            remaining_tokens=budget_limit - sum(b.estimated_tokens for b in included),
            blocks_included=len(included),
            blocks_excluded=len(excluded),
        )

        entries = [
            ManifestEntry(
                key=b.key,
                category=b.category,
                base_priority=b.base_priority,
                final_priority=b.priority,
                estimated_tokens=b.estimated_tokens,
                included=b.included,
                exclude_reason=b.exclude_reason,
                signals=b.signals,
            )
            for b in included + excluded
        ]

        manifest = Manifest(
            entity_id=entity_id,
            mode=mode,
            situation=situation,
            budget=budget,
            entries=entries,
            assembled_text=assembled_text,
            total_blocks_considered=len(entries),
        )

        return assembled_text, manifest

    # -- Internal pipeline steps --

    def _build_blocks(
        self,
        data: dict[str, Any],
        situation: Situation,
        mode_config: ModeConfig,
    ) -> list[Block]:
        blocks: list[Block] = []
        active_keys = mode_config.block_keys or list(self.block_defs.keys())

        for key in active_keys:
            block_def = self.block_defs.get(key)
            if not block_def:
                continue

            raw_data = data.get(block_def.gatherer_key)
            if raw_data is None:
                continue

            if not block_def.should_include(raw_data, situation):
                blocks.append(Block(
                    key=key,
                    category=block_def.category,
                    priority=0,
                    base_priority=block_def.base_priority,
                    included=False,
                    exclude_reason="should_include gate: False",
                    raw_data=raw_data,
                ))
                continue

            formatted = block_def.format_fn(raw_data, situation)
            tokens = estimate_tokens(formatted)

            blocks.append(Block(
                key=key,
                category=block_def.category,
                priority=block_def.base_priority,
                base_priority=block_def.base_priority,
                estimated_tokens=tokens,
                formatted_text=formatted,
                raw_data=raw_data,
            ))

        return blocks

    def _apply_goal_adjustments(
        self, blocks: list[Block], goals: list[Goal],
    ) -> None:
        for goal in goals:
            if goal.status != GoalStatus.active:
                continue
            for block in blocks:
                adj = goal.priority_adjustments.get(block.key, 0)
                if adj:
                    block.priority += adj
                    block.signals.append(f"goal:{goal.name}:{adj:+.0f}")

    def _apply_scoring_rules(
        self, blocks: list[Block], situation: Situation,
    ) -> None:
        for rule in self.scoring_rules:
            adjustments = rule.apply(situation)
            for block in blocks:
                adj = adjustments.get(block.key, 0)
                if adj:
                    block.priority += adj
                    block.signals.append(f"rule:{rule.name}:{adj:+.0f}")

        for block in blocks:
            block.priority = max(0, min(100, block.priority))

    def _build_memory_blocks(
        self, memories: list[Memory], situation: Situation,
    ) -> list[Block]:
        blocks: list[Block] = []
        for mem in memories:
            if mem.stage in (MemoryStage.archived,):
                continue

            base = 40 + (mem.confidence * 40)  # 40-80 range
            formatted = f"[Memory: {mem.category.value}] {mem.summary}"
            if mem.detail:
                formatted += f"\n{mem.detail}"

            blocks.append(Block(
                key=f"memory:{mem.id or mem.summary[:30]}",
                category=f"memory.{mem.category.value}",
                priority=base,
                base_priority=base,
                estimated_tokens=estimate_tokens(formatted),
                formatted_text=formatted,
                raw_data=mem.model_dump(),
                temporal=mem.temporal,
                signals=[f"confidence:{mem.confidence:.1f}", f"stage:{mem.stage.value}"],
            ))

        return blocks

    def _select_within_budget(
        self, blocks: list[Block], budget: int,
    ) -> tuple[list[Block], list[Block]]:
        scoreable = [b for b in blocks if b.exclude_reason is None]
        pre_excluded = [b for b in blocks if b.exclude_reason is not None]

        scoreable.sort(key=lambda b: b.priority, reverse=True)

        included: list[Block] = []
        excluded = list(pre_excluded)
        remaining = budget

        for block in scoreable:
            if block.estimated_tokens <= remaining:
                block.included = True
                included.append(block)
                remaining -= block.estimated_tokens
            else:
                block.included = False
                block.exclude_reason = f"budget: {remaining} tokens remaining"
                excluded.append(block)

        return included, excluded

    def _format_for_llm(
        self,
        blocks: list[Block],
        situation: Situation,
        goals: list[Goal] | None = None,
    ) -> str:
        sections: list[str] = []

        if situation.narrative:
            sections.append(f"## Current Situation\n{situation.narrative}\n")

        if goals:
            active = [g for g in goals if g.status == GoalStatus.active]
            if active:
                lines = ["## Active Goals"]
                for g in active:
                    lines.append(f"- **{g.name}**: {g.description} ({g.progress:.0%})")
                sections.append("\n".join(lines) + "\n")

        by_category: dict[str, list[Block]] = {}
        for b in blocks:
            cat = b.category or "general"
            by_category.setdefault(cat, []).append(b)

        for category, cat_blocks in sorted(by_category.items()):
            for block in cat_blocks:
                sections.append(f"## {block.key}\n{block.formatted_text}\n")

        return "\n".join(sections)


def _default_analyzer(data: dict[str, Any]) -> Situation:
    return Situation(flags=data)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_engine(
    name: str,
    block_defs: list[RuntimeBlockDef],
    scoring_rules: list[ScoringRule] | None = None,
    analyze_situation: SituationAnalyzer | None = None,
    modes: dict[str, ModeConfig] | None = None,
    budget: int = 1800,
) -> ContextAssemblyEngine:
    """Create a configured assembly engine."""
    return ContextAssemblyEngine(
        name=name,
        block_defs=block_defs,
        scoring_rules=scoring_rules,
        analyze_situation=analyze_situation,
        modes=modes,
        default_budget=budget,
    )


# ---------------------------------------------------------------------------
# Temporal Analysis
# ---------------------------------------------------------------------------


def compute_temporal(
    values: list[tuple[datetime, float]],
    window_current: int = 14,
    window_previous: int = 30,
    window_baseline: int = 90,
) -> TemporalMetadata:
    """Compute temporal metadata from a time-series of (datetime, value) pairs."""
    if not values:
        return TemporalMetadata()

    values.sort(key=lambda x: x[0])
    now = datetime.now(timezone.utc)

    current_vals = [v for dt, v in values if (now - dt).days <= window_current]
    previous_vals = [v for dt, v in values if window_current < (now - dt).days <= window_previous]
    baseline_vals = [v for dt, v in values if window_previous < (now - dt).days <= window_baseline]

    current_avg = sum(current_vals) / len(current_vals) if current_vals else 0
    previous_avg = sum(previous_vals) / len(previous_vals) if previous_vals else 0
    baseline_avg = sum(baseline_vals) / len(baseline_vals) if baseline_vals else 0

    delta = current_avg - previous_avg

    if len(current_vals) < 2:
        trend = Trend.stable
    elif abs(delta) < 0.5:
        trend = Trend.stable
    elif delta > 0:
        trend = Trend.improving
    else:
        trend = Trend.declining

    velocity = 0.0
    if previous_avg and baseline_avg:
        prev_delta = previous_avg - baseline_avg
        velocity = delta - prev_delta

    return TemporalMetadata(
        first_observed=values[0][0],
        last_observed=values[-1][0],
        occurrences=len(values),
        trend=trend,
        current=current_avg,
        previous=previous_avg,
        baseline=baseline_avg,
        delta=delta,
        velocity=velocity,
    )


# ---------------------------------------------------------------------------
# Memory Lifecycle
# ---------------------------------------------------------------------------


def advance_memory_lifecycle(memory: Memory, reinforced: bool = False) -> Memory:
    """Advance a memory through its lifecycle based on new evidence.

    Lifecycle: draft → reinforced → mature → decaying → revised/archived
    """
    now = datetime.now(timezone.utc)

    if reinforced:
        memory.temporal.occurrences += 1
        memory.temporal.last_observed = now
        memory.confidence = min(1.0, memory.confidence + 0.15)

        if memory.stage == MemoryStage.draft and memory.confidence >= 0.4:
            memory.stage = MemoryStage.reinforced
        elif memory.stage == MemoryStage.reinforced and memory.confidence >= 0.7:
            memory.stage = MemoryStage.mature
        elif memory.stage == MemoryStage.decaying:
            memory.stage = MemoryStage.reinforced
            memory.confidence = max(0.4, memory.confidence)
    else:
        memory.confidence = max(0.0, memory.confidence - 0.05)
        if memory.confidence < 0.3 and memory.stage == MemoryStage.mature:
            memory.stage = MemoryStage.decaying

    memory.updated_at = now
    return memory


def revise_memory(old: Memory, new_summary: str, new_detail: str = "") -> tuple[Memory, Memory]:
    """Revise a memory: archive old, create new with lineage.

    Returns (archived_old, new_memory).
    """
    now = datetime.now(timezone.utc)

    old.stage = MemoryStage.archived
    old.updated_at = now

    revised = Memory(
        entity_id=old.entity_id,
        category=old.category,
        stage=MemoryStage.draft,
        confidence=0.3,
        summary=new_summary,
        detail=new_detail or f"Previously: {old.summary}",
        tags=old.tags,
        temporal=TemporalMetadata(
            first_observed=now,
            last_observed=now,
            occurrences=1,
        ),
        metadata={**old.metadata, "revised_from": old.id},
        created_at=now,
        updated_at=now,
    )

    old.superseded_by = revised.id
    return old, revised
