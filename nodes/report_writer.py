from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def report_writer_node(state: WorkflowState) -> WorkflowState:
    validation_errors = state.get("validation_errors", [])
    if validation_errors:
        report = (
            "候选人评估流程未能完成：结构化信息校验失败，且已达到最大重试次数。\n\n"
            "需要人工检查的问题：\n"
            + "\n".join(f"- {error}" for error in validation_errors)
        )
        return {
            "report": report,
            "current_step": "report_writer",
            "trace": add_trace(
                state,
                "report_writer",
                "Generated validation failure report after retry exhaustion.",
            ),
        }

    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}
    risk_factors = state.get("risk_factors", [])
    scoring_rubric = state.get("scoring_rubric") or {}
    evidence_notes = match_breakdown.get("evidence_notes", [])

    report = (
        f"候选人 {candidate.get('name')} 与岗位「{job.get('title')}」整体匹配度为 "
        f"{state.get('match_score')} 分。\n\n"
        f"评分轨道：{scoring_rubric.get('track', 'unknown')}。"
        f"{scoring_rubric.get('rationale', '')}\n"
        f"主要匹配点：{', '.join(match_breakdown.get('matched_skills', []))}。\n"
        f"证据说明：{'；'.join(evidence_notes) if evidence_notes else '暂无结构化证据说明。'}\n"
        f"风险提示：{'；'.join(risk_factors)}\n"
        "建议：可进入下一轮技术面试，重点确认项目深度、薪资预期和稳定性。"
    )

    return {
        "report": report,
        "current_step": "report_writer",
        "trace": add_trace(state, "report_writer", "Generated mock evaluation report."),
    }
