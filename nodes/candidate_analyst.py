from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.agent_reasoning import enrich_findings_with_llm
from core.agent_skills import analyze_candidate_profile_skill
from core.state import WorkflowState
from harness.trace import add_trace


def candidate_analyst_node(state: WorkflowState) -> WorkflowState:
    candidate = state.get("candidate_profile") or {}
    insight = analyze_candidate_profile_skill(candidate)
    reasoning = enrich_findings_with_llm(
        agent_name="candidate_analyst",
        role="candidate_profile_review",
        base_findings=insight,
        context={
            "candidate_profile": candidate,
            "job_profile": state.get("job_profile") or {},
        },
    )
    insight = reasoning.findings
    gaps = list(insight.get("gaps") or [])
    concerns = gaps + [concern for concern in reasoning.concerns if concern not in gaps]
    agent_result = AgentResult(
        agent_name="candidate_analyst",
        role="candidate_profile_review",
        status="success",
        findings=insight,
        evidence_refs=[],
        confidence=0.8 if insight.get("strengths") else 0.45,
        concerns=concerns,
        token_usage=reasoning.token_usage,
        model_name=reasoning.model_name,
        provider=reasoning.provider,
    )
    agent_updates = record_agent_result(state, agent_result)

    return {
        "candidate_insights": insight,
        **agent_updates,
        "current_step": "candidate_analyst",
        "trace": add_trace(
            state,
            "candidate_analyst",
            "Candidate analyst agent summarized candidate strengths and information gaps.",
            insight,
        ),
    }
