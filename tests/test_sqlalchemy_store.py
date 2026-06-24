from __future__ import annotations

from core.sqlalchemy_store import SQLAlchemyRunStore


def test_sqlalchemy_run_store_persists_run_batch_review_and_job() -> None:
    store = SQLAlchemyRunStore("sqlite+pysqlite:///:memory:")
    store.initialize()
    result = {
        "request_id": "sa-run-001",
        "current_step": "human_review",
        "match_score": 88.0,
        "risk_score": 0.21,
        "human_review_status": "pending",
        "trace": [{"node": "supervisor", "output_summary": "planned"}],
        "report": "# report",
        "candidate_profile": {"name": "Alice", "education": "Bachelor"},
        "job_profile": {"title": "Backend Engineer", "required_skills": ["Python"]},
        "agent_metrics": {"candidate_analyst": {"status": "success", "confidence": 0.8}},
        "agent_outputs": {"candidate_analyst": {"findings": {"strengths": ["Python"]}}},
        "supervisor_decisions": [{"stage": "initial_plan", "active_agents": ["candidate_analyst"]}],
    }

    store.save_workflow_result(result)
    saved = store.get_run("sa-run-001")

    assert saved is not None
    assert saved["request_id"] == "sa-run-001"
    assert saved["agent_metrics"]["candidate_analyst"]["status"] == "success"
    assert store.get_trace("sa-run-001")[0]["node"] == "supervisor"
    assert store.get_candidate("sa-run-001")["name"] == "Alice"
    assert store.get_job("sa-run-001")["required_skills"] == ["Python"]
    assert store.get_report("sa-run-001")["markdown"] == "# report"
    assert store.get_agent_runs("sa-run-001")[0]["agent_name"] == "candidate_analyst"
    assert store.get_supervisor_decisions("sa-run-001")[0]["stage"] == "initial_plan"

    review = store.save_review(request_id="sa-run-001", decision="approve", feedback="ok", reviewer="hr")
    assert review["decision"] == "approve"
    assert store.get_run("sa-run-001")["human_review_status"] == "reviewed_approve"

    batch = {
        "request_id": "sa-batch-001",
        "candidate_count": 1,
        "ranked_candidates": [{"candidate_id": "alice", "request_id": "sa-run-001", "rank_score": 90}],
        "results": [result],
        "batch_report": "# batch",
    }
    store.save_batch_result(batch)
    assert store.get_batch("sa-batch-001")["runs"][0]["request_id"] == "sa-run-001"

    store.save_evaluation_job(
        job_id="job-001",
        kind="batch_evaluation",
        request_id="sa-batch-001",
        payload={"candidate_count": 1},
    )
    store.mark_evaluation_job_running("job-001")
    store.complete_evaluation_job("job-001", {"request_id": "sa-batch-001"})
    assert store.get_evaluation_job("job-001")["status"] == "completed"
