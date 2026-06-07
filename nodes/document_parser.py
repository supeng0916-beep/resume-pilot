from __future__ import annotations

from core.schemas import DocumentMeta
from core.state import WorkflowState
from harness.trace import add_trace


def document_parser_node(state: WorkflowState) -> WorkflowState:
    resume_text = (
        "候选人：张三。5 年 Python 后端开发经验，熟悉 FastAPI、PostgreSQL、Redis，"
        "参与过 LLM 应用和数据平台项目。期望薪资 30k，当前在职，学历本科。"
    )
    document_meta = DocumentMeta(
        file_name=state.get("resume_file_path"),
        page_count=1,
        parser="mock",
        needs_ocr=False,
        text_length=len(resume_text),
    ).model_dump()
    return {
        "resume_text": resume_text,
        "document_meta": document_meta,
        "current_step": "document_parser",
        "trace": add_trace(
            state,
            "document_parser",
            "Parsed mock resume PDF into resume_text.",
            {"text_length": len(resume_text)},
        ),
    }
