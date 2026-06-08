from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.control_cabin import (
    build_ranking_rows,
    candidates_needing_review,
    safe_uploaded_filename,
    save_batch_report,
    save_uploaded_resumes,
)


@dataclass
class FakeUpload:
    name: str
    content: bytes

    def getbuffer(self) -> memoryview:
        return memoryview(self.content)


def test_safe_uploaded_filename_keeps_upload_inside_target_directory() -> None:
    assert safe_uploaded_filename("../resume.pdf") == "resume.pdf"
    assert safe_uploaded_filename("..\\resume.pdf") == "resume.pdf"


def test_save_uploaded_resumes_writes_files_under_request_dir() -> None:
    upload_dir = Path("data/test_outputs/control_cabin_upload_test")
    try:
        paths = save_uploaded_resumes(
            [FakeUpload(name="../alice.pdf", content=b"%PDF-1.7")],
            request_id="batch-001",
            upload_dir=upload_dir,
        )

        saved_path = Path(paths[0])
        assert saved_path.read_bytes() == b"%PDF-1.7"
        assert saved_path.parent == upload_dir / "batch-001"
        assert saved_path.name == "001_alice.pdf"
    finally:
        import shutil

        shutil.rmtree(upload_dir, ignore_errors=True)


def test_build_ranking_rows_and_review_queue() -> None:
    batch_result = {
        "ranked_candidates": [
            {
                "candidate_id": "alice",
                "name": "Alice",
                "track": "campus",
                "rank_score": 81.2,
                "match_score": 88,
                "risk_score": 0.12,
                "evidence_confidence": 0.9,
                "needs_ocr": False,
                "human_review_status": "pending",
                "matched_skills": ["Python", "PyTorch"],
                "review_reasons": [],
            },
            {
                "candidate_id": "scan",
                "name": "未知候选人",
                "track": "unknown",
                "rank_score": 0,
                "match_score": 0,
                "risk_score": 0.5,
                "evidence_confidence": 0,
                "needs_ocr": True,
                "human_review_status": "pending",
                "matched_skills": [],
                "review_reasons": ["PDF 需要 OCR"],
            },
        ]
    }

    rows = build_ranking_rows(batch_result)
    review_needed = candidates_needing_review(batch_result)

    assert rows[0]["排名"] == 1
    assert rows[0]["匹配技能"] == "Python, PyTorch"
    assert rows[1]["OCR复核"] == "是"
    assert review_needed[0]["candidate_id"] == "scan"


def test_save_batch_report_writes_markdown() -> None:
    report_dir = Path("data/test_outputs/control_cabin_report_test")
    try:
        path = save_batch_report(
            {"batch_report": "# 批量候选人评估汇总"},
            request_id="batch-001",
            report_dir=report_dir,
        )

        assert path.name == "batch-001_batch_report.md"
        assert path.read_text(encoding="utf-8") == "# 批量候选人评估汇总"
    finally:
        import shutil

        shutil.rmtree(report_dir, ignore_errors=True)
