from __future__ import annotations

from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case
from nodes.parallel_specialists import parallel_specialists_node


def test_parallel_specialists_node_merges_candidate_job_and_memory_outputs() -> None:
    state = sample_candidate_case()
    state.update(
        {
            "active_agents": ["candidate_analyst", "job_analyst", "memory_agent"],
            "candidate_profile": {
                "name": "Alice",
                "education": "Bachelor",
                "years_experience": 3,
                "skills": ["Python", "FastAPI"],
                "expected_salary": "25k",
                "candidate_track": "experienced",
                "work_experiences": ["Built FastAPI services."],
            },
            "job_profile": {
                "title": "Backend Engineer",
                "required_years": 2,
                "required_skills": ["Python", "FastAPI"],
                "recruitment_track": "experienced",
            },
        }
    )

    result = parallel_specialists_node(state)

    assert "candidate_analyst" in result["agent_outputs"]
    assert "job_analyst" in result["agent_outputs"]
    assert "memory_agent" in result["agent_outputs"]
    assert result["current_step"] == "parallel_specialists"
    assert result["specialist_execution"]["mode"] == "parallel"
    assert set(result["specialist_execution"]["agents"]) == {
        "candidate_analyst",
        "job_analyst",
        "memory_agent",
    }


def test_parallel_specialists_respects_supervisor_active_agents() -> None:
    state = sample_candidate_case()
    state.update(
        {
            "active_agents": ["candidate_analyst", "job_analyst"],
            "candidate_profile": {
                "name": "Alice",
                "education": "Bachelor",
                "years_experience": 3,
                "skills": ["Python", "FastAPI"],
                "expected_salary": "25k",
                "candidate_track": "experienced",
                "work_experiences": ["Built FastAPI services."],
            },
            "job_profile": {
                "title": "Backend Engineer",
                "required_years": 2,
                "required_skills": ["Python", "FastAPI"],
                "recruitment_track": "experienced",
            },
        }
    )

    result = parallel_specialists_node(state)

    assert "candidate_analyst" in result["agent_outputs"]
    assert "job_analyst" in result["agent_outputs"]
    assert "memory_agent" not in result["agent_outputs"]
    assert result["specialist_execution"]["agents"] == [
        "candidate_analyst",
        "job_analyst",
    ]


def test_workflow_uses_parallel_specialist_dispatch() -> None:
    result = build_workflow().invoke(sample_candidate_case())
    trace_nodes = [item["node"] for item in result["trace"]]

    assert "parallel_specialists" in trace_nodes
    assert "candidate_analyst" in result["agent_outputs"]
    assert "job_analyst" in result["agent_outputs"]
    assert "memory_agent" not in result["agent_outputs"]
    assert result["specialist_execution"]["mode"] == "parallel"
