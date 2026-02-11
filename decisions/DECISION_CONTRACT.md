# RTG Forge Decision Contract

This document defines the structure, schema, and validation rules for all decisions in the RTG Forge system. Every decision MUST comply with this contract to be discoverable by the MCP server and intelligence layer.

---

## Directory Structure

Every decision lives in a directory under `decisions/<category>/<decision-name>/`. Categories organize decisions by type:

| Category | Purpose |
|----------|---------|
| `corrections/` | Before/after records of what Claude gets wrong and what skills fix |
| `architectural/` | Technology choices, design patterns, tradeoff resolutions |

### Required Files

| File | Purpose |
|------|---------|
| `decision.toml` | Machine-readable manifest — type, severity, choice, evidence, correction data |
| `DECISION.md` | Human/AI-readable narrative — context, reasoning, examples, related decisions |

### Naming Conventions

- Decision directory names use `kebab-case` (e.g., `direct-api-in-components`)
- Names should describe the decision or correction, not the outcome
- Correction decisions should reference the anti-pattern, not the fix

---

## decision.toml Schema

Every decision MUST have a `decision.toml` file with the following structure:

### Core Decision Section

```toml
[decision]
name = "decision-name"
version = "0.1.0"
type = "correction"               # correction | architectural | pattern | tradeoff
status = "active"                  # active | superseded | deprecated
severity = "architectural"         # architectural | structural | style | correctness
description = "One-line description of the decision"
created = "2026-02-11"
last_observed = "2026-02-11"
```

### Context Section

```toml
[decision.context]
applies_to = ["react", "typescript"]  # Technology tags
profiles = ["rtg-default"]            # Relevant profiles
trigger = "Description of when this decision is relevant"
```

### Choice Section

```toml
[decision.choice]
chosen = "Description of the chosen approach"
rejected = [
  { option = "Rejected approach", reason = "Why it was rejected" },
]
```

### Evidence Section

```toml
[decision.evidence]
skills = ["skill-name"]           # Skills that informed or enforce this decision
modules = []                       # Modules where this decision applies
related_decisions = []             # Other decisions that interact with this one
```

### Correction Section (type = "correction" only)

```toml
[correction]
skill_applied = "skill-name"
instinct_pattern = "What Claude does by default without the skill"
corrected_pattern = "What the skill teaches Claude to do instead"
impact_level = "architectural"     # architectural | structural | style | correctness

[correction.frequency]
total_observations = 1
first_observed = "2026-02-11"
last_observed = "2026-02-11"
observations = [
  { date = "2026-02-11", project = "project-name", file = "file.tsx" },
]

[correction.classification]
themes = ["separation-of-concerns", "type-safety"]
origin = "model-instinct"          # model-instinct | convention-mismatch | outdated-pattern
predictability = "high"            # high | medium | low
```

---

## Field Definitions

### `[decision]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Unique identifier, matches directory name |
| `version` | string | yes | Semver version. Bump when observations or reasoning change. |
| `type` | enum | yes | `correction` = before/after skill delta; `architectural` = technology/design choice; `pattern` = recurring design pattern; `tradeoff` = explicit tradeoff analysis |
| `status` | enum | yes | `active` = current and relevant; `superseded` = replaced by another decision; `deprecated` = no longer applicable |
| `severity` | enum | yes | `architectural` = system-level impact; `structural` = file/component-level; `style` = code style/conventions; `correctness` = bug or logic error |
| `description` | string | yes | One-line summary used in listings and search |
| `created` | string (date) | yes | ISO date when decision was first recorded |
| `last_observed` | string (date) | yes | ISO date of the most recent observation |

### `[decision.context]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `applies_to` | array[string] | yes | Technology tags this decision applies to |
| `profiles` | array[string] | yes | Forge profiles where this decision is relevant |
| `trigger` | string | yes | Describes the situation that makes this decision relevant |

### `[decision.choice]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chosen` | string | yes | The approach that was selected |
| `rejected` | array[{option, reason}] | yes | Alternatives considered and why they were rejected |

### `[decision.evidence]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skills` | array[string] | yes | Skills that relate to this decision |
| `modules` | array[string] | yes | Modules where this decision has been applied |
| `related_decisions` | array[string] | yes | Other decision names that interact with this one |

### `[correction]` Section (corrections only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill_applied` | string | yes | The skill that prompted the correction |
| `instinct_pattern` | string | yes | What Claude does without the skill |
| `corrected_pattern` | string | yes | What the skill teaches |
| `impact_level` | enum | yes | Same values as severity |

### `[correction.frequency]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_observations` | integer | yes | Total times this correction has been observed |
| `first_observed` | string (date) | yes | ISO date of first observation |
| `last_observed` | string (date) | yes | ISO date of most recent observation |
| `observations` | array[{date, project, file}] | yes | Individual observation records |

### `[correction.classification]` Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `themes` | array[string] | yes | Conceptual themes (e.g., "separation-of-concerns", "type-safety") |
| `origin` | enum | yes | `model-instinct` = Claude's default behavior; `convention-mismatch` = valid but wrong for this stack; `outdated-pattern` = once-correct but now superseded |
| `predictability` | enum | yes | `high` = happens almost every time; `medium` = happens often; `low` = occasional |

---

## Validation Rules

A decision passes validation when:

1. `decision.toml` exists and parses without error
2. `DECISION.md` exists and is non-empty
3. All required fields in `[decision]` section are present
4. `type` is one of: correction, architectural, pattern, tradeoff
5. `status` is one of: active, superseded, deprecated
6. `severity` is one of: architectural, structural, style, correctness
7. If `type = "correction"`, the `[correction]` section exists with all required fields
8. `observations` array length matches `total_observations`

---

## Adding a New Decision

### Correction Type

1. Identify what Claude wrote before reading a skill (instinct pattern)
2. Identify what the skill corrected it to (corrected pattern)
3. Create directory: `decisions/corrections/<decision-name>/`
4. Write `decision.toml` with full correction metadata
5. Write `DECISION.md` with before/after examples and reasoning
6. Run validation to check compliance

### Architectural Type

1. Identify the technology or design choice being made
2. Document alternatives that were considered
3. Create directory: `decisions/architectural/<decision-name>/`
4. Write `decision.toml` with choice and evidence
5. Write `DECISION.md` with full reasoning narrative
6. Run validation to check compliance

## Updating a Decision

1. Increment `total_observations` in frequency section
2. Add new entry to `observations` array
3. Update `last_observed` date
4. Bump version if reasoning or patterns changed
5. Update DECISION.md if new examples or context emerged
