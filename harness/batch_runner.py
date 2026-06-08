from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from harness.runner import run_evaluation


@dataclass(frozen=True)
class BatchResumeInput:
    candidate_id: str
    resume_file_path: str | None = None
    resume_text: str | None = None


def _evidence_confidence(result: dict[str, Any]) -> float:
    candidate = result.get("candidate_profile") or {}
    skill_evidence = candidate.get("skill_evidence", [])
    if not skill_evidence:
        return 0.0

    strength_scores = {
        "strong": 1.0,
        "medium": 0.7,
        "weak": 0.4,
        "unsupported": 0.0,
    }
    scores = [
        strength_scores.get(item.get("evidence_strength", "unsupported"), 0.0)
        for item in skill_evidence
        if isinstance(item, dict)
    ]
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def calculate_rank_score(result: dict[str, Any]) -> float:
    match_score = float(result.get("match_score") or 0.0)
    risk_score = float(result.get("risk_score") or 0.0)
    evidence_score = _evidence_confidence(result) * 100
    rank_score = match_score * 0.65 + evidence_score * 0.20 - risk_score * 100 * 0.15
    return round(max(0.0, min(100.0, rank_score)), 2)


def _build_candidate_summary(candidate_id: str, result: dict[str, Any]) -> dict[str, Any]:
    candidate = result.get("candidate_profile") or {}
    match_breakdown = result.get("match_breakdown") or {}
    document_meta = result.get("document_meta") or {}
    needs_ocr = document_meta.get("needs_ocr", False)
    llm_status = result.get("llm_extraction_status") or []
    evidence_confidence = _evidence_confidence(result)
    review_reasons = []
    if needs_ocr:
        review_reasons.append("PDF 解析未获得可信文本")
    parse_quality_flags = document_meta.get("parse_quality_flags") or []
    if parse_quality_flags:
        review_reasons.append("解析质量标记：" + "; ".join(str(flag) for flag in parse_quality_flags[:3]))
    if evidence_confidence == 0:
        review_reasons.append("缺少可用于评分的技能/项目证据")
    if float(result.get("risk_score") or 0) >= 0.5:
        review_reasons.append("风险分较高")
    if result.get("errors"):
        review_reasons.append("流程存在错误")

    return {
        "candidate_id": candidate_id,
        "request_id": result.get("request_id"),
        "name": candidate.get("name", "未知候选人"),
        "track": candidate.get("candidate_track", "unknown"),
        "match_score": result.get("match_score"),
        "risk_score": result.get("risk_score"),
        "rank_score": calculate_rank_score(result),
        "evidence_confidence": evidence_confidence,
        "matched_skills": match_breakdown.get("matched_skills", []),
        "human_review_status": result.get("human_review_status"),
        "document_parser": document_meta.get("parser"),
        "parse_quality_score": document_meta.get("parse_quality_score"),
        "parse_quality_flags": document_meta.get("parse_quality_flags", []),
        "llm_extraction_status": llm_status,
        "needs_ocr": needs_ocr,
        "review_reasons": review_reasons,
        "errors": result.get("errors", []),
    }


def render_batch_report(summaries: list[dict[str, Any]], *, jd_text: str | None = None) -> str:
    eligible_candidates = [
        item
        for item in summaries
        if not item.get("needs_ocr")
        and item.get("evidence_confidence", 0) > 0
        and (item.get("matched_skills") or [])
    ]
    top_candidates = eligible_candidates[:3]
    review_needed = [
        item
        for item in summaries
        if item.get("needs_ocr")
        or item.get("evidence_confidence", 0) == 0
        or item.get("risk_score", 0) >= 0.5
        or item.get("errors")
    ]
    skill_matrix = sorted(
        {
            skill
            for item in summaries
            for skill in item.get("matched_skills", [])
        }
    )
    review_lines = [
        f"- {item['name']}（{item['candidate_id']}）：{'; '.join(item.get('review_reasons') or ['需人工确认'])}"
        for item in review_needed
    ] or ["- 暂无需要额外标记的候选人。"]
    recommendation_lines = [
        f"- {item['name']}（{item['candidate_id']}）：{', '.join(item.get('matched_skills', [])) or '暂无匹配技能'}"
        for item in top_candidates
    ] or ["- 暂无可直接推荐候选人；请先完成人工/OCR复核。"]

    sections = [
        "# 批量候选人评估汇总",
        "## JD 摘要",
        jd_text or "使用默认 JD。",
        "",
        "## 候选人排名",
        *[
            (
                f"{index}. {item['name']}（{item['candidate_id']}）："
                f"综合分 {item['rank_score']}，匹配分 {item['match_score']}，"
                f"风险分 {item['risk_score']}，证据置信度 {item['evidence_confidence']}"
            )
            for index, item in enumerate(summaries, start=1)
        ],
        "",
        "## 推荐进入下一轮",
        *recommendation_lines,
        "",
        "## 需要人工重点复核",
        *review_lines,
        "",
        "## 技能覆盖矩阵",
        *[
            f"- {skill}："
            + ", ".join(
                item["name"]
                for item in summaries
                if skill in item.get("matched_skills", [])
            )
            for skill in skill_matrix
        ],
    ]
    return "\n".join(sections)


def run_batch_evaluation(
    resumes: list[BatchResumeInput],
    *,
    jd_text: str | None = None,
    request_id: str = "batch-run",
    feedback_memory_path: str | None = None,
    risk_model_path: str | None = None,
    enable_llm_report_enhancement: bool | None = None,
    enable_llm_structured_extraction: bool | None = None,
    progress_callback: Callable[[int, int, BatchResumeInput, str], None] | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for index, resume in enumerate(resumes, start=1):
        if progress_callback:
            progress_callback(index, len(resumes), resume, "started")
        candidate_request_id = f"{request_id}-{index:03d}-{resume.candidate_id}"
        result = run_evaluation(
            resume_file_path=resume.resume_file_path,
            resume_text=resume.resume_text,
            jd_text=jd_text,
            request_id=candidate_request_id,
            feedback_memory_path=feedback_memory_path,
            risk_model_path=risk_model_path,
            enable_llm_report_enhancement=enable_llm_report_enhancement,
            enable_llm_structured_extraction=enable_llm_structured_extraction,
        )
        results.append(result)
        summaries.append(_build_candidate_summary(resume.candidate_id, result))
        if progress_callback:
            progress_callback(index, len(resumes), resume, "completed")

    ranked_summaries = sorted(
        summaries,
        key=lambda item: (
            item["rank_score"],
            item.get("match_score") or 0,
            -float(item.get("risk_score") or 0),
        ),
        reverse=True,
    )
    return {
        "request_id": request_id,
        "candidate_count": len(resumes),
        "ranked_candidates": ranked_summaries,
        "results": results,
        "batch_report": render_batch_report(ranked_summaries, jd_text=jd_text),
    }


def resume_inputs_from_paths(paths: list[str]) -> list[BatchResumeInput]:
    return [
        BatchResumeInput(candidate_id=Path(path).stem or f"candidate-{index}", resume_file_path=path)
        for index, path in enumerate(paths, start=1)
    ]
