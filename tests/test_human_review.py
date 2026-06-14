from __future__ import annotations

from graph.workflow import build_workflow
from harness.runner import run_evaluation
from harness.test_cases import sample_candidate_case


def test_workflow_waits_for_human_review_by_default() -> None:
    result = build_workflow().invoke(sample_candidate_case())

    assert result["current_step"] == "human_review"
    assert result["human_review_required"] is True
    assert result["human_review_status"] == "pending_review"
    assert result["human_decision"] is None
    assert result["trace"][-1]["node"] == "human_review"
    assert result["trace"][0]["node"] == "supervisor"
    assert result["supervisor_plan"]["request_type"] == "candidate_evaluation"
    assert "candidate_analyst" in result["active_agents"]
    assert "reporting_agent" in result["active_agents"]


def test_workflow_records_human_review_decision() -> None:
    state = sample_candidate_case()
    state["human_decision"] = "approve"
    state["human_feedback"] = "候选人项目经历和岗位要求匹配，建议进入下一轮技术面。"

    result = build_workflow().invoke(state)

    assert result["human_review_required"] is False
    assert result["human_review_status"] == "reviewed_approve"
    assert result["human_feedback"] == "候选人项目经历和岗位要求匹配，建议进入下一轮技术面。"
    assert result["trace"][-1]["extra"]["has_feedback"] is True


def test_workflow_rejects_invalid_human_review_decision() -> None:
    result = run_evaluation(human_decision="hire_directly")

    assert result["human_review_required"] is True
    assert result["human_review_status"] == "invalid_review_decision"
    assert "Invalid human_decision: hire_directly" in result["errors"]
