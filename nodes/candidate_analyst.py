from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def candidate_analyst_node(state: WorkflowState) -> WorkflowState:
    candidate = state.get("candidate_profile") or {}
    skills = list(candidate.get("skills", []))
    experiences = list(candidate.get("work_experiences", []))
    projects = list(candidate.get("campus_projects", []))

    strengths: list[str] = []
    if skills:
        strengths.append(f"Primary skill stack includes {', '.join(skills[:4])}.")
    if experiences:
        strengths.append("Has prior work experience that can support behavioral interviewing.")
    if projects:
        strengths.append("Has project evidence available for technical deep-dive questions.")

    gaps: list[str] = []
    if not candidate.get("expected_salary"):
        gaps.append("Expected salary is missing and should be confirmed in review.")
    if not experiences and not projects:
        gaps.append("Limited concrete project/work evidence extracted from the resume.")

    insight = {
        "profile_focus": candidate.get("candidate_track", "unknown"),
        "strengths": strengths or ["Need richer candidate evidence before final recommendation."],
        "gaps": gaps,
    }
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_outputs["candidate_analyst"] = insight

    return {
        "candidate_insights": insight,
        "agent_outputs": agent_outputs,
        "current_step": "candidate_analyst",
        "trace": add_trace(
            state,
            "candidate_analyst",
            "Candidate analyst agent summarized candidate strengths and information gaps.",
            insight,
        ),
    }
