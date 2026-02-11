# Capture Correction

Record a before/after delta — what Claude wrote without a skill vs. what the skill corrected.

## Arguments

- `$ARGUMENTS` — Optional: description of the correction to record

## Workflow

### Step 1: Identify the Delta

Ask the user (or analyze recent changes) to identify:

1. **What changed?** — The specific code or pattern that was rewritten
2. **Which skill prompted it?** — Use `get_skill` to confirm the skill exists
3. **Before (instinct pattern)** — What Claude wrote without the skill loaded
4. **After (corrected pattern)** — What the code looks like after applying the skill

If the user provides `$ARGUMENTS`, use that as the starting context. Otherwise, ask:
- "What did Claude write before the skill was applied?"
- "What did the skill correct it to?"
- "Which skill prompted this correction?"

### Step 2: Classify the Correction

Determine:

- **Severity/Impact level:**
  - `architectural` — System-level (e.g., wrong data flow pattern)
  - `structural` — File/component-level (e.g., wrong file organization)
  - `style` — Code style/conventions (e.g., naming, formatting)
  - `correctness` — Bug or logic error

- **Origin:**
  - `model-instinct` — Claude's default training behavior
  - `convention-mismatch` — Valid in general but wrong for this specific stack
  - `outdated-pattern` — Was correct before, superseded by newer practice

- **Predictability:**
  - `high` — Happens almost every time Claude encounters this situation
  - `medium` — Happens often but not always
  - `low` — Occasional

- **Themes:** Tag with relevant concepts (e.g., "separation-of-concerns", "type-safety", "caching", "error-handling")

### Step 3: Check for Duplicates

Use `search_decisions` with keywords from the instinct pattern to find existing corrections.

- If a matching correction exists, the `record_correction` tool will automatically increment its frequency counter
- If no match exists, a new correction record will be created

### Step 4: Record the Correction

Call the `record_correction` MCP tool with:

```
skill_name: <the skill that prompted the correction>
instinct_pattern: <what Claude does without the skill>
corrected_pattern: <what the skill teaches>
impact_level: <architectural|structural|style|correctness>
project: <project name where observed>
file: <file where observed>
themes: <comma-separated theme tags>
origin: <model-instinct|convention-mismatch|outdated-pattern>
predictability: <high|medium|low>
context: <any additional context>
```

### Step 5: Verify and Save Diff

1. Use `validate_decision` to ensure the record is contract-compliant
2. Use `get_decision` to show the user the full record
3. If the user has a diff available, append it to the DECISION.md file

### Output

Confirm to the user:
- Decision name and location
- Whether it was a new record or frequency increment
- Current observation count
- Suggestion to run `/generate-claude-md` once enough corrections accumulate
