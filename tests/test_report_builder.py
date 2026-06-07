from __future__ import annotations

from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case


def test_report_contains_structured_sections() -> None:
    result = build_workflow().invoke(sample_candidate_case())
    report = result["report"]

    assert "# 招聘评估报告" in report
    assert "## 候选人摘要" in report
    assert "## 评分结论" in report
    assert "## 匹配亮点" in report
    assert "## 风险点" in report
    assert "## 证据引用" in report
    assert "## 建议面试问题" in report
    assert "## 人工复核提示" in report


def test_report_includes_recommendation_and_interview_questions() -> None:
    result = build_workflow().invoke(sample_candidate_case())
    report = result["report"]

    assert "人工审批建议" in report
    assert "请候选人" in report
    assert result["candidate_profile"]["name"] in report
