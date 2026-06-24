from __future__ import annotations

from statistics import mean
from typing import Any

from core.agent_contracts import AgentResult, record_agent_result
from core.state import WorkflowState
from harness.trace import add_trace


def _agent_items(state: WorkflowState) -> list[dict[str, Any]]:
    outputs = state.get("agent_outputs") or {}
    return [item for item in outputs.values() if isinstance(item, dict)]


def _collect_list(items: list[dict[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    for item in items:
        raw = item.get(key)
        if isinstance(raw, list):
            values.extend(str(value) for value in raw if str(value).strip())
    return values


def _collect_findings_list(items: list[dict[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    for item in items:
        findings = item.get("findings") or {}
        raw = findings.get(key) if isinstance(findings, dict) else None
        if isinstance(raw, list):
            values.extend(str(value) for value in raw if str(value).strip())
    return values


def _recommendation(match_score: float, risk_score: float | None, concerns: list[str], conflicts: list[str]) -> str:
    if match_score < 60:
        return "reject"
    if conflicts or concerns:
        return "need_more_info"
    if risk_score is not None and risk_score >= 0.5:
        return "need_more_info"
    if match_score < 75:
        return "need_more_info"
    return "advance"


def consensus_agent_node(state: WorkflowState) -> WorkflowState:
    items = _agent_items(state)
    confidences = [
        float(item.get("confidence"))
        for item in items
        if isinstance(item.get("confidence"), int | float)
    ]
    concerns = _collect_list(items, "concerns")
    conflicts = _collect_findings_list(items, "conflicts")
    unsupported_skills = _collect_findings_list(items, "unsupported_skills")
    match_score = float(state.get("match_score") or 0.0)
    risk_score = state.get("risk_score")
    consensus_confidence = round(mean(confidences), 2) if confidences else 0.0

    final_recommendation = {
        "recommendation": _recommendation(match_score, risk_score, concerns, conflicts),
        "rationale": "Multi-agent consensus over candidate fit, evidence quality, and risk signals.",
        "match_score": match_score,
        "risk_score": risk_score,
        "consensus_confidence": consensus_confidence,
        "conflicts": conflicts,
        "unsupported_skills": unsupported_skills,
        "open_concerns": concerns,
    }
    agent_result = AgentResult(
        agent_name="consensus_agent",
        role="multi_agent_arbitration",
        status="success",
        findings=final_recommendation,
        evidence_refs=[],
        confidence=consensus_confidence,
        concerns=concerns,
    )
    updates = record_agent_result(state, agent_result)
    updates.update(
        {
            "final_recommendation": final_recommendation,
            "current_step": "consensus_agent",
            "trace": add_trace(
                state,
                "consensus_agent",
                "Consensus agent arbitrated specialist outputs into a final recommendation.",
                final_recommendation,
            ),
        }
    )
    return updates
