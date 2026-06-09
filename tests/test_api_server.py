from __future__ import annotations

from fastapi.testclient import TestClient

from api.server import create_app
from core.persistence import SQLiteRunStore


def test_api_runs_evaluation_and_persists_result(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.db")
    app = create_app(store=store)
    client = TestClient(app)

    response = client.post(
        "/evaluations",
        json={
            "request_id": "api-run-001",
            "resume_text": "Candidate Alice. Python FastAPI Redis project.",
            "jd_text": "Backend engineer requires Python, FastAPI and Redis.",
            "risk_model_path": "models/review_risk_model.json",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == "api-run-001"
    assert payload["report"]

    saved = client.get("/runs/api-run-001")
    assert saved.status_code == 200
    assert saved.json()["request_id"] == "api-run-001"


def test_api_health_returns_storage_status(tmp_path) -> None:
    app = create_app(store=SQLiteRunStore(tmp_path / "runs.db"))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_serves_react_dist_when_available(tmp_path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<div id=\"root\">React app</div>", encoding="utf-8")
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")

    app = create_app(store=SQLiteRunStore(tmp_path / "runs.db"), frontend_dist=dist_dir)
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "React app" in root.text

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert "console.log" in asset.text

    spa_route = client.get("/runs/not-a-real-client-route")
    assert spa_route.status_code == 404


def test_api_exposes_trace_report_and_review_endpoints(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.db")
    store.save_workflow_result(
        {
            "request_id": "api-detail-001",
            "current_step": "human_review",
            "match_score": 91.0,
            "risk_score": 0.18,
            "human_review_status": "pending",
            "trace": [{"node": "matcher", "output_summary": "matched Python"}],
            "report": "# Candidate report",
            "candidate_profile": {"name": "Candidate Detail"},
            "job_profile": {"title": "Backend Engineer", "required_skills": ["Python"]},
        }
    )
    app = create_app(store=store)
    client = TestClient(app)

    trace = client.get("/traces/api-detail-001")
    assert trace.status_code == 200
    assert trace.json()["trace"][0]["node"] == "matcher"

    report = client.get("/reports/api-detail-001")
    assert report.status_code == 200
    assert report.json()["markdown"] == "# Candidate report"

    review = client.post(
        "/reviews/api-detail-001",
        json={"decision": "approve", "feedback": "Proceed.", "reviewer": "hr"},
    )
    assert review.status_code == 200
    assert review.json()["decision"] == "approve"

    reviews = client.get("/reviews")
    assert reviews.status_code == 200
    assert reviews.json()["reviews"][0]["request_id"] == "api-detail-001"


def test_api_accepts_uploaded_resume_text_files_for_batch(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.db")
    app = create_app(store=store, upload_dir=tmp_path / "uploads")
    client = TestClient(app)

    response = client.post(
        "/batch-evaluations/uploads",
        data={
            "request_id": "upload-batch-001",
            "jd_text": "Backend engineer requires Python and FastAPI.",
            "risk_model_path": "models/review_risk_model.json",
        },
        files=[
            ("files", ("alice.txt", b"Alice. Python FastAPI Redis project.", "text/plain")),
            ("files", ("bob.txt", b"Bob. Python SQL data pipeline.", "text/plain")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_count"] == 2
    saved_runs = client.get("/runs").json()["runs"]
    assert len(saved_runs) == 2

    batches = client.get("/batches").json()["batches"]
    assert batches[0]["request_id"] == "upload-batch-001"
    assert batches[0]["candidate_count"] == 2

    batch_detail = client.get("/batches/upload-batch-001")
    assert batch_detail.status_code == 200
    assert len(batch_detail.json()["runs"]) == 2


def test_api_filters_and_pages_runs(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.db")
    for index, status in enumerate(["pending", "reviewed_approve", "pending"], start=1):
        store.save_workflow_result(
            {
                "request_id": f"api-filter-{index}",
                "current_step": "human_review",
                "match_score": 80 + index,
                "risk_score": 0.1,
                "human_review_status": status,
                "trace": [],
                "report": "# report",
            }
        )
    app = create_app(store=store)
    client = TestClient(app)

    pending = client.get("/runs", params={"status": "pending", "limit": 10, "offset": 0})
    assert pending.status_code == 200
    assert {item["human_review_status"] for item in pending.json()["runs"]} == {"pending"}

    paged = client.get("/runs", params={"limit": 1, "offset": 1})
    assert paged.status_code == 200
    assert len(paged.json()["runs"]) == 1
