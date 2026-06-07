from __future__ import annotations

from graph.workflow import build_workflow
from harness.evaluator import evaluate_report_quality, evaluate_workflow_result
from harness.runner import run_evaluation
from harness.test_cases import sample_candidate_case


def test_evaluate_workflow_result_accepts_complete_report() -> None:
    result = build_workflow().invoke(sample_candidate_case())

    quality = evaluate_workflow_result(result)

    assert quality.passed is True
    assert quality.score == 1.0
    assert quality.missing_requirements == []


def test_evaluate_report_quality_detects_missing_sections() -> None:
    report = """
# 招聘评估报告
## 候选人摘要
候选人信息完整。

## 评分结论
- 匹配分：80
- 人工审批建议：建议进入下一轮
"""

    quality = evaluate_report_quality(report)

    assert quality.passed is False
    assert quality.score < 1.0
    assert "evidence_citations" in quality.missing_requirements
    assert "risk_points" in quality.missing_requirements
    assert "interview_questions" in quality.missing_requirements
    assert "human_review_note" in quality.missing_requirements


def test_run_evaluation_can_include_report_quality() -> None:
    result = run_evaluation(include_quality_check=True)

    assert result["report_quality"]["passed"] is True
    assert result["report_quality"]["score"] == 1.0
    assert len(result["report_quality"]["checks"]) == 6
