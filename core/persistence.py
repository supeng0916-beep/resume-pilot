from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("data/hr_runs.sqlite3")


class SQLiteRunStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    request_id TEXT PRIMARY KEY,
                    current_step TEXT,
                    match_score REAL,
                    risk_score REAL,
                    human_review_status TEXT,
                    report TEXT,
                    payload_json TEXT NOT NULL,
                    trace_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save_workflow_result(self, result: dict[str, Any]) -> None:
        self.initialize()
        request_id = str(result.get("request_id") or "").strip()
        if not request_id:
            raise ValueError("workflow result must include request_id")

        trace = result.get("trace") or []
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_runs (
                    request_id,
                    current_step,
                    match_score,
                    risk_score,
                    human_review_status,
                    report,
                    payload_json,
                    trace_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    current_step=excluded.current_step,
                    match_score=excluded.match_score,
                    risk_score=excluded.risk_score,
                    human_review_status=excluded.human_review_status,
                    report=excluded.report,
                    payload_json=excluded.payload_json,
                    trace_json=excluded.trace_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    request_id,
                    result.get("current_step"),
                    result.get("match_score"),
                    result.get("risk_score"),
                    result.get("human_review_status"),
                    result.get("report"),
                    json.dumps(result, ensure_ascii=False, default=str),
                    json.dumps(trace, ensure_ascii=False, default=str),
                ),
            )

    def get_run(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workflow_runs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM workflow_runs
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "request_id": row["request_id"],
            "current_step": row["current_step"],
            "match_score": row["match_score"],
            "risk_score": row["risk_score"],
            "human_review_status": row["human_review_status"],
            "report": row["report"],
            "payload": json.loads(row["payload_json"]),
            "trace": json.loads(row["trace_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
