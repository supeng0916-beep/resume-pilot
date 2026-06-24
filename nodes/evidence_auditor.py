from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.state import WorkflowState
from harness.trace import add_trace


def evidence_auditor_node(state: WorkflowState) -> WorkflowState:
    candidate = state.get("candidate_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}
    matched_skills = list(match_breakdown.get("matched_skills") or [])
    evidence_by_skill = {
        str(item.get("skill", "")).lower(): item
        for item in candidate.get("skill_evidence", [])
        if isinstance(item, dict)
    }

    supported_skills: list[str] = []
    unsupported_skills: list[str] = []
    weak_skills: list[str] = []
    for skill in matched_skills:
        evidence = evidence_by_skill.get(str(skill).lower())
        strength = (evidence or {}).get("evidence_strength")
        if strength in {"strong", "medium"}:
            supported_skills.append(skill)
        elif strength == "weak":
            weak_skills.append(skill)
        else:
            unsupported_skills.append(skill)

    total = max(len(matched_skills), 1)
    confidence = round((len(supported_skills) + len(weak_skills) * 0.5) / total, 2)
    concerns = []
    if unsupported_skills:
        concerns.append("Matched skills lack direct resume evidence: " + ", ".join(unsupported_skills))
    if weak_skills:
        concerns.append("Matched skills have weak evidence: " + ", ".join(weak_skills))

    result = AgentResult(
        agent_name="evidence_auditor",
        role="resume_evidence_grounding",
        status="success",
        findings={
            "supported_skills": supported_skills,
            "weak_skills": weak_skills,
            "unsupported_skills": unsupported_skills,
        },
        evidence_refs=[],
        confidence=confidence,
        concerns=concerns,
    )
    updates = record_agent_result(state, result)
    updates.update(
        {
            "current_step": "evidence_auditor",
            "trace": add_trace(
                state,
                "evidence_auditor",
                "Evidence auditor checked matched skills against resume evidence.",
                result.findings,
            ),
        }
    )
    return updates
