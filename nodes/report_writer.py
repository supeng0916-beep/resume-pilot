from __future__ import annotations

from core.llm_provider import generate_report_llm_enhancement
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
    if state.get("enable_llm_report_enhancement") is False:
        return {
            "report": report,
            "current_step": "report_writer",
            "llm_enhancement_status": "LLM 报告增强已在本次运行中关闭。",
            "trace": add_trace(state, "report_writer", "Generated structured evaluation report without LLM enhancement."),
        }

    enhancement = generate_report_llm_enhancement(state, report)
    output_summary = "Generated structured evaluation report."
    if enhancement.content:
        report = f"{report}\n\n## LLM 辅助增强\n{enhancement.content}"
        output_summary = "Generated structured evaluation report with LLM enhancement."
    elif enhancement.enabled:
        output_summary = enhancement.provider_message

    return {
        "report": report,
        "current_step": "report_writer",
        "llm_enhancement_status": enhancement.provider_message,
        "trace": add_trace(state, "report_writer", output_summary),
    }
