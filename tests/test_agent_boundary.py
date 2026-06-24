from __future__ import annotations

from graph.routing import route_after_evidence_audit, route_after_review_supervisor
from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case


def test_workflow_uses_consensus_instead_of_reporting_agent() -> None:
    result = build_workflow().invoke(sample_candidate_case())
    trace_nodes = [item["node"] for item in result["trace"]]

    assert "reporting_agent" not in trace_nodes
    assert "consensus_agent" in trace_nodes
    assert "consensus_agent" in result["agent_outputs"]
    assert "reporting_agent" not in result["agent_outputs"]
    assert result["final_recommendation"]["recommendation"] in {
        "advance",
        "reject",
        "need_more_info",
    }


def test_supervisor_plan_lists_only_core_specialist_agents() -> None:
    result = build_workflow().invoke(sample_candidate_case())

    assert result["active_agents"] == [
        "candidate_analyst",
        "job_analyst",
        "evidence_auditor",
        "critic_agent",
        "consensus_agent",
    ]
    assert "reporting_agent" not in result["supervisor_plan"]["ordered_agents"]


def test_supervisor_routes_memory_agent_only_when_feedback_memory_is_configured() -> None:
    state = sample_candidate_case()
    state["feedback_memory_path"] = "data/test_outputs/nonexistent_feedback_memory.jsonl"

    result = build_workflow().invoke(state)

    assert "memory_agent" in result["supervisor_plan"]["ordered_agents"]
    assert "memory_agent" in result["agent_outputs"]
    assert "memory_agent" in result["specialist_execution"]["agents"]


def test_review_supervisor_skips_evidence_auditor_when_no_matched_skills_exist() -> None:
    assert route_after_review_supervisor(
        {
            "active_agents": ["consensus_agent"],
            "supervisor_plan": {"review_route": ["consensus_agent"]},
        }
    ) == "consensus_agent"


def test_review_supervisor_routes_supported_low_risk_case_directly_to_consensus() -> None:
    assert route_after_evidence_audit(
        {
            "active_agents": ["evidence_auditor", "consensus_agent"],
            "agent_outputs": {
                "evidence_auditor": {
                    "findings": {
                        "unsupported_skills": [],
                        "weak_skills": [],
                    },
                    "concerns": [],
                    "confidence": 1.0,
                }
            },
        }
    ) == "consensus_agent"


def test_review_supervisor_routes_evidence_gaps_to_critic() -> None:
    assert route_after_evidence_audit(
        {
            "active_agents": ["evidence_auditor", "critic_agent", "consensus_agent"],
            "agent_outputs": {
                "evidence_auditor": {
                    "findings": {
                        "unsupported_skills": ["Redis"],
                        "weak_skills": [],
                    },
                    "concerns": ["Redis lacks direct evidence."],
                    "confidence": 0.5,
                }
            },
        }
    ) == "critic_agent"
