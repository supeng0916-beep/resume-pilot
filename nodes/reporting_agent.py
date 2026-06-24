from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.state import WorkflowState
from harness.trace import add_trace


def reporting_agent_node(state: WorkflowState) -> WorkflowState:
    match_score = float(state.get("match_score") or 0)
    risk_score = state.get("risk_score")
    recommendation = "advance"
    rationale = "Strong match with manageable delivery risk."

    if match_score < 60:
        recommendation = "reject"
        rationale = "Overall match is low relative to the target role requirements."
    elif risk_score is not None and risk_score >= 0.5:
        recommendation = "need_more_info"
        rationale = "Candidate fit is promising but risk signals require human validation."
    elif match_score < 75:
        recommendation = "need_more_info"
        rationale = "Candidate shows partial fit and needs deeper interview verification."

    final_recommendation = {
        "recommendation": recommendation,
        "rationale": rationale,
        "match_score": match_score,
        "risk_score": risk_score,
    }
    agent_result = AgentResult(
        agent_name="reporting_agent",
        role="match_risk_recommendation",
        status="success",
        findings=final_recommendation,
        evidence_refs=[],
        confidence=0.78,
        concerns=[] if recommendation == "advance" else [rationale],
    )
    agent_updates = record_agent_result(state, agent_result)

    return {
        "final_recommendation": final_recommendation,
        **agent_updates,
        "current_step": "reporting_agent",
        "trace": add_trace(
            state,
            "reporting_agent",
            "Reporting agent consolidated match and risk into a final recommendation.",
            final_recommendation,
        ),
    }
