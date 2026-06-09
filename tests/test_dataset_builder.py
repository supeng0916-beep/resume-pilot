from __future__ import annotations

import json
from pathlib import Path

from core.dataset_builder import (
    append_annotation_record,
    generate_synthetic_dataset,
    load_jsonl,
    write_jsonl,
)


def test_generate_synthetic_dataset_is_deterministic_and_linked() -> None:
    first = generate_synthetic_dataset(count=6, seed=7)
    second = generate_synthetic_dataset(count=6, seed=7)

    assert first == second
    assert len(first.candidates) == 6
    assert len(first.jobs) == 3
    assert len(first.labels) == 6

    candidate_ids = {item["candidate_id"] for item in first.candidates}
    job_ids = {item["jd_id"] for item in first.jobs}
    for label in first.labels:
        assert label["candidate_id"] in candidate_ids
        assert label["jd_id"] in job_ids
        assert label["match_label"] in {"strong_match", "partial_match", "weak_match"}
        assert isinstance(label["needs_human_review"], bool)


def test_write_and_load_jsonl_round_trip(tmp_path: Path) -> None:
    rows = [{"id": "one", "value": 1}, {"id": "two", "value": 2}]
    output_path = tmp_path / "rows.jsonl"

    write_jsonl(output_path, rows)

    assert load_jsonl(output_path) == rows
    assert output_path.read_text(encoding="utf-8").count("\n") == 2


def test_append_annotation_record_preserves_corrected_profiles_and_labels(tmp_path: Path) -> None:
    output_path = tmp_path / "annotations.jsonl"

    record = append_annotation_record(
        output_path,
        sample_id="case_001",
        resume_id="resume_001",
        jd_id="jd_001",
        corrected_candidate_profile={"name": "脱敏候选人A", "skills": ["Python"]},
        corrected_job_profile={"title": "校招 AI 工程师"},
        labels={
            "match_label": "strong_match",
            "needs_human_review": False,
            "risk_labels": [],
            "evidence_quality": "strong",
        },
        annotator="human_001",
        notes="项目中明确使用 Python。",
    )

    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert rows == [record]
    assert record["sample_id"] == "case_001"
    assert record["corrected_candidate_profile"]["skills"] == ["Python"]
    assert record["labels"]["evidence_quality"] == "strong"
    assert record["annotation"]["annotator"] == "human_001"
    assert "created_at" in record["annotation"]
