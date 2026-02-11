"""Skill update proposer — generate SKILL.md changes from council synthesis.

Takes the council debate output and produces concrete skill update proposals
that can be turned into git branches and pull requests.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import tomli


@dataclass
class SkillProposal:
    skill_name: str
    skill_path: str
    corrections_adopted: list[dict]
    corrections_investigated: list[dict]
    proposed_additions: list[str]
    proposed_tracking_updates: list[str]
    summary: str


def _load_toml(path: Path) -> dict:
    try:
        return tomli.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def propose_from_council(council_result: dict, forge_root: Path) -> SkillProposal:
    """Generate a skill update proposal from council synthesis.

    Reads the ADOPT and INVESTIGATE corrections from the synthesis,
    and produces:
    - New patterns to add to SKILL.md
    - New common_mistakes to add to meta.toml tracking
    """
    skill_name = council_result.get("skill_name", "unknown")
    synthesis = council_result.get("synthesis", {})
    proposals = synthesis.get("proposals", [])

    # Find skill path
    skills_dir = forge_root / "skills"
    skill_path = ""
    if skills_dir.is_dir():
        for category_dir in skills_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            candidate = category_dir / skill_name
            if (candidate / "meta.toml").exists():
                skill_path = str(candidate)
                break

    adopted = [p for p in proposals if p.get("action") == "ADOPT"]
    investigated = [p for p in proposals if p.get("action") == "INVESTIGATE"]

    # Generate proposed additions to SKILL.md
    additions: list[str] = []
    for p in adopted:
        # Look up correction details from evidence
        name = p.get("correction_name", "")
        additions.append(
            f"### Correction: {name}\n"
            f"**Reasoning:** {p.get('reasoning', 'N/A')}\n"
            f"**Confidence:** {p.get('confidence', 'N/A')}\n"
        )

    # Generate tracking updates for meta.toml
    tracking_updates: list[str] = []
    for p in adopted:
        tracking_updates.append(p.get("correction_name", ""))

    summary_parts = []
    if adopted:
        summary_parts.append(f"{len(adopted)} correction(s) to adopt")
    if investigated:
        summary_parts.append(f"{len(investigated)} correction(s) to investigate")

    return SkillProposal(
        skill_name=skill_name,
        skill_path=skill_path,
        corrections_adopted=adopted,
        corrections_investigated=investigated,
        proposed_additions=additions,
        proposed_tracking_updates=tracking_updates,
        summary=", ".join(summary_parts) if summary_parts else "No changes proposed.",
    )


def proposal_to_dict(proposal: SkillProposal) -> dict:
    """Serialize a SkillProposal to a dict."""
    return {
        "skill_name": proposal.skill_name,
        "skill_path": proposal.skill_path,
        "summary": proposal.summary,
        "corrections_adopted": proposal.corrections_adopted,
        "corrections_investigated": proposal.corrections_investigated,
        "proposed_additions": proposal.proposed_additions,
        "proposed_tracking_updates": proposal.proposed_tracking_updates,
    }


def main() -> None:
    """CLI entry point: propose_skill_update <council.json> [forge-root] [output.json]."""
    if len(sys.argv) < 2:
        print("Usage: python -m forge_intelligence.propose_skill_update <council.json> [forge-root] [output.json]")
        sys.exit(1)

    council_path = Path(sys.argv[1])
    forge_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    council_result = json.loads(council_path.read_text(encoding="utf-8"))
    proposal = propose_from_council(council_result, forge_root)

    output = json.dumps(proposal_to_dict(proposal), indent=2)
    if output_path:
        output_path.write_text(output, encoding="utf-8")
        print(f"Proposal written to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
