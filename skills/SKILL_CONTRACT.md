# RTG Forge Skill Contract

This document defines the structure, schema, and resolution rules for all skills in the RTG Forge system. Every skill MUST comply with this contract to be loaded by the skill resolver.

---

## Directory Structure

Every skill lives in a directory under `skills/<category>/<skill-name>/`. The required and optional contents are:

### Required Files

| File/Dir | Purpose |
|---|---|
| `SKILL.md` | The skill content itself — patterns, rules, examples, anti-patterns. This is what gets injected into context. |
| `meta.toml` | Machine-readable metadata — tier, category, tags, priority, relationships, optimization tracking. |
| `examples/good/` | At least one file demonstrating the **correct** application of the skill. Must contain a minimum of 1 file. |
| `examples/bad/` | At least one file demonstrating the **incorrect** version (anti-patterns). Must contain a minimum of 1 file. |

### Optional Files

| File/Dir | Purpose |
|---|---|
| `tests/` | Automated tests that validate skill examples compile, lint, or pass assertions. |

### Naming Conventions

- Skill directory names use `kebab-case` (e.g., `python-clean-architecture`)
- Example files should clearly indicate what they demonstrate (e.g., `service_example.py`, `migration_example.sql`)
- Good and bad examples should share the same filename to make comparison easy

---

## meta.toml Schema

Every skill MUST have a `meta.toml` file with the following structure:

```toml
[skill]
name = "human-readable-skill-name"
version = "0.1.0"
tier = "foundation"          # foundation | specialized | workflow
category = "stack"            # stack | practices | workflows
relevance_tags = ["tag1", "tag2"]
priority_weight = 85          # 0-100, higher = more important
description = "One-line description of what this skill teaches."

[relationships]
prerequisites = []            # Skills that MUST be loaded before this one
complements = []              # Skills that work well alongside this one
supersedes = []               # Skills this one replaces (for migration/deprecation)

[optimization]
last_optimized = "2026-02-11" # Date of last content review
token_count = 0               # Current token count of SKILL.md
token_count_previous = 0      # Token count before last edit
growth_justified = true       # Was the last size increase justified?

[tracking]
common_mistakes = []          # Frequently observed violations of this skill
```

### Field Definitions

#### `[skill]` Section

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Human-readable name, typically matching the directory name |
| `version` | string | yes | Semver version. Bump minor for content changes, major for structural changes. |
| `tier` | enum | yes | `foundation` = core patterns loaded for most tasks; `specialized` = loaded when tags match; `workflow` = multi-step process skills |
| `category` | enum | yes | `stack` = technology-specific; `practices` = cross-cutting engineering practices; `workflows` = multi-step operational patterns |
| `relevance_tags` | array[string] | yes | Tags used by the resolver to match skills to the current task context. Be specific. |
| `priority_weight` | integer | yes | 0-100. Controls loading order when multiple skills match. Higher = loaded first, more likely to survive context trimming. |
| `description` | string | yes | One-line summary. Used in skill listings and resolver logging. |

#### `[relationships]` Section

| Field | Type | Required | Description |
|---|---|---|---|
| `prerequisites` | array[string] | yes | Skill names that MUST be loaded before this skill. The resolver will auto-include them. |
| `complements` | array[string] | yes | Skills that pair well. The resolver MAY suggest loading them together. |
| `supersedes` | array[string] | yes | Skills this one replaces. Superseded skills are excluded when this skill is loaded. |

#### `[optimization]` Section

| Field | Type | Required | Description |
|---|---|---|---|
| `last_optimized` | string (date) | yes | ISO date of the last content review/optimization pass. |
| `token_count` | integer | yes | Approximate token count of the current SKILL.md content. |
| `token_count_previous` | integer | yes | Token count before the last edit. Used to track growth. |
| `growth_justified` | boolean | yes | Whether the last size increase was justified by new patterns or corrections. |

#### `[tracking]` Section

| Field | Type | Required | Description |
|---|---|---|---|
| `common_mistakes` | array[string] | yes | List of mistakes frequently observed in code that this skill addresses. Used for proactive detection. |

---

## Skill Resolution Order

When the system needs to determine which skills to load for a given task, it follows this resolution process:

### Step 1: Profile Matching

If a developer profile is active (e.g., `profiles/matt.toml`), the profile specifies:
- A base set of always-loaded skills
- Technology preferences that bias tag matching
- Excluded skills (things the developer already knows cold)

### Step 2: Context Tag Extraction

The resolver analyzes the current task context (file paths, language, frameworks mentioned, task description) and extracts a set of relevance tags.

### Step 3: Skill Scoring

Each skill is scored based on:

1. **Tag overlap** — How many of the skill's `relevance_tags` match the extracted context tags
2. **Priority weight** — The `priority_weight` from meta.toml acts as a multiplier
3. **Tier bonus** — `foundation` skills get a +10 bonus, `specialized` get +0, `workflow` get -5 (they're only loaded when explicitly relevant)
4. **Profile affinity** — Skills listed in the active profile get a boost

### Step 4: Dependency Resolution

For every skill selected for loading:
1. Check `prerequisites` — load those skills first (recursively)
2. Check `complements` — if a complement is already scored above threshold, include it
3. Check `supersedes` — remove any superseded skills from the load set

### Step 5: Context Budget Trimming

If the total token count of selected skills exceeds the context budget:
1. Sort by final score (descending)
2. Drop the lowest-scoring skills until the budget is met
3. Never drop a skill that is a prerequisite of a still-loaded skill

### Step 6: Injection Order

Skills are injected into context in this order:
1. `foundation` tier (sorted by priority_weight descending)
2. `specialized` tier (sorted by priority_weight descending)
3. `workflow` tier (sorted by priority_weight descending)

Within each tier, prerequisites are always injected before dependents.

---

## Adding a New Skill

1. Create the directory: `skills/<category>/<skill-name>/`
2. Write `meta.toml` following the schema above
3. Write `SKILL.md` with the actual skill content
4. Add at least one good example in `examples/good/`
5. Add at least one bad example in `examples/bad/`
6. Set `token_count` in meta.toml to the approximate token count of SKILL.md
7. Run validation: ensure meta.toml parses, required files exist, examples are non-empty

## Updating a Skill

1. Edit `SKILL.md` with the changes
2. Update `token_count_previous` to the old `token_count`
3. Update `token_count` to the new count
4. Set `growth_justified` to `true` only if the size increase adds genuine value
5. Bump the `version` (minor for content, major for structural changes)
6. Update `last_optimized` to today's date
