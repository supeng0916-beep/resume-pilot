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
        "trace": [{"node": "matcher", "output_summary": "matched"}],
        "report": "# report",
        "candidate_profile": {"name": "Candidate A"},
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
