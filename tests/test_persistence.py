from __future__ import annotations

from core.persistence import SQLiteRunStore


def test_sqlite_run_store_persists_run_trace_review_and_report(tmp_path) -> None:
    db_path = tmp_path / "hr_runs.db"
    store = SQLiteRunStore(db_path)
    store.initialize()

    result = {
        "request_id": "run-001",
        "current_step": "human_review",
        "match_score": 86.5,
        "risk_score": 0.22,
        "human_review_status": "pending",
        "trace": [{"node": "matcher", "timestamp": "2026-06-09T00:00:00Z", "output_summary": "matched"}],
        "report": "# report",
        "report_quality": {"passed": True},
        "candidate_profile": {
            "name": "Candidate A",
            "education": "Bachelor",
            "years_experience": 2,
            "candidate_track": "experienced",
            "expected_salary": "25k CNY/month",
        },
        "job_profile": {
            "title": "Backend Engineer",
            "required_years": 2,
            "recruitment_track": "experienced",
            "required_skills": ["Python", "FastAPI"],
        },
    }

    store.save_workflow_result(result)

    saved = store.get_run("run-001")
    assert saved is not None
    assert saved["request_id"] == "run-001"
    assert saved["match_score"] == 86.5
    assert saved["payload"]["candidate_profile"]["name"] == "Candidate A"
    assert saved["trace"][0]["node"] == "matcher"
    assert saved["report"] == "# report"

    listed = store.list_runs(limit=5)
    assert [item["request_id"] for item in listed] == ["run-001"]

    candidate = store.get_candidate("run-001")
    assert candidate is not None
    assert candidate["name"] == "Candidate A"
    assert candidate["profile"]["education"] == "Bachelor"

    job = store.get_job("run-001")
    assert job is not None
    assert job["title"] == "Backend Engineer"
    assert job["required_skills"] == ["Python", "FastAPI"]

    trace = store.get_trace("run-001")
    assert trace[0]["node"] == "matcher"
    assert trace[0]["output_summary"] == "matched"

    report = store.get_report("run-001")
    assert report is not None
    assert report["markdown"] == "# report"
    assert report["quality"]["passed"] is True

    review = store.save_review(
        request_id="run-001",
        decision="approve",
        feedback="Looks good.",
        reviewer="hr-lead",
    )
    assert review["decision"] == "approve"
    assert store.get_run("run-001")["human_review_status"] == "reviewed_approve"
    assert store.list_reviews()[0]["feedback"] == "Looks good."


def test_sqlite_run_store_persists_batch_and_filters_runs(tmp_path) -> None:
    db_path = tmp_path / "hr_runs.db"
    store = SQLiteRunStore(db_path)
    store.initialize()

    first_result = {
        "request_id": "batch-001-001-alice",
        "current_step": "human_review",
        "match_score": 92.0,
        "risk_score": 0.12,
        "human_review_status": "pending",
        "trace": [],
        "report": "# Alice",
        "candidate_profile": {"name": "Alice"},
        "job_profile": {"title": "Backend Engineer", "required_skills": ["Python"]},
    }
    second_result = {
        "request_id": "batch-001-002-bob",
        "current_step": "human_review",
        "match_score": 70.0,
        "risk_score": 0.48,
        "human_review_status": "reviewed_reject",
        "trace": [],
        "report": "# Bob",
        "candidate_profile": {"name": "Bob"},
        "job_profile": {"title": "Backend Engineer", "required_skills": ["Python"]},
    }
    batch_result = {
        "request_id": "batch-001",
        "candidate_count": 2,
        "ranked_candidates": [
            {"candidate_id": "alice", "request_id": "batch-001-001-alice", "rank_score": 91.5},
            {"candidate_id": "bob", "request_id": "batch-001-002-bob", "rank_score": 68.2},
        ],
        "results": [first_result, second_result],
        "batch_report": "# Batch report",
    }

    for result in batch_result["results"]:
        store.save_workflow_result(result)
    store.save_batch_result(batch_result)

    pending_runs = store.list_runs(status="pending", limit=10, offset=0)
    assert [item["request_id"] for item in pending_runs] == ["batch-001-001-alice"]

    paged_runs = store.list_runs(limit=1, offset=1)
    assert len(paged_runs) == 1

    batches = store.list_batches(limit=10)
    assert batches[0]["request_id"] == "batch-001"
    assert batches[0]["candidate_count"] == 2
    assert batches[0]["top_candidate_request_id"] == "batch-001-001-alice"

    batch = store.get_batch("batch-001")
    assert batch is not None
    assert batch["ranked_candidates"][0]["candidate_id"] == "alice"
    assert batch["runs"][0]["request_id"] == "batch-001-001-alice"
