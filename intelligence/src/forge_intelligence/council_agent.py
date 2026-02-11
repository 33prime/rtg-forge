"""Council agent — run one perspective of the skill evolution debate.

Three perspectives debate whether a skill should be updated:
- Conservative: argues for minimal changes, worries about false positives
- Progressive: argues for updating when correction data shows patterns
- Synthesizer: reads both positions, produces ADOPT/INVESTIGATE/DEFER per proposal

Each agent reads the evidence.json and produces a structured opinion.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

PERSPECTIVES = {
    "conservative",
    "progressive",
    "synthesizer",
}


@dataclass
class Proposal:
    correction_name: str
    action: str  # ADOPT | INVESTIGATE | DEFER
    reasoning: str
    confidence: str  # high | medium | low


@dataclass
class AgentOpinion:
    perspective: str
    skill_name: str
    summary: str
    proposals: list[Proposal]
    overall_recommendation: str


def run_conservative(evidence: dict) -> AgentOpinion:
    """Conservative perspective: argue for minimal changes.

    Concerns:
    - Low-frequency corrections may be noise, not signal
    - Style corrections shouldn't drive skill rewrites
    - Single-project observations don't generalize
    - Skill churn degrades trust in the system
    """
    skill_name = evidence.get("skill_name", "unknown")
    corrections = evidence.get("corrections", [])

    proposals: list[Proposal] = []
    for c in corrections:
        obs = c.get("total_observations", 0)
        projects = c.get("projects", [])
        impact = c.get("impact_level", "style")
        predictability = c.get("predictability", "low")

        if obs >= 5 and len(projects) >= 2 and impact in ("architectural", "structural"):
            action = "INVESTIGATE"
            reasoning = (
                f"Observed {obs} times across {len(projects)} projects at {impact} level. "
                "Worth investigating but verify it's not project-specific."
            )
            confidence = "medium"
        elif obs >= 10 and predictability == "high":
            action = "ADOPT"
            reasoning = (
                f"High-frequency ({obs}x), high-predictability correction. "
                "Data is strong enough despite conservative stance."
            )
            confidence = "high"
        else:
            action = "DEFER"
            reasoning = (
                f"Only {obs} observations. Need more data before modifying a skill. "
                "Risk of false positive outweighs benefit."
            )
            confidence = "medium"

        proposals.append(Proposal(
            correction_name=c.get("name", "unknown"),
            action=action,
            reasoning=reasoning,
            confidence=confidence,
        ))

    adopt_count = sum(1 for p in proposals if p.action == "ADOPT")
    investigate_count = sum(1 for p in proposals if p.action == "INVESTIGATE")

    if adopt_count > 0:
        overall = f"Cautiously support {adopt_count} adoption(s), {investigate_count} investigation(s). Defer the rest."
    elif investigate_count > 0:
        overall = f"Investigate {investigate_count} correction(s) further. No changes warranted yet."
    else:
        overall = "No changes recommended. Insufficient evidence."

    return AgentOpinion(
        perspective="conservative",
        skill_name=skill_name,
        summary=f"Reviewed {len(corrections)} corrections with conservative lens.",
        proposals=proposals,
        overall_recommendation=overall,
    )


def run_progressive(evidence: dict) -> AgentOpinion:
    """Progressive perspective: argue for updating when patterns emerge.

    Principles:
    - 3+ observations is a pattern, not noise
    - High-predictability corrections should be absorbed into skills immediately
    - Waiting for perfection means skills stay stale
    - Model-instinct corrections are the most valuable (they reveal training gaps)
    """
    skill_name = evidence.get("skill_name", "unknown")
    corrections = evidence.get("corrections", [])

    proposals: list[Proposal] = []
    for c in corrections:
        obs = c.get("total_observations", 0)
        origin = c.get("origin", "unknown")
        predictability = c.get("predictability", "low")
        impact = c.get("impact_level", "style")

        if obs >= 3 and predictability in ("high", "medium"):
            action = "ADOPT"
            reasoning = (
                f"Observed {obs} times with {predictability} predictability. "
                f"Origin: {origin}. Pattern is clear — update the skill."
            )
            confidence = "high" if obs >= 5 else "medium"
        elif obs >= 2 and origin == "model-instinct":
            action = "ADOPT"
            reasoning = (
                f"Model-instinct correction ({obs}x) — this is a training gap "
                "that will keep recurring. Proactive skill update saves future corrections."
            )
            confidence = "medium"
        elif obs >= 1 and impact == "architectural":
            action = "INVESTIGATE"
            reasoning = (
                f"Architectural-level correction, even at {obs} observation(s). "
                "High-impact patterns deserve early attention."
            )
            confidence = "low"
        else:
            action = "DEFER"
            reasoning = f"Only {obs} observation(s) at {impact} level. Monitor for now."
            confidence = "low"

        proposals.append(Proposal(
            correction_name=c.get("name", "unknown"),
            action=action,
            reasoning=reasoning,
            confidence=confidence,
        ))

    adopt_count = sum(1 for p in proposals if p.action == "ADOPT")
    overall = f"Recommend adopting {adopt_count} of {len(proposals)} corrections into the skill."

    return AgentOpinion(
        perspective="progressive",
        skill_name=skill_name,
        summary=f"Reviewed {len(corrections)} corrections with progressive lens.",
        proposals=proposals,
        overall_recommendation=overall,
    )


def run_synthesizer(
    evidence: dict,
    conservative_opinion: AgentOpinion,
    progressive_opinion: AgentOpinion,
) -> AgentOpinion:
    """Synthesizer: read both positions and produce final recommendation.

    For each correction, resolves disagreements:
    - Both ADOPT → ADOPT (high confidence)
    - Both DEFER → DEFER (high confidence)
    - Disagreement → INVESTIGATE (medium confidence), explain both sides
    """
    skill_name = evidence.get("skill_name", "unknown")
    corrections = evidence.get("corrections", [])

    # Index opinions by correction name
    conservative_by_name = {p.correction_name: p for p in conservative_opinion.proposals}
    progressive_by_name = {p.correction_name: p for p in progressive_opinion.proposals}

    proposals: list[Proposal] = []
    for c in corrections:
        name = c.get("name", "unknown")
        con = conservative_by_name.get(name)
        pro = progressive_by_name.get(name)

        if con is None or pro is None:
            proposals.append(Proposal(
                correction_name=name,
                action="INVESTIGATE",
                reasoning="Missing perspective — investigate manually.",
                confidence="low",
            ))
            continue

        if con.action == pro.action:
            # Agreement
            proposals.append(Proposal(
                correction_name=name,
                action=con.action,
                reasoning=f"Both perspectives agree: {con.action}. Conservative: {con.reasoning} Progressive: {pro.reasoning}",
                confidence="high",
            ))
        elif con.action == "ADOPT" or pro.action == "ADOPT":
            # One says adopt, other doesn't — investigate
            if con.action == "ADOPT":
                proposals.append(Proposal(
                    correction_name=name,
                    action="ADOPT",
                    reasoning=f"Even conservative recommends adoption. {con.reasoning}",
                    confidence="high",
                ))
            else:
                proposals.append(Proposal(
                    correction_name=name,
                    action="INVESTIGATE",
                    reasoning=f"Progressive recommends ADOPT but conservative says {con.action}. Investigate further. Conservative: {con.reasoning} Progressive: {pro.reasoning}",
                    confidence="medium",
                ))
        else:
            # Both defer or one investigate
            proposals.append(Proposal(
                correction_name=name,
                action="DEFER",
                reasoning=f"Neither perspective strongly advocates adoption. Conservative: {con.reasoning} Progressive: {pro.reasoning}",
                confidence="medium",
            ))

    adopt_count = sum(1 for p in proposals if p.action == "ADOPT")
    investigate_count = sum(1 for p in proposals if p.action == "INVESTIGATE")
    defer_count = sum(1 for p in proposals if p.action == "DEFER")

    overall = (
        f"Synthesis: ADOPT {adopt_count}, INVESTIGATE {investigate_count}, "
        f"DEFER {defer_count} of {len(proposals)} corrections."
    )

    return AgentOpinion(
        perspective="synthesizer",
        skill_name=skill_name,
        summary=f"Synthesized {len(corrections)} corrections from conservative and progressive positions.",
        proposals=proposals,
        overall_recommendation=overall,
    )


def opinion_to_dict(opinion: AgentOpinion) -> dict:
    """Serialize an AgentOpinion to a dict."""
    return {
        "perspective": opinion.perspective,
        "skill_name": opinion.skill_name,
        "summary": opinion.summary,
        "overall_recommendation": opinion.overall_recommendation,
        "proposals": [
            {
                "correction_name": p.correction_name,
                "action": p.action,
                "reasoning": p.reasoning,
                "confidence": p.confidence,
            }
            for p in opinion.proposals
        ],
    }


def run_council(evidence: dict) -> dict:
    """Run the full three-agent council debate.

    Returns a dict with all three opinions and the final synthesis.
    """
    conservative = run_conservative(evidence)
    progressive = run_progressive(evidence)
    synthesizer = run_synthesizer(evidence, conservative, progressive)

    return {
        "skill_name": evidence.get("skill_name", "unknown"),
        "conservative": opinion_to_dict(conservative),
        "progressive": opinion_to_dict(progressive),
        "synthesis": opinion_to_dict(synthesizer),
    }


def main() -> None:
    """CLI entry point: council_agent <evidence.json> [output.json]."""
    if len(sys.argv) < 2:
        print("Usage: python -m forge_intelligence.council_agent <evidence.json> [output.json]")
        sys.exit(1)

    evidence_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    result = run_council(evidence)

    output = json.dumps(result, indent=2)
    if output_path:
        output_path.write_text(output, encoding="utf-8")
        print(f"Council result written to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
