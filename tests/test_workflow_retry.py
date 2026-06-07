from __future__ import annotations

from graph.workflow import build_workflow
from harness.test_cases import sample_retry_exhaustion_case, sample_retry_repair_case


def test_workflow_retries_and_repairs_invalid_candidate_profile() -> None:
    result = build_workflow().invoke(sample_retry_repair_case())

    assert result["validation_errors"] == []
    assert result["retry_count"] == 1
    assert result["match_score"] >= 80
    assert result["match_breakdown"]["track"] == "experienced"
    assert "建议进入下一轮" in result["report"]

    trace_summaries = [item["output_summary"] for item in result["trace"]]
    assert any("Validation failed" in summary for summary in trace_summaries)
    assert any("Validation passed" in summary for summary in trace_summaries)
    assert any("Re-extracted corrected" in summary for summary in trace_summaries)


def test_workflow_stops_after_retry_exhaustion() -> None:
    result = build_workflow().invoke(sample_retry_exhaustion_case())

    assert result["validation_errors"]
    assert result["retry_count"] == 2
    assert result["match_score"] is None
    assert "已达到最大重试次数" in result["report"]
