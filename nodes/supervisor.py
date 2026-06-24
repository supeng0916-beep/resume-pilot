from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


CORE_SPECIALIST_AGENTS = [
    "candidate_analyst",
    "job_analyst",
]

REVIEW_AGENTS = [
    "evidence_auditor",
    "critic_agent",
    "consensus_agent",
]


def _append_decision(state: WorkflowState, stage: str, active_agents: list[str], skipped_agents: dict[str, str]) -> list[dict]:
    decisions = list(state.get("supervisor_decisions") or [])
    decisions.append(
        {
            "stage": stage,
            "active_agents": active_agents,
            "skipped_agents": skipped_agents,
        }
    )
    return decisions


def _memory_agent_needed(state: WorkflowState) -> bool:
    return bool(
        state.get("feedback_memory_path")
        or state.get("feedback_memory_records")
        or state.get("feedback_memory_summaries")
        or state.get("use_feedback_memory")
    )


def supervisor_node(state: WorkflowState) -> WorkflowState:
    request_type = state.get("request_type") or "candidate_evaluation"
    active_agents = list(CORE_SPECIALIST_AGENTS)
    skipped_agents: dict[str, str] = {}
    if _memory_agent_needed(state):
        active_agents.append("memory_agent")
    else:
        skipped_agents["memory_agent"] = "No feedback memory source was configured for this request."

    active_agents.extend(REVIEW_AGENTS)
    plan = {
        "request_type": request_type,
        "objective": "Produce an explainable candidate evaluation with human-review checkpoints.",
        "ordered_agents": active_agents,
        "specialist_route": [
            agent
            for agent in active_agents
            if agent in {"candidate_analyst", "job_analyst", "memory_agent"}
        ],
        "review_route": list(REVIEW_AGENTS),
        "skipped_agents": skipped_agents,
        "handoff_rules": {
            "validation_failure": "retry_resume_extractor_or_fail_report",
            "high_risk_or_missing_context": "human_review",
        },
    }
    return {
        "request_type": request_type,
        "active_agents": active_agents,
        "supervisor_plan": plan,
        "supervisor_decisions": _append_decision(state, "initial_plan", active_agents, skipped_agents),
        "current_step": "supervisor",
        "trace": add_trace(
            state,
            "supervisor",
            "Supervisor agent planned the evaluation and selected required agents.",
            plan,
        ),
    }


def supervisor_review_router_node(state: WorkflowState) -> WorkflowState:
    plan = dict(state.get("supervisor_plan") or {})
    match_breakdown = state.get("match_breakdown") or {}
    matched_skills = list(match_breakdown.get("matched_skills") or [])
    risk_score = state.get("risk_score")
    match_score = float(state.get("match_score") or 0.0)

    review_route = ["consensus_agent"]
    skipped_agents: dict[str, str] = {}

    if matched_skills:
        review_route.insert(0, "evidence_auditor")
        review_route.insert(1, "critic_agent")
    else:
        skipped_agents["evidence_auditor"] = "No matched skills were available for evidence grounding."

    needs_pre_evidence_critic = (
        (risk_score is not None and float(risk_score) >= 0.5)
        or 55 <= match_score < 75
    )
    if needs_pre_evidence_critic and "critic_agent" not in review_route:
        review_route.insert(-1, "critic_agent")
    elif not needs_pre_evidence_critic and "evidence_auditor" not in review_route:
        skipped_agents["critic_agent"] = "No risk, threshold, evidence, or ambiguity signal required critique."

    active_agents = [
        agent
        for agent in list(state.get("active_agents") or [])
        if agent not in {"evidence_auditor", "critic_agent", "consensus_agent"}
    ]
    active_agents.extend(agent for agent in review_route if agent not in active_agents)
    plan["review_route"] = review_route
    plan["skipped_agents"] = {**dict(plan.get("skipped_agents") or {}), **skipped_agents}

    return {
        "active_agents": active_agents,
        "supervisor_plan": plan,
        "supervisor_decisions": _append_decision(state, "review_plan", active_agents, skipped_agents),
        "current_step": "supervisor_review_router",
        "trace": add_trace(
            state,
            "supervisor_review_router",
            "Supervisor selected the review route after matching and risk evaluation.",
            {"review_route": review_route, "skipped_agents": skipped_agents},
        ),
    }
