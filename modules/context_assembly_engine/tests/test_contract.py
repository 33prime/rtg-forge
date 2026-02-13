"""Contract tests for the Context Assembly Engine module."""

from pathlib import Path


MODULE_DIR = Path(__file__).parent.parent


def test_required_files_exist():
    required = [
        "module.toml", "MODULE.md", "__init__.py",
        "router.py", "service.py", "models.py", "config.py",
    ]
    for fname in required:
        assert (MODULE_DIR / fname).is_file(), f"Missing required file: {fname}"


def test_required_dirs_exist():
    for dname in ["migrations", "tests"]:
        assert (MODULE_DIR / dname).is_dir(), f"Missing required dir: {dname}"


def test_module_info_import():
    from context_assembly_engine import ModuleInfo
    info = ModuleInfo()
    assert info.name == "context_assembly_engine"
    assert info.version


def test_engine_creation():
    from context_assembly_engine import (
        RuntimeBlockDef,
        ScoringRule,
        Situation,
        create_engine,
    )
    from context_assembly_engine.models import Tier

    engine = create_engine(
        name="test_engine",
        block_defs=[
            RuntimeBlockDef(
                key="greeting",
                tier=Tier.always,
                format_fn=lambda data, sit: f"Hello, {data}!",
            ),
            RuntimeBlockDef(
                key="detail",
                tier=Tier.conditional,
                format_fn=lambda data, sit: str(data),
                should_include=lambda data, sit: sit.has_flag("include_detail"),
            ),
        ],
        scoring_rules=[
            ScoringRule(
                name="boost_detail",
                condition=lambda sit: sit.has_flag("urgent"),
                adjustments={"detail": +30},
            ),
        ],
        budget=500,
    )
    assert engine.name == "test_engine"


def test_assembly_pipeline():
    from context_assembly_engine import RuntimeBlockDef, create_engine
    from context_assembly_engine.models import Tier

    engine = create_engine(
        name="test",
        block_defs=[
            RuntimeBlockDef(
                key="main",
                tier=Tier.always,
                format_fn=lambda data, sit: f"Value: {data}",
            ),
        ],
        budget=500,
    )

    text, manifest = engine.assemble(
        entity_id="player-1",
        data={"main": 42},
    )

    assert "Value: 42" in text
    assert manifest.entity_id == "player-1"
    assert manifest.budget.blocks_included == 1
    assert manifest.total_blocks_considered == 1


def test_budget_exclusion():
    from context_assembly_engine import RuntimeBlockDef, create_engine
    from context_assembly_engine.models import Tier

    engine = create_engine(
        name="test",
        block_defs=[
            RuntimeBlockDef(key="big", tier=Tier.always, format_fn=lambda d, s: "x" * 2000),
            RuntimeBlockDef(key="small", tier=Tier.conditional, format_fn=lambda d, s: "y"),
        ],
        budget=100,  # Very tight — only room for the small block
    )

    text, manifest = engine.assemble(
        entity_id="test",
        data={"big": True, "small": True},
    )

    # Big block should be excluded due to budget
    assert manifest.budget.blocks_excluded >= 1
    excluded = [e for e in manifest.entries if not e.included]
    assert any("budget" in (e.exclude_reason or "") for e in excluded)


def test_scoring_rules_adjust_priority():
    from context_assembly_engine import RuntimeBlockDef, ScoringRule, Situation, create_engine
    from context_assembly_engine.models import Tier

    engine = create_engine(
        name="test",
        block_defs=[
            RuntimeBlockDef(key="a", tier=Tier.conditional, format_fn=lambda d, s: str(d)),
        ],
        scoring_rules=[
            ScoringRule(
                name="boost_a",
                condition=lambda sit: sit.has_flag("boost"),
                adjustments={"a": +25},
            ),
        ],
        budget=500,
    )

    _, manifest = engine.assemble(
        entity_id="test",
        data={"a": "data"},
        mode="default",
    )
    no_boost = [e for e in manifest.entries if e.key == "a"][0]
    assert no_boost.final_priority == 60  # base priority for conditional

    engine_with_flag = create_engine(
        name="test",
        block_defs=[
            RuntimeBlockDef(key="a", tier=Tier.conditional, format_fn=lambda d, s: str(d)),
        ],
        scoring_rules=[
            ScoringRule(
                name="boost_a",
                condition=lambda sit: sit.has_flag("boost"),
                adjustments={"a": +25},
            ),
        ],
        analyze_situation=lambda data: Situation(flags={"boost": True}),
        budget=500,
    )

    _, manifest2 = engine_with_flag.assemble(
        entity_id="test",
        data={"a": "data"},
    )
    boosted = [e for e in manifest2.entries if e.key == "a"][0]
    assert boosted.final_priority == 85  # 60 + 25
    assert "rule:boost_a:+25" in boosted.signals


def test_memory_lifecycle():
    from context_assembly_engine.models import Memory, MemoryCategory, MemoryStage
    from context_assembly_engine.service import advance_memory_lifecycle

    mem = Memory(
        entity_id="player-1",
        category=MemoryCategory.behavioral_pattern,
        summary="Gets aggressive when over par",
    )
    assert mem.stage == MemoryStage.draft
    assert mem.confidence == 0.2

    # Reinforce twice → should move to reinforced
    mem = advance_memory_lifecycle(mem, reinforced=True)
    mem = advance_memory_lifecycle(mem, reinforced=True)
    assert mem.stage == MemoryStage.reinforced
    assert mem.confidence >= 0.4


def test_temporal_computation():
    from datetime import datetime, timedelta, timezone

    from context_assembly_engine.service import compute_temporal

    now = datetime.now(timezone.utc)
    values = [
        (now - timedelta(days=2), 50.0),
        (now - timedelta(days=5), 48.0),
        (now - timedelta(days=20), 42.0),
        (now - timedelta(days=60), 38.0),
    ]

    temporal = compute_temporal(values)
    assert temporal.occurrences == 4
    assert temporal.current > temporal.previous
    assert temporal.trend.value == "improving"


def test_router_mounts():
    from context_assembly_engine.router import router
    paths = [r.path for r in router.routes]
    assert "/api/v1/cae/assemble" in paths
    assert "/api/v1/cae/goals" in paths
    assert "/api/v1/cae/memories" in paths
