# RTG Forge — North Star

> Every project you build makes the forge smarter. Every project the forge touches builds faster. That's the flywheel.

## The One-Sentence Goal

RTG Forge is a **self-populating knowledge system** where AI extracts, stores, and applies everything learned from building software — so no pattern is ever built from scratch twice.

## Three Types of Knowledge

RTG Forge captures three distinct categories of engineering knowledge. All three must grow together for the system to compound.

| Type | Question It Answers | Format | Example |
|------|---------------------|--------|---------|
| **Skills** | *How* do we write code? | `SKILL.md` + `meta.toml` | "Always use pydantic-settings for config, never raw os.getenv" |
| **Modules** | *What* do we build? | `module.toml` + source files | A stakeholder enrichment pipeline with router, service, models, migrations |
| **Decisions** | *Why* this approach over alternatives? | `decision.toml` + `DECISION.md` | "We chose LangGraph over CrewAI because of checkpoint persistence and conditional routing" |

Skills make Claude Code write better code. Modules give it proven starting points. Decisions prevent it from repeating mistakes or revisiting rejected approaches.

## The Flywheel

```
Build a project
      │
      ▼
AI evaluates the build ──► Novel module? ──► Extract to forge
      │                 ──► Non-obvious decision? ──► Log to forge
      │                 ──► Skill gap? ──► Improve skill in forge
      ▼
Forge is smarter
      │
      ▼
Next project starts from better knowledge
      │
      ▼
Build is faster + higher quality
      │
      ▼
More signal for extraction ──► (repeat)
```

The critical property: **zero human discipline required.** The extraction happens as a natural byproduct of building, not as a separate documentation step someone has to remember to do.

## Litmus Test for Every Feature

Before adding anything to RTG Forge, it must pass these questions:

1. **Does it make the flywheel spin faster?**
   Either it helps extract knowledge from builds, helps apply knowledge to new builds, or improves the quality of stored knowledge. If it does none of these, it doesn't belong.

2. **Does it work without human discipline?**
   If a feature requires developers to remember to do something manually, it will decay. Prefer automation, defaults, and AI-driven workflows over documentation and process.

3. **Does it compound?**
   A feature that's equally useful with 5 modules and 500 modules is fine. A feature that only matters at scale and provides no value today is premature. The best features provide immediate value AND get better with scale.

4. **Is it architecturally honest?**
   Does it fit the existing contract system (TOML manifests, markdown docs, file-per-unit)? Or does it require a fundamentally different pattern that fragments the codebase? New knowledge types should follow the same structure as existing ones.

5. **Does it keep the AI in the loop?**
   RTG Forge is AI-native. Every piece of knowledge must be machine-readable and accessible via MCP. If a human can use it but Claude Code can't, it's incomplete.

## What RTG Forge Is NOT

- **Not a package manager.** Modules are copied and adapted, not installed as dependencies. The forge is a reference library, not a registry you `pip install` from.
- **Not a template generator.** Templates produce identical starting points. The forge produces *personalized* implementations — Claude reads the target project, interviews the user, and adapts the module to fit.
- **Not a documentation site.** The Explorer is a window into the knowledge, but the real consumers are AI agents building software. The docs serve Claude Code first, humans second.
- **Not a framework.** There is no runtime dependency on RTG Forge. Projects that use forge modules should have zero awareness that the forge exists once the code is adapted and integrated.

## Current State vs. North Star

### What Works Today (Phase 1)
- Module registry with standardized contracts (TOML + source + docs)
- Skills engine with tiered, categorized coding standards
- Stack profiles with recursive constraint inheritance
- MCP server giving Claude Code direct access to forge knowledge
- `/prepare-module` discovers code in a project and maps it for extraction
- `/add-module` extracts a module from a project into the forge
- `/use-module` reads the forge, interviews the user, and adapts code to a new project
- Explorer frontend for browsing modules, skills, and profiles with source viewer
- Prebuild pipeline (TOML/Markdown/source -> JSON indexes -> static frontend)

### What's Next
- **Correction capture workflow** — `/capture-correction` slash command and `record_correction` MCP tool for recording before/after deltas when Claude writes code without a skill, then rewrites with one. Each delta is a measured data point.
- **Skill evolution pipeline** — GitHub Actions with a multi-agent council (conservative, progressive, synthesizer) that debates whether accumulated corrections warrant a skill update, then proposes changes as PRs.
- **CLAUDE.md auto-generation** — `/generate-claude-md` slash command that detects a project's tech stack, queries correction data, and produces a project-specific CLAUDE.md ranked by empirical correction frequency — not hypothesized best practices.
- **Extraction scoring** — An evaluation step at the end of builds that scores for module novelty, decision novelty, and skill gaps. Proposes forge contributions when thresholds are met.
- **Auto-extraction pipeline** — Claude Code proposes module/decision/skill additions without being asked. The developer just approves or dismisses.
- **Cross-module relationships** — Understanding which modules commonly appear together, which decisions informed which module designs, which skills are prerequisites for which modules.

### The Long Game
The forge becomes a **knowledge moat**. Every project built with it deposits knowledge back. Over time, the accumulated understanding of what works, what doesn't, and why creates a compounding advantage that's impossible to replicate by starting fresh. The forge doesn't just store code — it stores *judgment*.

The end state: every project gets an auto-generated CLAUDE.md file pre-loaded with guidance ranked by empirical correction frequency. "Patterns Claude Gets Wrong Here" isn't a guess — it's measured data from every previous project with this tech stack. The CLAUDE.md gets better as more corrections accumulate, creating a flywheel where each project's mistakes improve every future project's starting point.

## The Learning Loop

The correction capture system closes the loop between using skills and improving them:

```
Claude writes code (without skill)
      │
      ▼
Skill corrects it (before/after delta)
      │
      ▼
Correction recorded (decision.toml)
      │
      ▼
Data aggregated (by skill, frequency, theme)
      │
      ▼
Council debates (conservative vs. progressive vs. synthesizer)
      │
      ▼
Skill updated (PR with evidence)
      │
      ▼
Better skill → fewer corrections → (repeat)
```

Each correction record is a measured data point: what Claude got wrong, which skill fixed it, how often it happens, and across how many projects. Over time, skills absorb the most common corrections and the correction rate drops — proof that the system is learning.

The same data feeds CLAUDE.md generation. When you run `/generate-claude-md` in a project, the resulting file contains a "Patterns Claude Gets Wrong Here" section ranked by actual observation frequency. A correction seen 10 times across 3 projects ranks higher than one seen once — empirical evidence, not opinion.

## Guiding Principles

**Start concrete, abstract later.** Build real modules from real projects before designing elaborate extraction frameworks. The patterns will emerge from usage.

**Quality over quantity.** Ten deeply documented modules with clear decisions beat a hundred shallow ones. The scoring mechanism should have a high threshold for what gets added.

**The forge serves the build, not the other way around.** If using the forge ever feels like overhead — extra steps, extra formats, extra process — something is wrong. The forge should feel like having a senior engineer's accumulated knowledge available on demand.

**TOML is the contract.** Every piece of knowledge has a machine-readable manifest. If it's not in TOML, it's not in the forge. Markdown carries the narrative; TOML carries the structure.

**Empirical over theoretical.** Correction records are measured data about what AI gets wrong. A correction observed 10 times across 3 projects is a fact; a best practice from a blog post is an opinion. The forge prioritizes evidence from actual builds over hypothesized best practices.

---

*This document is the reference point for all RTG Forge development. Update it when the vision evolves. Delete sections that no longer apply. The north star should be as maintained as the code.*
