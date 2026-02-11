# Profile Contract

This document defines the structure, requirements, and resolution semantics for RTG Forge profiles.

A **profile** is a self-contained directory that declares a technology stack, its constraints, and the skills/modules available to agents working within that stack. Profiles are the primary mechanism for configuring what an AI coding agent knows, prefers, and refuses.

---

## Required Files

Every profile directory MUST contain the following files:

| File | Purpose |
|---|---|
| `profile.toml` | Identity, version, maturity, and base profile reference |
| `STACK.md` | Human-readable technology stack reference document |
| `constraints.toml` | Machine-readable required/allowed/forbidden technology declarations |

A profile missing any of these three files is **invalid** and must not be loaded.

## Optional Files and Directories

| Path | Purpose |
|---|---|
| `skills/` | Profile-scoped skill definitions (override or extend global skills) |
| `modules/` | Copy-paste code modules scoped to this profile's stack |
| `gotchas/GOTCHAS.md` | Known pitfalls, foot-guns, and edge cases for this stack |
| `intelligence/sources.toml` | Curated documentation URLs, reference material, and learning resources |

---

## profile.toml Structure

```toml
[profile]
name = "my-profile"           # Unique identifier (kebab-case, matches directory name)
display_name = "My Profile"   # Human-readable name
version = "0.1.0"             # Semver version
description = ""              # What this profile is for
maturity = "seed"             # One of: seed, development, production
vendor = ""                   # Vendor or client name (optional)
vendor_url = ""               # Vendor URL (optional)

[base]
extends = "rtg-default"       # Parent profile to inherit from ("" for root profiles)

[maintainer]
team = ""                     # Owning team
last_reviewed = ""            # ISO date of last review
```

---

## Profile Resolution

When a profile is loaded, the resolver follows this algorithm:

1. **Load the requested profile** from its directory.
2. **Check `[base].extends`** for a parent profile reference.
3. If a parent exists, **recursively load the parent profile** (and its parent, and so on).
4. **Merge from root to leaf**, applying each profile's declarations on top of its parent:
   - `constraints.toml`: Child `required` entries ADD to parent required. Child `forbidden` entries ADD to parent forbidden. Child `allowed` entries REPLACE the parent's allowed list for that category. Child `overrides` can remove inherited forbidden or required entries.
   - `STACK.md`: Child STACK.md fully replaces parent STACK.md (no merge).
   - `profile.toml`: Child values replace parent values (standard override).

### Merge Precedence

```
root profile (e.g., rtg-default)
  <- child profile (e.g., client-acme)
    <- grandchild profile (e.g., client-acme-experimental)
```

The most specific (deepest child) profile wins on conflict.

### Circular Extension Detection

The resolver MUST detect circular `extends` chains and raise an error. A profile cannot directly or indirectly extend itself.

---

## Skill Resolution Order

Skills are resolved in the following priority order (highest priority first):

1. **Profile skills** -- Skills defined in the profile's own `skills/` directory. These take absolute precedence and can override any global skill of the same name.
2. **Global skills** -- Skills defined in the top-level `skills/` directory of RTG Forge. These are available to all profiles unless overridden or forbidden.
3. **Filter forbidden** -- After merging, any skill that references or depends on a technology listed in `constraints.toml [constraints.forbidden]` is **removed** from the available skill set. This ensures agents never receive instructions for forbidden technologies.

### Resolution Example

Given:
- Global skill `setup-database` references Supabase
- Profile skill `setup-database` exists in `profiles/my-profile/skills/`
- Profile forbids MongoDB

Resolution:
1. Profile `setup-database` overrides global `setup-database` (profile wins).
2. Any global skill referencing MongoDB is filtered out (forbidden).
3. Remaining global skills are merged into the available set.

---

## Constraints Semantics

### Required

Technologies that MUST be used. Agents should actively recommend and default to these.

```toml
[constraints.required]
database = { name = "Supabase (Postgres)", reason = "Core data layer" }
```

### Allowed

Technologies that MAY be used when needed. Agents can suggest these but should not default to them over required technologies.

```toml
[constraints.allowed]
queue = ["upstash-qstash"]
```

### Forbidden

Technologies that MUST NOT be used. Agents must refuse to generate code using these and should suggest the required/allowed alternative.

```toml
[constraints.forbidden]
orm = ["sqlalchemy", "prisma", "drizzle"]
```

### Overrides

Overrides allow a child profile to remove entries inherited from a parent profile. This is the escape hatch for when a child needs to un-forbid or un-require something from its parent.

```toml
[constraints.overrides]
# Example: remove "prisma" from inherited forbidden list
# unforbid_orm = ["prisma"]
```

---

## Validation Rules

1. `profile.name` MUST match the directory name.
2. `profile.name` MUST be kebab-case.
3. `profile.maturity` MUST be one of: `seed`, `development`, `production`.
4. `profile.version` MUST be valid semver.
5. If `base.extends` references a profile, that profile MUST exist.
6. `constraints.toml` MUST have all four sections (`required`, `allowed`, `forbidden`, `overrides`), even if empty.
7. A technology MUST NOT appear in both `required` and `forbidden` within the same resolved profile (after merge). This is a fatal error.
