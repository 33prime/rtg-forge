Sync all forge knowledge (skills, modules, profiles, decisions) from local files to the Supabase cloud database.

## Steps

1. Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set in your environment (or `.env` file)
2. Run the sync script from the forge root:

```bash
cd $FORGE_ROOT
uv run --directory intelligence python -m forge_intelligence.sync_to_supabase
```

3. Verify the sync by checking row counts:
   - `forge_skills` — should match the number of skill directories
   - `forge_modules` — should match the number of module directories
   - `forge_profiles` — should match the number of profile directories
   - `forge_decisions` — should match the number of decision directories

## When to Use

- After adding or updating skills, modules, profiles, or decisions locally
- Before deploying the MCP server to Railway (ensures cloud data is fresh)
- As a manual alternative to the GitHub Action (which auto-syncs on push to main)
