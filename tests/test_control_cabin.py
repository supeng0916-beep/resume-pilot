from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.control_cabin import (
    apply_human_review,
    build_detail_summary,
    build_evidence_rows,
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
                "request_id": "batch-001-001-alice",
                "name": "Alice",
                "track": "campus",
                "rank_score": 81.2,
                "match_score": 88,
                "risk_score": 0.12,
                "evidence_confidence": 0.9,
                "needs_ocr": False,
                "human_review_status": "pending",
                "document_parser": "pymupdf",
                "parse_quality_score": 0.95,
                "parse_quality_flags": [],
                "llm_extraction_status": ["简历 LLM 结构化抽取成功。"],
                "matched_skills": ["Python", "PyTorch"],
                "review_reasons": [],
            },
            {
                "candidate_id": "scan",
                "request_id": "batch-001-002-scan",
                "name": "未知候选人",
                "track": "unknown",
                "rank_score": 0,
                "match_score": 0,
                "risk_score": 0.5,
                "evidence_confidence": 0,
                "needs_ocr": True,
                "human_review_status": "pending",
                "document_parser": "pymupdf+vision_llm",
                "parse_quality_score": 0.45,
                "parse_quality_flags": ["文本过短"],
                "llm_extraction_status": [],
                "matched_skills": [],
                "review_reasons": ["PDF 需要 OCR"],
            },
        ]
    }

    rows = build_ranking_rows(batch_result)
    review_needed = candidates_needing_review(batch_result)

    assert rows[0]["排名"] == 1
    assert rows[0]["请求ID"] == "batch-001-001-alice"
    assert rows[0]["匹配技能"] == "Python, PyTorch"
    assert rows[0]["解析器"] == "pymupdf"
    assert rows[0]["LLM抽取"] == "简历 LLM 结构化抽取成功。"
    assert rows[1]["质量标记"] == "文本过短"
    assert rows[1]["OCR复核"] == "是"
    assert review_needed[0]["candidate_id"] == "scan"


def test_build_detail_summary_and_evidence_rows() -> None:
    result = {
        "candidate_profile": {
            "name": "Alice",
            "candidate_track": "campus",
            "track_reason": "应届生",
            "education": "本科",
            "major": "计算机",
            "years_experience": 0,
            "skill_evidence": [
                {
                    "skill": "Python",
                    "evidence_strength": "strong",
                    "evidence": [
                        {
                            "source": "resume",
                            "section": "项目经历",
                            "text": "使用 Python 完成推荐系统项目",
                            "confidence": 0.9,
                        }
                    ],
                }
            ],
        },
        "job_profile": {"title": "校招 AI 工程师", "recruitment_track": "campus"},
        "document_meta": {
            "parser": "pymupdf",
            "parse_quality_score": 0.98,
            "parse_quality_flags": [],
        },
        "match_breakdown": {"matched_skills": ["Python"]},
        "llm_extraction_status": ["JD LLM 结构化抽取成功。"],
        "human_review_status": "pending_review",
    }

    summary = build_detail_summary(result)
    rows = build_evidence_rows(result)

    assert summary["候选人"] == "Alice"
    assert summary["解析器"] == "pymupdf"
    assert summary["LLM抽取状态"] == "JD LLM 结构化抽取成功。"
    assert rows[0]["技能"] == "Python"
    assert rows[0]["片段"] == "使用 Python 完成推荐系统项目"


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


def test_apply_human_review_persists_feedback_and_updates_status() -> None:
    memory_path = Path("data/test_outputs/control_cabin_feedback_test.json")
    batch_result = {
        "ranked_candidates": [
            {
                "candidate_id": "alice",
                "request_id": "batch-001-001-alice",
                "name": "Alice",
                "human_review_status": "pending_review",
            }
        ],
        "results": [
            {
                "request_id": "batch-001-001-alice",
                "jd_text": "招聘 Python 工程师",
                "job_profile": {"title": "Python 工程师", "recruitment_track": "campus"},
                "candidate_profile": {"candidate_track": "campus", "track_confidence": 0.8},
                "scoring_rubric": {"track": "campus"},
                "match_score": 82,
                "risk_score": 0.12,
            }
        ],
    }

    record = apply_human_review(
        batch_result,
        request_id="batch-001-001-alice",
        decision="approve",
        feedback="项目经历匹配，进入技术面。",
        feedback_memory_path=memory_path,
    )

    records = json.loads(memory_path.read_text(encoding="utf-8"))
    assert record == records[-1]
    assert record["human_review"]["decision"] == "approve"
    assert batch_result["results"][0]["human_review_status"] == "reviewed_approve"
    assert batch_result["ranked_candidates"][0]["human_review_status"] == "reviewed_approve"
