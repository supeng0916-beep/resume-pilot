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
