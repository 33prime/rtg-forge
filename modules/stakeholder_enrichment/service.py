"""Business logic for the stakeholder enrichment module.

Contains:
  - Data source functions: enrich_pdl, enrich_brightdata, enrich_firecrawl
  - Claude synthesis: synthesize_consultant, generate_psychographic_sales_intel,
    score_icp_fit, generate_project_ideas
  - Pipeline orchestrators: run_enrichment_pipeline, run_ideas_pipeline

Source file mapping from production codebase:
  - icp-service/app/services/enrichment.py  -> data source functions
  - icp-service/app/services/synthesis.py   -> Claude synthesis functions
  - icp-service/app/api/enrichment.py       -> pipeline orchestrators
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
from anthropic import AsyncAnthropic

from .config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared HTTP client
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_json(message) -> dict:
    """Extract JSON from a Claude SDK response, stripping code fences."""
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# Data Source: PeopleDataLabs
# ---------------------------------------------------------------------------


async def enrich_pdl(linkedin_url: str) -> dict:
    """Enrich a person via PeopleDataLabs API.

    Returns structured profile data: job_title, company, industry, etc.
    """
    settings = get_settings()
    if not settings.pdl_api_key:
        raise ValueError("PDL_API_KEY not configured")

    client = _get_client()
    res = await client.post(
        "https://api.peopledatalabs.com/v5/person/enrich",
        headers={"Content-Type": "application/json", "X-Api-Key": settings.pdl_api_key},
        json={"profile": linkedin_url},
    )
    if res.status_code != 200:
        raise RuntimeError(f"PDL API error {res.status_code}: {res.text}")

    data = res.json()
    return {
        "raw": data,
        "job_title": data.get("job_title"),
        "company_name": data.get("job_company_name"),
        "industry": data.get("job_company_industry"),
        "company_size": data.get("job_company_size"),
        "location": data.get("location_metro"),
        "seniority": data.get("job_title_levels"),
        "skills": (data.get("skills") or [])[:20],
        "experience": (data.get("experience") or [])[:3],
        "education": (data.get("education") or [])[:2],
    }


# ---------------------------------------------------------------------------
# Data Source: Bright Data LinkedIn Scraper
# ---------------------------------------------------------------------------


async def enrich_brightdata(linkedin_url: str) -> dict:
    """Scrape a LinkedIn profile via Bright Data Web Scraper API.

    Uses trigger + poll pattern: POST to start scrape, then poll snapshot for results.
    Gotcha: BD uses 'position' not 'headline', 'followers' not 'followers_count',
    posts have 'title' + 'attribution' not 'text'.
    """
    settings = get_settings()
    if not settings.brightdata_api_key:
        raise ValueError("BRIGHTDATA_API_KEY not configured")

    client = _get_client()
    auth_headers = {
        "Authorization": f"Bearer {settings.brightdata_api_key}",
        "Content-Type": "application/json",
    }

    # 1. Trigger the scrape
    trigger_res = await client.post(
        "https://api.brightdata.com/datasets/v3/trigger",
        params={"dataset_id": "gd_l1viktl72bvl7bjuj0", "include_errors": "true"},
        headers=auth_headers,
        json=[{"url": linkedin_url}],
        timeout=30.0,
    )
    if trigger_res.status_code != 200:
        raise RuntimeError(f"Bright Data trigger error {trigger_res.status_code}: {trigger_res.text}")

    snapshot_id = trigger_res.json().get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"Bright Data: no snapshot_id returned: {trigger_res.text}")

    logger.info(f"Bright Data scrape started: {snapshot_id}")

    # 2. Poll for results (up to 2 minutes)
    for attempt in range(24):
        await asyncio.sleep(5)
        poll_res = await client.get(
            f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}",
            params={"format": "json"},
            headers={"Authorization": f"Bearer {settings.brightdata_api_key}"},
            timeout=15.0,
        )
        if poll_res.status_code == 200:
            results = poll_res.json()
            if isinstance(results, list) and len(results) > 0:
                profile = results[0]
                if profile.get("error"):
                    raise RuntimeError(f"Bright Data profile error: {profile.get('error')}")
                logger.info(f"Bright Data scrape complete after {(attempt + 1) * 5}s")
                return _parse_brightdata_profile(profile)
        elif poll_res.status_code != 202:
            raise RuntimeError(f"Bright Data poll error {poll_res.status_code}: {poll_res.text}")

    raise RuntimeError("Bright Data: timed out waiting for scrape results (2 min)")


def _parse_brightdata_profile(profile: dict) -> dict:
    """Extract structured fields from raw Bright Data LinkedIn response."""
    headline = profile.get("position") or profile.get("headline")
    raw_posts = (profile.get("posts") or [])[:5]
    posts = []
    for p in raw_posts:
        if isinstance(p, dict):
            posts.append({
                "text": p.get("title", "") + (" — " + p.get("attribution", "") if p.get("attribution") else ""),
                "link": p.get("link"),
                "created_at": p.get("created_at"),
                "interaction": p.get("interaction"),
            })
    return {
        "raw": profile,
        "headline": headline,
        "about": profile.get("about"),
        "posts": posts,
        "recommendations": profile.get("recommendations"),
        "certifications": profile.get("honors_and_awards"),
        "volunteer": None,
        "follower_count": profile.get("followers"),
        "experience": profile.get("experience"),
        "education": profile.get("education"),
        "current_company": profile.get("current_company"),
        "connections": profile.get("connections"),
        "activity": (profile.get("activity") or [])[:5],
    }


# ---------------------------------------------------------------------------
# Data Source: Firecrawl
# ---------------------------------------------------------------------------


async def enrich_firecrawl(website_url: str) -> dict:
    """Extract consulting firm data from a website via Firecrawl.

    Gotcha: /v1/extract is async — POST returns {success, id}, must poll GET /v1/extract/{id}.
    """
    settings = get_settings()
    if not settings.firecrawl_api_key:
        raise ValueError("FIRECRAWL_API_KEY not configured")

    client = _get_client()
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.firecrawl_api_key}",
    }

    res = await client.post(
        "https://api.firecrawl.dev/v1/extract",
        headers=auth_headers,
        json={
            "urls": [website_url],
            "prompt": (
                "Extract the following about this consulting firm: services offered, "
                "industries served, case study topics, typical client types, key "
                "differentiators, and any methodology mentions."
            ),
            "schema": {
                "type": "object",
                "properties": {
                    "services": {"type": "array", "items": {"type": "string"}},
                    "industries_served": {"type": "array", "items": {"type": "string"}},
                    "case_study_topics": {"type": "array", "items": {"type": "string"}},
                    "client_types": {"type": "array", "items": {"type": "string"}},
                    "differentiators": {"type": "array", "items": {"type": "string"}},
                    "methodology_mentions": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        timeout=60.0,
    )
    if res.status_code != 200:
        raise RuntimeError(f"Firecrawl API error {res.status_code}: {res.text}")

    json_data = res.json()

    # If data returned directly
    if json_data.get("data") and isinstance(json_data["data"], dict) and json_data["data"].get("services") is not None:
        return _parse_firecrawl_data(json_data["data"])

    # Otherwise poll for async result
    job_id = json_data.get("id")
    if not job_id:
        raise RuntimeError(f"Firecrawl: no job ID or data returned: {json_data}")

    logger.info(f"Firecrawl extract job started: {job_id}, polling for results...")
    for _ in range(24):
        await asyncio.sleep(5)
        poll_res = await client.get(
            f"https://api.firecrawl.dev/v1/extract/{job_id}",
            headers=auth_headers,
            timeout=15.0,
        )
        if poll_res.status_code != 200:
            raise RuntimeError(f"Firecrawl poll error {poll_res.status_code}: {poll_res.text}")
        poll_data = poll_res.json()
        status = poll_data.get("status")
        if status == "completed":
            return _parse_firecrawl_data(poll_data.get("data") or poll_data)
        elif status == "failed":
            raise RuntimeError(f"Firecrawl extract failed: {poll_data}")

    raise RuntimeError("Firecrawl: timed out waiting for extract results")


def _parse_firecrawl_data(data: dict) -> dict:
    return {
        "raw": data,
        "services": data.get("services"),
        "industries_served": data.get("industries_served"),
        "case_study_topics": data.get("case_study_topics"),
        "client_types": data.get("client_types"),
        "differentiators": data.get("differentiators"),
        "methodology_mentions": data.get("methodology_mentions"),
    }


# ---------------------------------------------------------------------------
# Claude Synthesis: Consultant Assessment
# ---------------------------------------------------------------------------


async def synthesize_consultant(
    app_data: dict,
    pdl_data: dict | None,
    brightdata_data: dict | None,
    firecrawl_data: dict | None,
) -> dict:
    """Produce a structured consultant assessment using Claude.

    Combines application form data, PDL profile, BrightData LinkedIn scrape,
    and Firecrawl website data into a single deep assessment.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    app_section = _build_app_section(app_data)
    pdl_section = _build_pdl_section(pdl_data)
    brightdata_section = _build_brightdata_section(brightdata_data)
    firecrawl_section = _build_firecrawl_section(firecrawl_data)

    user_prompt = f"""Analyze this beta applicant across all available data sources and produce a deep consultant assessment.

## Beta Application
{app_section}

## PeopleDataLabs Profile
{pdl_section}

## LinkedIn Profile (Bright Data Scrape)
{brightdata_section}

## Company Website (Firecrawl)
{firecrawl_section}

Output valid JSON only matching this schema:
{{
  "practice_maturity": <1-10>,
  "ai_readiness": <1-10>,
  "client_sophistication": <1-10>,
  "revenue_potential": <1-10>,
  "engagement_complexity": <1-10>,
  "primary_vertical": "<industry vertical>",
  "seniority_tier": "<solo | boutique_leader | mid_firm | enterprise>",
  "consultant_summary": "<3-4 sentence profile>",
  "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "potential_concerns": ["<concern>"],
  "recommended_approach": "<1-2 sentences>"
}}"""

    system_prompt = (
        "You are a consultant profiling engine for ReadyToGo.ai. "
        "Deeply analyze a beta applicant using all available enrichment data and produce "
        "a structured consultant assessment. Be specific and evidence-based. Output valid JSON only."
    )

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.synthesis_model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message)


# ---------------------------------------------------------------------------
# Claude Synthesis: Psychographic + Sales Intel
# ---------------------------------------------------------------------------


async def generate_psychographic_sales_intel(
    app_data: dict,
    consultant_assessment: dict,
    brightdata_data: dict | None,
    firecrawl_data: dict | None,
    pdl_data: dict | None,
) -> dict:
    """Generate psychographic profile and sales intelligence using Claude."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    assessment_section = _build_assessment_section(consultant_assessment)
    app_section = _build_app_section(app_data)
    pdl_section = _build_pdl_section(pdl_data)
    brightdata_section = _build_brightdata_section(brightdata_data)
    firecrawl_section = _build_firecrawl_section(firecrawl_data)

    user_prompt = f"""Produce a deep psychographic profile and actionable sales intelligence.

## Consultant Assessment
{assessment_section}

## Beta Application
{app_section}

## PeopleDataLabs Profile
{pdl_section}

## LinkedIn Profile
{brightdata_section}

## Company Website
{firecrawl_section}

Output valid JSON only with psychographic_profile and sales_intelligence keys."""

    system_prompt = (
        "You are a sales intelligence engine for ReadyToGo.ai. "
        "Produce psychographic profiles and actionable sales intelligence. "
        "Be specific, evidence-based, and actionable. Output valid JSON only."
    )

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.synthesis_model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message)


# ---------------------------------------------------------------------------
# Claude Synthesis: ICP Pre-Scoring
# ---------------------------------------------------------------------------


async def score_icp_fit(
    enrichment_data: dict,
    consultant_assessment: dict,
    icp_definition: dict | None,
) -> dict:
    """Score a consultant against the active ICP definition using Claude.

    Returns overall_score (0-100), fit_category, reasoning, attribute_scores.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    icp_section = "No active ICP definition available. Score based on general fit."
    if icp_definition:
        icp_section = f'Active ICP: "{icp_definition.get("name", "Unknown")}"\nAttributes: {json.dumps(icp_definition.get("attributes", {}), indent=2)}'

    user_prompt = f"""Score this consultant's fit against our ICP.

## Consultant Assessment
{json.dumps(consultant_assessment, indent=2)}

## Enrichment Summary
- Job Title: {enrichment_data.get('pdl_job_title', 'N/A')}
- Company: {enrichment_data.get('pdl_company_name', 'N/A')}
- Industry: {enrichment_data.get('pdl_industry', 'N/A')}
- Consulting Focus: {enrichment_data.get('consulting_focus', 'N/A')}

## ICP Definition
{icp_section}

Output valid JSON: overall_score (0-100), fit_category (strong_fit|moderate_fit|weak_fit|anti_pattern), reasoning, attribute_scores."""

    system_prompt = "You are an ICP scoring engine. Score consultants honestly. Output valid JSON only."

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.synthesis_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message)


# ---------------------------------------------------------------------------
# Claude Synthesis: Project Idea Generation
# ---------------------------------------------------------------------------


async def generate_project_ideas(
    app_data: dict,
    enrichment_profile: dict,
    consultant_assessment: dict | None,
) -> dict:
    """Generate 3 personalized demo project ideas from stored enrichment data.

    Returns dict with consultant_summary, primary_vertical, seniority_tier, project_ideas[3].
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    app_section = _build_app_section(app_data)
    pdl_section = _build_enrichment_pdl_section(enrichment_profile)
    brightdata_section = _build_brightdata_section({
        "headline": enrichment_profile.get("linkedin_headline"),
        "about": enrichment_profile.get("linkedin_about"),
        "posts": enrichment_profile.get("linkedin_posts"),
    })
    firecrawl_section = _build_enrichment_firecrawl_section(enrichment_profile)
    assessment_section = _build_assessment_section(consultant_assessment)

    user_prompt = f"""Propose 3 demo project ideas for this consultant.

## Beta Application
{app_section}

## PeopleDataLabs Profile
{pdl_section}

## LinkedIn Profile
{brightdata_section}

## Company Website
{firecrawl_section}

## Consultant Assessment
{assessment_section}

Output JSON with consultant_summary, primary_vertical, seniority_tier, project_ideas[3].
Each idea: rank, title, fictional_client, problem_statement, proposed_solution,
prototype_type (dashboard|assessment_tool|workflow_automation|analytics_platform|planning_tool|generator),
why_this_is_perfect, wow_factor."""

    system_prompt = (
        "You are a consultant profiling engine for ReadyToGo.ai. "
        "Propose personalized demo project ideas. Output valid JSON only."
    )

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.synthesis_model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(message)


# ---------------------------------------------------------------------------
# Section Builders
# ---------------------------------------------------------------------------


def _build_app_section(app: dict) -> str:
    return f"""- Name: {app.get('first_name', '')} {app.get('last_name', '')}
- Email: {app.get('email', 'N/A')}
- Consulting Focus: {app.get('consulting_focus', 'N/A')}
- Role for AI: {app.get('role_for_ai', 'N/A')}
- Interest Driver: {app.get('interest_driver', 'N/A')}
- AI Strategy Today: {app.get('ai_strategy_today', 'N/A')}"""


def _build_pdl_section(pdl: dict | None) -> str:
    if not pdl:
        return "No LinkedIn enrichment data available."
    raw = pdl.get("raw", pdl)
    skills = ", ".join((raw.get("skills") or [])[:15]) or "N/A"
    return f"""- Job Title: {raw.get('job_title', 'N/A')}
- Company: {raw.get('job_company_name', 'N/A')}
- Industry: {raw.get('job_company_industry', 'N/A')}
- Company Size: {raw.get('job_company_size', 'N/A')}
- Skills: {skills}"""


def _build_brightdata_section(bd: dict | None) -> str:
    if not bd:
        return "No LinkedIn scrape data available."
    headline = bd.get("headline", "N/A")
    about = (bd.get("about") or "N/A")[:800]
    return f"""- Headline: {headline}
- About: {about}
- Followers: {bd.get('follower_count', 'N/A')}"""


def _build_firecrawl_section(fc: dict | None) -> str:
    if not fc:
        return "No website data available."
    return f"""- Services: {', '.join(fc.get('services') or []) or 'N/A'}
- Industries: {', '.join(fc.get('industries_served') or []) or 'N/A'}
- Differentiators: {', '.join(fc.get('differentiators') or []) or 'N/A'}"""


def _build_enrichment_pdl_section(profile: dict) -> str:
    job_title = profile.get("pdl_job_title")
    if not job_title:
        return "No LinkedIn enrichment data available."
    return f"""- Job Title: {job_title}
- Company: {profile.get('pdl_company_name', 'N/A')}
- Industry: {profile.get('pdl_industry', 'N/A')}
- Company Size: {profile.get('pdl_company_size', 'N/A')}
- Skills: {', '.join((profile.get('pdl_skills') or [])[:15]) or 'N/A'}"""


def _build_enrichment_firecrawl_section(profile: dict) -> str:
    services = profile.get("firecrawl_services")
    if not services and not profile.get("firecrawl_data"):
        return "No website data available."
    fc_raw = profile.get("firecrawl_data") or {}
    return f"""- Services: {', '.join(services or []) or 'N/A'}
- Industries: {', '.join(profile.get('firecrawl_industries') or []) or 'N/A'}
- Differentiators: {', '.join(fc_raw.get('differentiators') or []) or 'N/A'}"""


def _build_assessment_section(assessment: dict | None) -> str:
    if not assessment:
        return "No consultant assessment available yet."
    return f"""- Practice Maturity: {assessment.get('practice_maturity', 'N/A')}/10
- AI Readiness: {assessment.get('ai_readiness', 'N/A')}/10
- Seniority Tier: {assessment.get('seniority_tier', 'N/A')}
- Summary: {assessment.get('consultant_summary', 'N/A')}"""


# ---------------------------------------------------------------------------
# Pipeline Helpers
# ---------------------------------------------------------------------------


async def _safe_enrich(fn, url: str, source_name: str) -> tuple[dict | None, str | None]:
    """Run an enrichment function, catching errors."""
    if not url:
        return None, None
    try:
        data = await fn(url)
        return data, None
    except Exception as e:
        err = f"{source_name} error: {e}"
        logger.warning(err)
        return None, err


async def _noop() -> tuple[None, None]:
    return None, None


# ---------------------------------------------------------------------------
# Legacy Pipeline: Enrichment
# ---------------------------------------------------------------------------


async def run_enrichment_pipeline(beta_application_id: str):
    """Full enrichment pipeline (non-LangGraph version).

    1. Fetch beta application from Supabase
    2. Create/update enrichment_profiles row (status: enriching)
    3. Run PDL + BrightData + Firecrawl in parallel
    4. Store raw data
    5. Claude deep synthesis -> consultant_assessment + psychographic/sales intel
    6. Claude ICP pre-score
    7. Insert icp_fit_assessments row
    8. Update status -> scored
    9. Auto-generate ideas if score >= 50
    """
    settings = get_settings()
    supabase_headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    base = settings.supabase_url + "/rest/v1"
    profile_id = None
    errors: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as sb:
            # 1. Fetch beta application
            res = await sb.get(
                f"{base}/beta_applications",
                params={"id": f"eq.{beta_application_id}", "select": "*"},
                headers=supabase_headers,
            )
            apps = res.json()
            if not apps:
                logger.error(f"Beta application not found: {beta_application_id}")
                return
            app_data = apps[0]

            # 2. Create or reset enrichment_profiles row
            res = await sb.get(
                f"{base}/enrichment_profiles",
                params={"beta_application_id": f"eq.{beta_application_id}", "select": "*"},
                headers=supabase_headers,
            )
            existing = res.json()
            if existing:
                profile = existing[0]
                profile_id = profile["id"]
                await sb.patch(
                    f"{base}/enrichment_profiles",
                    params={"id": f"eq.{profile_id}"},
                    headers=supabase_headers,
                    json={"enrichment_status": "enriching", "error_log": None, "updated_at": _now()},
                )
            else:
                res = await sb.post(
                    f"{base}/enrichment_profiles",
                    headers=supabase_headers,
                    json={"beta_application_id": beta_application_id, "enrichment_status": "enriching"},
                )
                profile = res.json()[0]
                profile_id = profile["id"]

            # 3. Parallel enrichment
            linkedin_url = app_data.get("linkedin_url", "")
            website_url = app_data.get("company_website")

            pdl_result, bd_result, fc_result = await asyncio.gather(
                _safe_enrich(enrich_pdl, linkedin_url, "PDL"),
                _safe_enrich(enrich_brightdata, linkedin_url, "BrightData"),
                _safe_enrich(enrich_firecrawl, website_url, "Firecrawl") if website_url else _noop(),
            )

            pdl_data, pdl_err = pdl_result
            bd_data, bd_err = bd_result
            fc_data, fc_err = fc_result
            for err in [pdl_err, bd_err, fc_err]:
                if err:
                    errors.append(err)

            # 4. Store raw data
            now = _now()
            update_payload = {
                "pdl_data": pdl_data.get("raw") if pdl_data else None,
                "pdl_job_title": pdl_data.get("job_title") if pdl_data else None,
                "pdl_company_name": pdl_data.get("company_name") if pdl_data else None,
                "pdl_industry": pdl_data.get("industry") if pdl_data else None,
                "pdl_company_size": pdl_data.get("company_size") if pdl_data else None,
                "pdl_location": pdl_data.get("location") if pdl_data else None,
                "pdl_seniority": pdl_data.get("seniority") if pdl_data else None,
                "pdl_skills": (pdl_data.get("skills") or [])[:20] if pdl_data else None,
                "pdl_enriched_at": now if pdl_data else None,
                "brightdata_data": bd_data.get("raw") if bd_data else None,
                "linkedin_headline": bd_data.get("headline") if bd_data else None,
                "linkedin_about": bd_data.get("about") if bd_data else None,
                "linkedin_posts": bd_data.get("posts") if bd_data else None,
                "linkedin_recommendations": bd_data.get("recommendations") if bd_data else None,
                "brightdata_enriched_at": now if bd_data else None,
                "firecrawl_data": fc_data.get("raw") if fc_data else None,
                "firecrawl_services": fc_data.get("services") if fc_data else None,
                "firecrawl_industries": fc_data.get("industries_served") if fc_data else None,
                "firecrawl_enriched_at": now if fc_data else None,
                "error_log": errors if errors else None,
                "updated_at": now,
            }
            await sb.patch(
                f"{base}/enrichment_profiles",
                params={"id": f"eq.{profile_id}"},
                headers=supabase_headers,
                json=update_payload,
            )

            # 5. Claude synthesis
            assessment = None
            try:
                assessment = await synthesize_consultant(app_data, pdl_data, bd_data, fc_data)
                try:
                    psych_sales = await generate_psychographic_sales_intel(app_data, assessment, bd_data, fc_data, pdl_data)
                    assessment["psychographic_profile"] = psych_sales.get("psychographic_profile")
                    assessment["sales_intelligence"] = psych_sales.get("sales_intelligence")
                except Exception as e:
                    logger.warning(f"Psychographic/sales intel failed (non-fatal): {e}")

                await sb.patch(
                    f"{base}/enrichment_profiles",
                    params={"id": f"eq.{profile_id}"},
                    headers=supabase_headers,
                    json={"consultant_assessment": assessment, "consultant_summary": assessment.get("consultant_summary"), "updated_at": _now()},
                )
            except Exception as e:
                errors.append(f"Synthesis error: {e}")

            # 6. ICP scoring
            icp_score_data = None
            try:
                icp_res = await sb.get(
                    f"{base}/icp_definitions",
                    params={"is_active": "eq.true", "select": "*", "limit": "1"},
                    headers=supabase_headers,
                )
                icp_defs = icp_res.json()
                icp_def = icp_defs[0] if isinstance(icp_defs, list) and icp_defs else None

                enrichment_context = {
                    "pdl_job_title": pdl_data.get("job_title") if pdl_data else None,
                    "pdl_company_name": pdl_data.get("company_name") if pdl_data else None,
                    "pdl_industry": pdl_data.get("industry") if pdl_data else None,
                    "consulting_focus": app_data.get("consulting_focus"),
                }
                icp_score_data = await score_icp_fit(enrichment_context, assessment or {}, icp_def)

                await sb.patch(
                    f"{base}/enrichment_profiles",
                    params={"id": f"eq.{profile_id}"},
                    headers=supabase_headers,
                    json={
                        "pre_call_icp_score": icp_score_data.get("overall_score"),
                        "pre_call_fit_category": icp_score_data.get("fit_category"),
                        "pre_call_icp_reasoning": icp_score_data.get("reasoning"),
                        "updated_at": _now(),
                    },
                )

                # 7. Insert icp_fit_assessments
                await sb.post(
                    f"{base}/icp_fit_assessments",
                    headers=supabase_headers,
                    json={
                        "enrichment_profile_id": profile_id,
                        "icp_definition_id": icp_def["id"] if icp_def else None,
                        "overall_score": icp_score_data.get("overall_score"),
                        "attribute_scores": icp_score_data.get("attribute_scores", {}),
                        "reasoning": icp_score_data.get("reasoning"),
                        "fit_category": icp_score_data.get("fit_category"),
                    },
                )
            except Exception as e:
                errors.append(f"ICP scoring error: {e}")

            # 8. Final status
            final_status = "scored" if assessment or icp_score_data else "enriching"
            if errors and not assessment and not icp_score_data:
                final_status = "failed"

            await sb.patch(
                f"{base}/enrichment_profiles",
                params={"id": f"eq.{profile_id}"},
                headers=supabase_headers,
                json={"enrichment_status": final_status, "error_log": errors if errors else None, "updated_at": _now()},
            )

            # 9. Auto-generate ideas if score >= 50
            icp_score = icp_score_data.get("overall_score", 0) if icp_score_data else 0
            if final_status == "scored" and icp_score >= 50:
                try:
                    await run_ideas_pipeline(profile_id)
                except Exception as e:
                    logger.error(f"Auto idea generation failed for {profile_id}: {e}")

    except Exception as e:
        logger.error(f"Enrichment pipeline crashed for {beta_application_id}: {e}", exc_info=True)
        if profile_id:
            try:
                async with httpx.AsyncClient(timeout=10.0) as sb2:
                    await sb2.patch(
                        f"{base}/enrichment_profiles",
                        params={"id": f"eq.{profile_id}"},
                        headers=supabase_headers,
                        json={"enrichment_status": "failed", "error_log": errors + [f"Pipeline crash: {e}"], "updated_at": _now()},
                    )
            except Exception:
                logger.error(f"Could not update status to failed for {profile_id}")


# ---------------------------------------------------------------------------
# Legacy Pipeline: Ideas
# ---------------------------------------------------------------------------


async def run_ideas_pipeline(enrichment_profile_id: str):
    """Project idea generation pipeline.

    1. Fetch enrichment_profiles + beta_applications
    2. Parse stored JSON fields
    3. Delete existing demo_project_ideas (idempotency)
    4. Generate ideas (retry once on failure)
    5. Insert 3 idea rows
    6. Update status -> ideas_ready
    """
    settings = get_settings()
    supabase_headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    base = settings.supabase_url + "/rest/v1"

    async with httpx.AsyncClient(timeout=30.0) as sb:
        # Fetch profile
        res = await sb.get(
            f"{base}/enrichment_profiles",
            params={"id": f"eq.{enrichment_profile_id}", "select": "*"},
            headers=supabase_headers,
        )
        profiles = res.json()
        if not profiles:
            logger.error(f"Enrichment profile not found: {enrichment_profile_id}")
            return
        profile = profiles[0]

        # Fetch beta application
        beta_app_id = profile.get("beta_application_id")
        res = await sb.get(
            f"{base}/beta_applications",
            params={"id": f"eq.{beta_app_id}", "select": "*"},
            headers=supabase_headers,
        )
        apps = res.json()
        if not apps:
            logger.error(f"Beta application not found: {beta_app_id}")
            return
        app_data = apps[0]

        # Parse JSON fields
        for field in ["pdl_data", "firecrawl_data", "linkedin_posts"]:
            val = profile.get(field)
            if isinstance(val, str):
                try:
                    profile[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    profile[field] = None

        consultant_assessment = profile.get("consultant_assessment")
        if isinstance(consultant_assessment, str):
            try:
                consultant_assessment = json.loads(consultant_assessment)
            except (json.JSONDecodeError, TypeError):
                consultant_assessment = None

        # Delete existing ideas
        await sb.delete(
            f"{base}/demo_project_ideas",
            params={"enrichment_profile_id": f"eq.{enrichment_profile_id}"},
            headers=supabase_headers,
        )

        # Generate ideas (retry once)
        ideas = None
        try:
            ideas = await generate_project_ideas(app_data, profile, consultant_assessment)
        except Exception as e:
            logger.warning(f"Idea generation first attempt failed, retrying: {e}")
            try:
                ideas = await generate_project_ideas(app_data, profile, consultant_assessment)
            except Exception as e2:
                logger.error(f"Idea generation failed after retry: {e2}")
                await sb.patch(
                    f"{base}/enrichment_profiles",
                    params={"id": f"eq.{enrichment_profile_id}"},
                    headers=supabase_headers,
                    json={"enrichment_status": "failed", "error_log": [f"Idea generation error: {e2}"], "updated_at": _now()},
                )
                return

        # Insert idea rows
        idea_rows = [
            {
                "enrichment_profile_id": enrichment_profile_id,
                "rank": idea.get("rank", idx + 1),
                "title": idea.get("title"),
                "fictional_client": idea.get("fictional_client"),
                "problem_statement": idea.get("problem_statement"),
                "proposed_solution": idea.get("proposed_solution"),
                "prototype_type": idea.get("prototype_type"),
                "why_this_is_perfect": idea.get("why_this_is_perfect"),
                "wow_factor": idea.get("wow_factor"),
            }
            for idx, idea in enumerate(ideas.get("project_ideas", []))
        ]
        if idea_rows:
            res = await sb.post(f"{base}/demo_project_ideas", headers=supabase_headers, json=idea_rows)
            if res.status_code >= 400:
                logger.error(f"Failed to insert ideas: {res.text}")

        # Update status
        await sb.patch(
            f"{base}/enrichment_profiles",
            params={"id": f"eq.{enrichment_profile_id}"},
            headers=supabase_headers,
            json={"enrichment_status": "ideas_ready", "updated_at": _now()},
        )
        logger.info(f"Ideas pipeline complete for profile {enrichment_profile_id}: {len(idea_rows)} ideas generated")
