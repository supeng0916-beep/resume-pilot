from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.state import WorkflowState
from harness.trace import add_trace


def critic_agent_node(state: WorkflowState) -> WorkflowState:
    outputs = state.get("agent_outputs") or {}
    evidence = outputs.get("evidence_auditor") or {}
    findings = evidence.get("findings") if isinstance(evidence, dict) else {}
    unsupported_skills = list((findings or {}).get("unsupported_skills") or [])
    weak_skills = list((findings or {}).get("weak_skills") or [])
    match_score = float(state.get("match_score") or 0)
    risk_score = state.get("risk_score")

    conflicts: list[str] = []
    review_triggers: list[str] = []
    if match_score >= 80 and (unsupported_skills or weak_skills):
        conflicts.append("High match score depends on skills with weak evidence.")
        review_triggers.append("Verify matched skills through project deep dive.")
    if risk_score is not None and float(risk_score) >= 0.5:
        review_triggers.append("Risk score is high enough to require manual review.")
    if match_score < 60 and risk_score is not None and float(risk_score) < 0.25:
        conflicts.append("Low match score but low risk score may hide missing requirement coverage.")

    confidence = 0.65 if conflicts or review_triggers else 0.85
    result = AgentResult(
        agent_name="critic_agent",
        role="cross_agent_consistency_review",
        status="success",
        findings={
            "conflicts": conflicts,
            "review_triggers": review_triggers,
        },
        evidence_refs=[],
        confidence=confidence,
        concerns=review_triggers,
    )
    updates = record_agent_result(state, result)
    updates.update(
        {
            "current_step": "critic_agent",
            "trace": add_trace(
                state,
                "critic_agent",
                "Critic agent reviewed cross-agent consistency and manual-review triggers.",
                result.findings,
            ),
        }
    )
    return updates
