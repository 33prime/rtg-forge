# Install and Personalize a Forge Module

Take a module from rtg-forge, adapt it to the current project's codebase, and integrate it.

This is NOT a blind copy-paste. You are an AI that understands both the module's reference implementation AND the target project. You personalize the code.

## Steps

### Phase 1: Understand the Target Project
1. Read the project's CLAUDE.md (if it exists) to understand architecture, conventions, tech stack
2. Scan the project structure: where are routes? services? models? migrations? configs?
3. Identify naming conventions, existing patterns, database schema style
4. Check what's already installed (dependencies, existing modules)

### Phase 2: Read the Forge Module
5. Use the rtg-forge MCP tools to read the module:
   - Call `get_module` to read MODULE.md and module.toml
   - Read the actual source files from /Users/matt/rtg-forge/modules/{name}/
   - Read: router.py, service.py, models.py, config.py, graph/ (if exists), migrations/
6. Understand what the module does, its dependencies, its database tables, its API shape

### Phase 3: Personalization Interview
7. Ask the user targeted questions to personalize the module:
   - "What's your specific use case for this module?"
   - "What should the data model look like for YOUR domain?" (e.g., different field names, additional fields)
   - "What external services/APIs will you connect to?"
   - "Any naming changes? (e.g., 'stakeholder' → 'lead', 'enrichment' → 'research')"
   - "Should this integrate with any existing tables/models in your project?"
8. Based on answers, plan the adaptations

### Phase 4: Adapt and Install
9. Create the module directory in the target project, following the project's existing structure
   - If project uses `app/api/` → put router there
   - If project uses `app/services/` → put service there
   - If project uses flat structure → keep module as a directory
10. Adapt the code:
    - Rename entities to match the use case (stakeholder → lead, etc.)
    - Adjust Pydantic models to match the domain
    - Modify the service logic for the specific use case
    - Adapt the LangGraph pipeline prompts and nodes
    - Update database migrations with correct table/column names
    - Update config with the right env var names
    - Wire into the project's existing auth, error handling, and config patterns
11. Install Python dependencies listed in module.toml
12. Add required env vars to .env (with comments explaining each)

### Phase 5: Integrate
13. Mount the router in the project's main app (main.py, app/__init__.py, etc.)
14. Run the database migrations
15. Run the module's tests to verify integration
16. Show the user what was created and what they need to configure

## Key Principle
The forge module is a REFERENCE IMPLEMENTATION. Your job is to understand the pattern it implements and recreate that pattern personalized for this specific project. Don't just copy files — adapt them intelligently.

## Arguments
Module name: $ARGUMENTS
