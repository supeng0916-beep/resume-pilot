from __future__ import annotations

from core.llm_provider import LLMEnhancementResult
from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case
from nodes.report_writer import report_writer_node


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
    assert "## Agent 协作摘要" in report
    assert "## 人工复核提示" in report


def test_report_includes_recommendation_and_interview_questions() -> None:
    result = build_workflow().invoke(sample_candidate_case())
    report = result["report"]

    assert "人工审批建议" in report
    assert "请候选人" in report
    assert result["candidate_profile"]["name"] in report


def test_report_writer_appends_llm_enhancement_when_available(monkeypatch) -> None:
    state = build_workflow().invoke(sample_candidate_case())

    def fake_enhancement(state, report):
        return LLMEnhancementResult(
            enabled=True,
            content="### LLM 辅助摘要\n建议追问项目贡献边界。",
            provider_message="LLM 增强已生成。",
        )

    monkeypatch.setattr("nodes.report_writer.generate_report_llm_enhancement", fake_enhancement)
    result = report_writer_node(state)

    assert "## LLM 辅助增强" in result["report"]
    assert "建议追问项目贡献边界" in result["report"]
    assert result["llm_enhancement_status"] == "LLM 增强已生成。"


def test_report_writer_can_disable_llm_enhancement(monkeypatch) -> None:
    state = build_workflow().invoke(sample_candidate_case())
    state["enable_llm_report_enhancement"] = False

    def fail_if_called(state, report):
        raise AssertionError("LLM enhancement should not be called")

    monkeypatch.setattr("nodes.report_writer.generate_report_llm_enhancement", fail_if_called)
    result = report_writer_node(state)

    assert "## LLM 辅助增强" not in result["report"]
    assert result["llm_enhancement_status"] == "LLM 报告增强已在本次运行中关闭。"
