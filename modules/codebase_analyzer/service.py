"""Codebase analyzer service — GitHub file fetching, Claude synthesis, Supabase persistence.

Zero framework imports. All business logic for analyzing a GitHub repo and
producing structured codebase context documents.
"""

import base64
import logging
from typing import Optional

import httpx
from anthropic import AsyncAnthropic

from .config import get_settings

logger = logging.getLogger(__name__)

# Key files to read for codebase understanding (project-specific defaults)
KEY_FILES = [
    "app/admin/page.tsx",
    "app/admin/components/AdminSidebar.tsx",
    "app/admin/types.ts",
    "app/admin/hooks/useAdminData.ts",
    "app/admin/hooks/useCallIntelligence.ts",
    "app/admin/hooks/useIcpLab.ts",
    "app/admin/hooks/useAdminFeedback.ts",
    "app/admin/hooks/useBrandGuides.ts",
    "app/admin/hooks/useEmailTemplates.ts",
    "app/admin/hooks/useContentStudio.ts",
    "app/admin/hooks/usePlaybook.ts",
    "app/admin/hooks/useCompetitiveIntel.ts",
    "icp-service/app/main.py",
    "icp-service/app/config.py",
    "icp-service/app/services/synthesis.py",
    "icp-service/app/services/enrichment.py",
]

KEY_DIRS = [
    "app/admin/components",
    "app/admin/hooks",
    "components/ui",
    "components/ui-custom",
    "icp-service/app/api",
    "icp-service/app/services",
    "icp-service/app/models",
]

ANALYSIS_SYSTEM_PROMPT = """\
You are a codebase analyst. Your job is to produce a precise, structured summary of a codebase \
that will be used as context for an AI coding assistant generating implementation instructions.

The output must be ACCURATE and SPECIFIC. Do not guess or assume — only report what you see in the code.

Generate a markdown document with these exact sections:

## 1. Architecture Overview
One paragraph describing the tech stack, deployment, and how frontend/backend connect.

## 2. File Registry
For EVERY component, hook, API route, and service file, list:
- **File path** (exact)
- **Purpose** (one line)
- **Key exports** (function/component names)

Group by: Frontend Components, Frontend Hooks, Backend API Routes, Backend Services.

## 3. Admin Sections
List every admin sidebar section with:
- Section ID and display name
- What component renders it
- What hook provides its data
- Key features already implemented (be specific — list CRUD operations, modals, filters, etc.)

## 4. Data Model
For each TypeScript interface in types.ts, list:
- Interface name
- All fields with types
- Which DB table it maps to (if obvious)

## 5. Database Constraints
List any CHECK constraints, ENUM values, or validation rules visible in the code.

## 6. Patterns & Conventions
- How hooks are structured (state, fetch, return pattern)
- How components are structured (props, state, rendering)
- How API routes are structured (router, endpoint, response)
- Styling approach (Tailwind classes, brand colors, shadcn components)
- Brand colors with hex values

## 7. Existing Features Checklist
A flat checklist of what IS and IS NOT built. Be thorough. Format:
- [x] Feature that exists
- [ ] Feature that does NOT exist

Include features like: edit modals, CRUD operations, filters, search, export, etc.

## 8. Environment & Config
List all env vars used, which service they belong to, and what they configure.

Be concise but complete. Every fact must come from the actual code provided.\
"""

INCREMENTAL_SYSTEM_PROMPT = """\
You are a codebase analyst performing an INCREMENTAL update to an existing context document.

You will receive:
1. The EXISTING context document (already accurate as of its generation date)
2. A list of files that changed since the last update, with their new contents

Your job: produce an UPDATED version of the full context document that incorporates the changes.

Rules:
- Keep the SAME section structure (## 1 through ## 8)
- Only modify sections affected by the changed files
- Add new files/components/endpoints to the registry
- Remove entries for deleted files
- Update feature checklists if new features were added
- Copy unchanged sections verbatim — do not rephrase or summarize them
- The output must be the COMPLETE updated document, not a diff\
"""


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------


def _sb_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _sb_base() -> str:
    settings = get_settings()
    return f"{settings.supabase_url}/rest/v1"


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


async def get_current_context() -> dict | None:
    """Fetch the current codebase context row from Supabase.

    Returns dict with content, generated_at, status keys, or None if no current context exists.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{_sb_base()}/codebase_context",
            params={"status": "eq.current", "select": "content,generated_at,status", "limit": "1"},
            headers=_sb_headers(),
        )
        rows = res.json()

    if not rows:
        return None
    return rows[0]


async def _get_existing_context() -> tuple[str, str] | None:
    """Fetch existing context content and generated_at timestamp. Returns None if none exists."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(
                f"{_sb_base()}/codebase_context",
                params={"status": "eq.current", "select": "content,generated_at", "limit": "1"},
                headers=_sb_headers(),
            )
            rows = res.json()
            if rows:
                return rows[0]["content"], rows[0]["generated_at"]
    except Exception as e:
        logger.warning("Failed to fetch existing context: %s", e)
    return None


async def _mark_existing_stale() -> None:
    """Mark any existing 'current' rows as 'stale'."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.patch(
            f"{_sb_base()}/codebase_context",
            params={"status": "eq.current"},
            json={"status": "stale"},
            headers=_sb_headers(),
        )


async def _store_context(context: str, model_used: str) -> None:
    """Store a new context document in Supabase."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(
            f"{_sb_base()}/codebase_context",
            json={
                "content": context,
                "status": "current",
                "model_used": model_used,
            },
            headers=_sb_headers(),
        )
        if res.status_code not in (200, 201):
            logger.error("Failed to store context: %s", res.text)


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


async def _github_get(path: str, token: str) -> Optional[dict | list]:
    """Make an authenticated GET request to the GitHub API."""
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(
            f"https://api.github.com/repos/{settings.github_repo_owner}/{settings.github_repo_name}/{path}",
            headers=headers,
        )
        if res.status_code == 200:
            return res.json()
        logger.warning("GitHub API %s returned %d", path, res.status_code)
        return None


async def _get_file_content(file_path: str, token: str) -> Optional[str]:
    """Get the decoded content of a file from GitHub."""
    data = await _github_get(f"contents/{file_path}", token)
    if data and isinstance(data, dict) and data.get("content"):
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except Exception:
            return None
    return None


async def _get_dir_listing(dir_path: str, token: str) -> list[str]:
    """Get list of filenames in a directory from GitHub."""
    data = await _github_get(f"contents/{dir_path}", token)
    if data and isinstance(data, list):
        return [item["name"] for item in data if item.get("type") == "file"]
    return []


async def _get_changed_files_since(since: str, token: str) -> list[str]:
    """Get list of changed file paths from commits since a given ISO timestamp."""
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    changed: set[str] = set()
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(
            f"https://api.github.com/repos/{settings.github_repo_owner}/{settings.github_repo_name}/commits",
            params={"since": since, "per_page": "50"},
            headers=headers,
        )
        if res.status_code != 200:
            logger.warning("Failed to fetch commits since %s: %d", since, res.status_code)
            return []

        commits = res.json()
        if not commits:
            return []

        logger.info("Found %d commits since %s", len(commits), since)

        for commit in commits:
            sha = commit["sha"]
            detail = await _github_get(f"commits/{sha}", token)
            if detail and isinstance(detail, dict):
                for f in detail.get("files", []):
                    changed.add(f["filename"])

    return list(changed)


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------


async def analyze_codebase_full(github_token: str) -> str:
    """Full codebase analysis — reads all key files, sends to Claude (Sonnet)."""
    settings = get_settings()
    logger.info("Starting FULL codebase analysis...")

    # 1. Get directory listings
    dir_listings: dict[str, list[str]] = {}
    for dir_path in KEY_DIRS:
        files = await _get_dir_listing(dir_path, github_token)
        if files:
            dir_listings[dir_path] = files
            logger.info("Listed %d files in %s", len(files), dir_path)

    # 2. Read key files
    file_contents: dict[str, str] = {}
    for file_path in KEY_FILES:
        content = await _get_file_content(file_path, github_token)
        if content:
            if len(content) > 8000:
                content = content[:8000] + "\n... (truncated)"
            file_contents[file_path] = content
            logger.info("Read %s (%d chars)", file_path, len(content))

    # 3. Also read component files (first 80 lines each)
    component_dir = "app/admin/components"
    if component_dir in dir_listings:
        for fname in dir_listings[component_dir]:
            if fname.endswith(".tsx"):
                fpath = f"{component_dir}/{fname}"
                if fpath not in file_contents:
                    content = await _get_file_content(fpath, github_token)
                    if content:
                        lines = content.split("\n")[:80]
                        file_contents[fpath] = "\n".join(lines) + "\n... (truncated)"

    # 4. Build the analysis prompt
    file_tree = "## File Tree\n\n"
    for dir_path, files in sorted(dir_listings.items()):
        file_tree += f"### {dir_path}/\n"
        for f in sorted(files):
            file_tree += f"- {f}\n"
        file_tree += "\n"

    file_dump = "## File Contents\n\n"
    for fpath, content in sorted(file_contents.items()):
        file_dump += f"### {fpath}\n```\n{content}\n```\n\n"

    user_prompt = (
        "Analyze this codebase and produce the structured summary.\n\n"
        f"{file_tree}\n{file_dump}"
    )

    # 5. Call Claude for analysis
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.codebase_full_analysis_model,
        max_tokens=8192,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    context = message.content[0].text.strip()
    logger.info("Full codebase analysis complete (%d chars)", len(context))
    return context


async def analyze_codebase_incremental(
    github_token: str, existing_context: str, since: str
) -> Optional[str]:
    """Incremental analysis — only reads changed files, uses lighter model to patch context.

    Returns None if no changes found since the given timestamp.
    """
    settings = get_settings()
    logger.info("Starting INCREMENTAL codebase analysis (since %s)...", since)

    # 1. Get changed files
    changed_paths = await _get_changed_files_since(since, github_token)
    if not changed_paths:
        logger.info("No commits since last analysis — context is up to date")
        return None

    # Filter to relevant paths
    relevant = [
        p for p in changed_paths
        if p.startswith(("app/", "components/", "icp-service/"))
        and not p.endswith((".md", ".json", ".lock", ".yml", ".yaml"))
    ]
    if not relevant:
        logger.info("Changed files are all non-code — skipping update")
        return None

    logger.info("Reading %d changed files: %s", len(relevant), relevant)

    # 2. Read changed files
    changed_contents: dict[str, str] = {}
    for fpath in relevant:
        content = await _get_file_content(fpath, github_token)
        if content:
            if len(content) > 8000:
                content = content[:8000] + "\n... (truncated)"
            changed_contents[fpath] = content
        else:
            changed_contents[fpath] = "(file deleted or not found)"

    # 3. Also refresh directory listings for changed dirs
    changed_dirs = set()
    for fpath in relevant:
        parts = fpath.rsplit("/", 1)
        if len(parts) == 2:
            changed_dirs.add(parts[0])

    dir_updates = ""
    for d in sorted(changed_dirs):
        if d in KEY_DIRS or d.startswith("app/admin/components"):
            files = await _get_dir_listing(d, github_token)
            if files:
                dir_updates += f"### {d}/\n"
                for f in sorted(files):
                    dir_updates += f"- {f}\n"
                dir_updates += "\n"

    # 4. Build incremental prompt
    changes_dump = "## Changed Files\n\n"
    for fpath, content in sorted(changed_contents.items()):
        changes_dump += f"### {fpath}\n```\n{content}\n```\n\n"

    if dir_updates:
        changes_dump += "## Updated Directory Listings\n\n" + dir_updates

    user_prompt = (
        "Here is the EXISTING codebase context document:\n\n"
        "---BEGIN EXISTING CONTEXT---\n"
        f"{existing_context}\n"
        "---END EXISTING CONTEXT---\n\n"
        f"The following files have changed since the last analysis:\n\n{changes_dump}\n"
        "Produce the COMPLETE updated context document."
    )

    # 5. Call Claude for incremental update
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.codebase_incremental_model,
        max_tokens=8192,
        system=INCREMENTAL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    context = message.content[0].text.strip()
    logger.info(
        "Incremental analysis complete (%d changed files, %d chars output)",
        len(changed_contents), len(context),
    )
    return context


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


async def run_refresh_pipeline() -> None:
    """Background task: analyze codebase and store result. Uses incremental mode when possible."""
    settings = get_settings()
    github_token = settings.github_token
    if not github_token:
        logger.error("GITHUB_TOKEN not configured — cannot analyze codebase")
        return

    try:
        existing = await _get_existing_context()

        if existing:
            existing_content, generated_at = existing
            logger.info("Found existing context from %s — trying incremental update", generated_at)

            context = await analyze_codebase_incremental(
                github_token, existing_content, generated_at
            )

            if context is None:
                logger.info("Context is already up to date — no refresh needed")
                return
        else:
            logger.info("No existing context — running full analysis")
            context = await analyze_codebase_full(github_token)

        # Mark any existing row as stale
        await _mark_existing_stale()

        # Store the new result
        model_used = settings.codebase_incremental_model if existing else settings.codebase_full_analysis_model
        await _store_context(context, model_used)

        mode = "incremental" if existing else "full"
        logger.info("Codebase context refresh complete (mode: %s)", mode)

    except Exception as e:
        logger.error("Codebase analysis failed: %s", e)
