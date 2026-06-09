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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    request_id TEXT PRIMARY KEY,
                    name TEXT,
                    education TEXT,
                    years_experience INTEGER,
                    candidate_track TEXT,
                    expected_salary TEXT,
                    profile_json TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    request_id TEXT PRIMARY KEY,
                    title TEXT,
                    required_years INTEGER,
                    recruitment_track TEXT,
                    required_skills_json TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    node TEXT,
                    timestamp TEXT,
                    output_summary TEXT,
                    extra_json TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    request_id TEXT PRIMARY KEY,
                    markdown TEXT,
                    quality_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    feedback TEXT,
                    reviewer TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )

    def save_workflow_result(self, result: dict[str, Any]) -> None:
        self.initialize()
        request_id = str(result.get("request_id") or "").strip()
        if not request_id:
            raise ValueError("workflow result must include request_id")

        trace = result.get("trace") or []
        candidate = result.get("candidate_profile") or {}
        job = result.get("job_profile") or {}
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
            if isinstance(candidate, dict) and candidate:
                connection.execute(
                    """
                    INSERT INTO candidates (
                        request_id,
                        name,
                        education,
                        years_experience,
                        candidate_track,
                        expected_salary,
                        profile_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(request_id) DO UPDATE SET
                        name=excluded.name,
                        education=excluded.education,
                        years_experience=excluded.years_experience,
                        candidate_track=excluded.candidate_track,
                        expected_salary=excluded.expected_salary,
                        profile_json=excluded.profile_json
                    """,
                    (
                        request_id,
                        candidate.get("name"),
                        candidate.get("education"),
                        candidate.get("years_experience"),
                        candidate.get("candidate_track"),
                        candidate.get("expected_salary"),
                        json.dumps(candidate, ensure_ascii=False, default=str),
                    ),
                )
            if isinstance(job, dict) and job:
                connection.execute(
                    """
                    INSERT INTO jobs (
                        request_id,
                        title,
                        required_years,
                        recruitment_track,
                        required_skills_json,
                        profile_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(request_id) DO UPDATE SET
                        title=excluded.title,
                        required_years=excluded.required_years,
                        recruitment_track=excluded.recruitment_track,
                        required_skills_json=excluded.required_skills_json,
                        profile_json=excluded.profile_json
                    """,
                    (
                        request_id,
                        job.get("title"),
                        job.get("required_years"),
                        job.get("recruitment_track"),
                        json.dumps(job.get("required_skills") or [], ensure_ascii=False, default=str),
                        json.dumps(job, ensure_ascii=False, default=str),
                    ),
                )
            connection.execute("DELETE FROM traces WHERE request_id = ?", (request_id,))
            connection.executemany(
                """
                INSERT INTO traces (
                    request_id,
                    node,
                    timestamp,
                    output_summary,
                    extra_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        request_id,
                        item.get("node"),
                        item.get("timestamp"),
                        item.get("output_summary"),
                        json.dumps(item.get("extra") or item.get("metadata") or {}, ensure_ascii=False, default=str),
                    )
                    for item in trace
                    if isinstance(item, dict)
                ],
            )
            connection.execute(
                """
                INSERT INTO reports (
                    request_id,
                    markdown,
                    quality_json
                )
                VALUES (?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    markdown=excluded.markdown,
                    quality_json=excluded.quality_json
                """,
                (
                    request_id,
                    result.get("report"),
                    json.dumps(result.get("report_quality") or {}, ensure_ascii=False, default=str),
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

    def get_candidate(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM candidates WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "request_id": row["request_id"],
            "name": row["name"],
            "education": row["education"],
            "years_experience": row["years_experience"],
            "candidate_track": row["candidate_track"],
            "expected_salary": row["expected_salary"],
            "profile": json.loads(row["profile_json"]),
        }

    def get_job(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "request_id": row["request_id"],
            "title": row["title"],
            "required_years": row["required_years"],
            "recruitment_track": row["recruitment_track"],
            "required_skills": json.loads(row["required_skills_json"]),
            "profile": json.loads(row["profile_json"]),
        }

    def get_trace(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM traces
                WHERE request_id = ?
                ORDER BY id ASC
                """,
                (request_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "request_id": row["request_id"],
                "node": row["node"],
                "timestamp": row["timestamp"],
                "output_summary": row["output_summary"],
                "extra": json.loads(row["extra_json"]),
            }
            for row in rows
        ]

    def get_report(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reports WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "request_id": row["request_id"],
            "markdown": row["markdown"],
            "quality": json.loads(row["quality_json"]),
            "created_at": row["created_at"],
        }

    def save_review(
        self,
        *,
        request_id: str,
        decision: str,
        feedback: str | None = None,
        reviewer: str | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        if self.get_run(request_id) is None:
            raise ValueError(f"run not found: {request_id}")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reviews (
                    request_id,
                    decision,
                    feedback,
                    reviewer
                )
                VALUES (?, ?, ?, ?)
                """,
                (request_id, decision, feedback, reviewer),
            )
            connection.execute(
                """
                UPDATE workflow_runs
                SET human_review_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
                """,
                (f"reviewed_{decision}", request_id),
            )
            row = connection.execute(
                "SELECT * FROM reviews WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return self._review_row_to_dict(row)

    def list_reviews(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM reviews
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._review_row_to_dict(row) for row in rows]

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

    @staticmethod
    def _review_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "request_id": row["request_id"],
            "decision": row["decision"],
            "feedback": row["feedback"],
            "reviewer": row["reviewer"],
            "created_at": row["created_at"],
        }
