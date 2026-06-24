from __future__ import annotations

from typing import Literal

from core.state import WorkflowState


ValidationRoute = Literal["retry_resume_extractor", "continue_to_matcher", "fail_to_report"]
ReviewRoute = Literal["evidence_auditor", "critic_agent", "consensus_agent"]
EvidenceAuditRoute = Literal["critic_agent", "consensus_agent"]


def route_after_validation(state: WorkflowState) -> ValidationRoute:
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 0)

    if not errors:
        return "continue_to_matcher"

    if retry_count <= max_retries:
        return "retry_resume_extractor"

    return "fail_to_report"


def route_after_review_supervisor(state: WorkflowState) -> ReviewRoute:
    review_route = list((state.get("supervisor_plan") or {}).get("review_route") or [])
    active_agents = set(state.get("active_agents") or [])

    if "evidence_auditor" in review_route and "evidence_auditor" in active_agents:
        return "evidence_auditor"
    if "critic_agent" in review_route and "critic_agent" in active_agents:
        return "critic_agent"
    return "consensus_agent"


def route_after_evidence_audit(state: WorkflowState) -> EvidenceAuditRoute:
    active_agents = set(state.get("active_agents") or [])
    if "critic_agent" not in active_agents:
        return "consensus_agent"

    evidence = (state.get("agent_outputs") or {}).get("evidence_auditor") or {}
    findings = evidence.get("findings") if isinstance(evidence, dict) else {}
    unsupported_skills = list((findings or {}).get("unsupported_skills") or [])
    weak_skills = list((findings or {}).get("weak_skills") or [])
    concerns = list(evidence.get("concerns") or []) if isinstance(evidence, dict) else []

    if unsupported_skills or weak_skills or concerns:
        return "critic_agent"
    return "consensus_agent"
