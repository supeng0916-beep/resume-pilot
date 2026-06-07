from __future__ import annotations

from nodes.risk_evaluator import risk_evaluator_node


def test_risk_evaluator_flags_unknown_salary() -> None:
    result = risk_evaluator_node(
        {
            "match_score": 79.25,
            "candidate_profile": {"expected_salary": "unknown"},
            "job_profile": {"salary_range": "25k-35k CNY/month"},
            "trace": [],
        }
    )

    assert result["risk_score"] == 0.35
    assert "期望薪资未知" in result["risk_factors"][0]


def test_risk_evaluator_flags_salary_above_budget() -> None:
    result = risk_evaluator_node(
        {
            "match_score": 90,
            "candidate_profile": {"expected_salary": "40k CNY/month"},
            "job_profile": {"salary_range": "25k-35k CNY/month"},
            "trace": [],
        }
    )

    assert result["risk_score"] == 0.3
    assert "高于岗位预算上限" in result["risk_factors"][0]
