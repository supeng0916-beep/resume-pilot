from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from core.feedback_memory import DEFAULT_FEEDBACK_MEMORY_PATH, append_feedback_record, build_feedback_record
from nodes.human_review import ALLOWED_HUMAN_DECISIONS


UPLOAD_DIR = Path("data/control_cabin_uploads")
REPORT_DIR = Path("data/test_outputs")


class UploadedResume(Protocol):
    name: str

    def getbuffer(self) -> memoryview:
        ...


def safe_uploaded_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip().replace("\x00", "")
    return safe_name or "resume.pdf"


def save_uploaded_resumes(
    uploaded_files: list[UploadedResume],
    *,
    request_id: str,
    upload_dir: Path = UPLOAD_DIR,
) -> list[str]:
    run_dir = upload_dir / request_id
    run_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        filename = safe_uploaded_filename(uploaded_file.name)
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
        path = run_dir / f"{index:03d}_{filename}"
        path.write_bytes(bytes(uploaded_file.getbuffer()))
        saved_paths.append(str(path))
    return saved_paths


def build_ranking_rows(batch_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for rank, candidate in enumerate(batch_result.get("ranked_candidates", []), start=1):
        rows.append(
            {
                "排名": rank,
                "候选人": candidate.get("name"),
                "文件ID": candidate.get("candidate_id"),
                "请求ID": candidate.get("request_id"),
                "类型": candidate.get("track"),
                "综合分": candidate.get("rank_score"),
                "匹配分": candidate.get("match_score"),
                "风险分": candidate.get("risk_score"),
                "证据置信度": candidate.get("evidence_confidence"),
                "OCR复核": "是" if candidate.get("needs_ocr") else "否",
                "人工状态": candidate.get("human_review_status"),
                "匹配技能": ", ".join(candidate.get("matched_skills") or []),
                "复核原因": "; ".join(candidate.get("review_reasons") or []),
            }
        )
    return rows


def candidates_needing_review(batch_result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in batch_result.get("ranked_candidates", [])
        if candidate.get("needs_ocr")
        or candidate.get("review_reasons")
        or candidate.get("errors")
    ]


def save_batch_report(
    batch_result: dict[str, Any],
    *,
    request_id: str,
    report_dir: Path = REPORT_DIR,
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{request_id}_batch_report.md"
    report_path.write_text(batch_result.get("batch_report") or "", encoding="utf-8")
    return report_path


def apply_human_review(
    batch_result: dict[str, Any],
    *,
    request_id: str,
    decision: str,
    feedback: str,
    feedback_memory_path: str | Path | None = None,
) -> dict[str, Any]:
    if decision not in ALLOWED_HUMAN_DECISIONS:
        raise ValueError(f"invalid human review decision: {decision}")

    matching_result = next(
        (
            result
            for result in batch_result.get("results", [])
            if result.get("request_id") == request_id
        ),
        None,
    )
    if matching_result is None:
        raise ValueError(f"candidate result not found for request_id: {request_id}")

    matching_result["human_decision"] = decision
    matching_result["human_feedback"] = feedback
    matching_result["human_review_required"] = False
    matching_result["human_review_status"] = f"reviewed_{decision}"
    matching_result["persist_human_feedback"] = True
    matching_result["feedback_memory_path"] = str(feedback_memory_path or DEFAULT_FEEDBACK_MEMORY_PATH)

    record = build_feedback_record(matching_result)
    append_feedback_record(matching_result["feedback_memory_path"], record)
    matching_result["feedback_memory_record"] = record

    for candidate in batch_result.get("ranked_candidates", []):
        if candidate.get("request_id") == request_id:
            candidate["human_review_status"] = matching_result["human_review_status"]
            break

    return record
