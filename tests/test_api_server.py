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
