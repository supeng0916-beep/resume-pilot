from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.agent_reasoning import enrich_findings_with_llm
from core.agent_skills import analyze_job_profile_skill
from core.state import WorkflowState
from harness.trace import add_trace


def job_analyst_node(state: WorkflowState) -> WorkflowState:
    job = state.get("job_profile") or {}
    insight = analyze_job_profile_skill(job)
    reasoning = enrich_findings_with_llm(
        agent_name="job_analyst",
        role="job_requirement_review",
        base_findings=insight,
        context={
            "job_profile": job,
            "candidate_profile": state.get("candidate_profile") or {},
        },
    )
    insight = reasoning.findings
    required_skills = list(job.get("required_skills", []))
    concerns = [] if required_skills else ["Job required skills are missing or unclear."]
    concerns.extend(concern for concern in reasoning.concerns if concern not in concerns)
    agent_result = AgentResult(
        agent_name="job_analyst",
        role="job_requirement_review",
        status="success",
        findings=insight,
        evidence_refs=[],
        confidence=0.8 if required_skills else 0.45,
        concerns=concerns,
        token_usage=reasoning.token_usage,
        model_name=reasoning.model_name,
        provider=reasoning.provider,
    )
    agent_updates = record_agent_result(state, agent_result)

    return {
        "job_insights": insight,
        **agent_updates,
        "current_step": "job_analyst",
        "trace": add_trace(
            state,
            "job_analyst",
            "Job analyst agent converted the JD into evaluation priorities.",
            insight,
        ),
    }
