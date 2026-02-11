# Generate CLAUDE.md

Generate a project-specific CLAUDE.md file from accumulated correction data.

## Arguments

- `$ARGUMENTS` — Optional: path to the target project (defaults to current working directory)

## Workflow

### Step 1: Detect Project Tech Stack

Scan the target project for technology indicators:

- `package.json` — Node.js dependencies, React, Vue, etc.
- `pyproject.toml` or `requirements.txt` — Python dependencies, FastAPI, Django, etc.
- `tsconfig.json` — TypeScript configuration
- `tailwind.config.*` — Tailwind CSS
- `supabase/` directory or `.env` with Supabase keys
- `vite.config.*` — Vite bundler
- Any other framework indicators

Build a list of detected technologies.

### Step 2: Match Against Forge Profile

Use `validate_against_profile` with the detected technologies to check compliance.
Use `get_profile` to load the full profile constraints.

### Step 3: Query Correction Stats

Use `get_correction_stats` to get all corrections ranked by frequency.

Filter corrections to those relevant to the detected tech stack by checking:
- `applies_to` tags match detected technologies
- `skill_applied` relates to the stack
- `themes` are relevant

### Step 4: Query Relevant Skills

Use `recommend_skills` with a task description based on the detected stack.
This identifies which skills are most relevant for this project.

### Step 5: Generate CLAUDE.md

Produce a CLAUDE.md file with the following sections:

```markdown
# CLAUDE.md

## Project Overview
[Auto-detected: tech stack, framework, key dependencies]

## Stack Constraints
[From forge profile: required/allowed/forbidden technologies]

## Patterns Claude Gets Wrong Here
[Ranked by correction frequency — most common mistakes first]

For each correction:
- What Claude tends to do (instinct pattern)
- What to do instead (corrected pattern)
- Why (brief reasoning)
- Frequency: observed N times

## Recommended Skills
[Skills from the forge that should be loaded for this project]

## Key Conventions
[Extracted from relevant skills — the most important rules]
```

### Step 6: Write and Confirm

1. Write the CLAUDE.md to the target project root (or `$ARGUMENTS` path)
2. Show the user the generated content
3. Ask if they want to customize any sections

### Notes

- The "Patterns Claude Gets Wrong Here" section is the key differentiator — it's empirical, not theoretical
- Corrections with higher frequency appear first (more common = more important)
- Only include corrections relevant to the project's tech stack
- If fewer than 5 relevant corrections exist, note that the section will improve as more corrections are captured
