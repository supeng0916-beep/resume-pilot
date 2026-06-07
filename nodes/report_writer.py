from __future__ import annotations

from core.report_builder import render_markdown_report
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

    report = render_markdown_report(state)

    return {
        "report": report,
        "current_step": "report_writer",
        "trace": add_trace(state, "report_writer", "Generated structured evaluation report."),
    }
