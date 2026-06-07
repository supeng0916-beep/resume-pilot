from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.state import WorkflowState


DEFAULT_FEEDBACK_MEMORY_PATH = "memory/review_feedback.json"


def jd_fingerprint(jd_text: str | None) -> str:
    normalized = " ".join((jd_text or "").lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def build_feedback_record(state: WorkflowState) -> dict[str, Any]:
    job = state.get("job_profile") or {}
    candidate = state.get("candidate_profile") or {}
    scoring_rubric = state.get("scoring_rubric") or {}

    return {
        "request_id": state.get("request_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job": {
            "title": job.get("title"),
            "recruitment_track": job.get("recruitment_track", "unknown"),
            "jd_fingerprint": jd_fingerprint(state.get("jd_text")),
        },
        "candidate": {
            "track": candidate.get("candidate_track", "unknown"),
            "track_confidence": candidate.get("track_confidence", 0),
        },
        "evaluation": {
            "match_score": state.get("match_score"),
            "risk_score": state.get("risk_score"),
            "rubric_track": scoring_rubric.get("track", "unknown"),
        },
        "human_review": {
            "decision": state.get("human_decision"),
            "feedback": state.get("human_feedback"),
        },
    }


def append_feedback_record(path: str | Path, record: dict[str, Any]) -> None:
    memory_path = Path(path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    if memory_path.exists():
        records = json.loads(memory_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError(f"feedback memory must contain a JSON list: {memory_path}")
    else:
        records = []

    records.append(record)
    memory_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_feedback_records(path: str | Path) -> list[dict[str, Any]]:
    memory_path = Path(path)
    if not memory_path.exists():
        return []

    records = json.loads(memory_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"feedback memory must contain a JSON list: {memory_path}")
    return [record for record in records if isinstance(record, dict)]


def retrieve_feedback_records(
    state: WorkflowState,
    *,
    path: str | Path | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    records = load_feedback_records(path or DEFAULT_FEEDBACK_MEMORY_PATH)
    job = state.get("job_profile") or {}
    current_title = job.get("title")
    current_track = job.get("recruitment_track", "unknown")
    current_fingerprint = jd_fingerprint(state.get("jd_text"))

    scored_records: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        record_job = record.get("job") or {}
        score = 0
        if record_job.get("jd_fingerprint") == current_fingerprint:
            score += 100
        if current_title and record_job.get("title") == current_title:
            score += 20
        if current_track != "unknown" and record_job.get("recruitment_track") == current_track:
            score += 10
        if score > 0:
            scored_records.append((score, record))

    scored_records.sort(
        key=lambda item: (
            item[0],
            str(item[1].get("created_at") or ""),
        ),
        reverse=True,
    )
    return [record for _, record in scored_records[:limit]]


def summarize_feedback_records(records: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for record in records:
        review = record.get("human_review") or {}
        job = record.get("job") or {}
        decision = review.get("decision") or "unknown"
        feedback = review.get("feedback") or "无文字反馈"
        title = job.get("title") or "未知岗位"
        summaries.append(f"{title} 历史反馈：决策={decision}；反馈={feedback}")
    return summaries
