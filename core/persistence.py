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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    request_id TEXT PRIMARY KEY,
                    candidate_count INTEGER NOT NULL,
                    top_candidate_request_id TEXT,
                    batch_report TEXT,
                    ranked_candidates_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_runs (
                    batch_request_id TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    candidate_id TEXT,
                    rank_score REAL,
                    rank_index INTEGER,
                    PRIMARY KEY(batch_request_id, request_id),
                    FOREIGN KEY(batch_request_id) REFERENCES batches(request_id),
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS email_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    sent INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    request_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT,
                    confidence REAL,
                    duration_ms INTEGER,
                    model_name TEXT,
                    provider TEXT,
                    token_usage_json TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    PRIMARY KEY(request_id, agent_name),
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS supervisor_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    stage TEXT,
                    active_agents_json TEXT NOT NULL,
                    skipped_agents_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_jobs (
                    job_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_runs_updated_at ON workflow_runs(updated_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_runs_review_status ON workflow_runs(human_review_status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_evaluation_jobs_status ON evaluation_jobs(status)"
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
            agent_metrics = result.get("agent_metrics") or {}
            agent_outputs = result.get("agent_outputs") or {}
            connection.execute("DELETE FROM agent_runs WHERE request_id = ?", (request_id,))
            connection.executemany(
                """
                INSERT INTO agent_runs (
                    request_id,
                    agent_name,
                    status,
                    confidence,
                    duration_ms,
                    model_name,
                    provider,
                    token_usage_json,
                    output_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        request_id,
                        agent_name,
                        metric.get("status"),
                        metric.get("confidence"),
                        metric.get("duration_ms"),
                        metric.get("model_name"),
                        metric.get("provider"),
                        json.dumps(metric.get("token_usage") or {}, ensure_ascii=False, default=str),
                        json.dumps(agent_outputs.get(agent_name) or {}, ensure_ascii=False, default=str),
                    )
                    for agent_name, metric in agent_metrics.items()
                    if isinstance(metric, dict)
                ],
            )
            supervisor_decisions = result.get("supervisor_decisions") or []
            connection.execute("DELETE FROM supervisor_decisions WHERE request_id = ?", (request_id,))
            connection.executemany(
                """
                INSERT INTO supervisor_decisions (
                    request_id,
                    stage,
                    active_agents_json,
                    skipped_agents_json,
                    decision_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        request_id,
                        decision.get("stage"),
                        json.dumps(decision.get("active_agents") or [], ensure_ascii=False, default=str),
                        json.dumps(decision.get("skipped_agents") or {}, ensure_ascii=False, default=str),
                        json.dumps(decision, ensure_ascii=False, default=str),
                    )
                    for decision in supervisor_decisions
                    if isinstance(decision, dict)
                ],
            )

    def get_run(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workflow_runs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        self.initialize()
        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))
        parameters: list[Any] = []
        where_clause = ""
        if status:
            where_clause = "WHERE human_review_status = ?"
            parameters.append(status)
        parameters.extend([safe_limit, safe_offset])
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM workflow_runs
                {where_clause}
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ? OFFSET ?
                """,
                parameters,
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def delete_run(self, request_id: str) -> bool:
        self.initialize()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT request_id FROM workflow_runs WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if existing is None:
                return False
            for table in (
                "traces",
                "reports",
                "reviews",
                "email_deliveries",
                "candidates",
                "jobs",
                "agent_runs",
                "supervisor_decisions",
            ):
                connection.execute(f"DELETE FROM {table} WHERE request_id = ?", (request_id,))
            connection.execute("DELETE FROM batch_runs WHERE request_id = ?", (request_id,))
            connection.execute("DELETE FROM workflow_runs WHERE request_id = ?", (request_id,))
            orphan_batches = connection.execute(
                """
                SELECT batches.request_id
                FROM batches
                LEFT JOIN batch_runs ON batch_runs.batch_request_id = batches.request_id
                WHERE batch_runs.request_id IS NULL
                """
            ).fetchall()
            for row in orphan_batches:
                connection.execute("DELETE FROM batches WHERE request_id = ?", (row["request_id"],))
        return True

    def clear_evaluation_data(self) -> int:
        self.initialize()
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) AS total FROM workflow_runs").fetchone()["total"]
            for table in (
                "email_deliveries",
                "reviews",
                "reports",
                "traces",
                "candidates",
                "jobs",
                "agent_runs",
                "supervisor_decisions",
                "batch_runs",
                "batches",
                "evaluation_jobs",
                "workflow_runs",
            ):
                connection.execute(f"DELETE FROM {table}")
        return int(count)

    def save_batch_result(self, batch_result: dict[str, Any]) -> None:
        self.initialize()
        request_id = str(batch_result.get("request_id") or "").strip()
        if not request_id:
            raise ValueError("batch result must include request_id")

        ranked_candidates = batch_result.get("ranked_candidates") or []
        top_candidate_request_id = None
        if ranked_candidates and isinstance(ranked_candidates[0], dict):
            top_candidate_request_id = ranked_candidates[0].get("request_id")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO batches (
                    request_id,
                    candidate_count,
                    top_candidate_request_id,
                    batch_report,
                    ranked_candidates_json,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    candidate_count=excluded.candidate_count,
                    top_candidate_request_id=excluded.top_candidate_request_id,
                    batch_report=excluded.batch_report,
                    ranked_candidates_json=excluded.ranked_candidates_json,
                    payload_json=excluded.payload_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    request_id,
                    int(batch_result.get("candidate_count") or len(ranked_candidates)),
                    top_candidate_request_id,
                    batch_result.get("batch_report"),
                    json.dumps(ranked_candidates, ensure_ascii=False, default=str),
                    json.dumps(batch_result, ensure_ascii=False, default=str),
                ),
            )
            connection.execute("DELETE FROM batch_runs WHERE batch_request_id = ?", (request_id,))
            connection.executemany(
                """
                INSERT INTO batch_runs (
                    batch_request_id,
                    request_id,
                    candidate_id,
                    rank_score,
                    rank_index
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        request_id,
                        item.get("request_id"),
                        item.get("candidate_id"),
                        item.get("rank_score"),
                        index,
                    )
                    for index, item in enumerate(ranked_candidates, start=1)
                    if isinstance(item, dict) and item.get("request_id")
                ],
            )

    def list_batches(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.initialize()
        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM batches
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ? OFFSET ?
                """,
                (safe_limit, safe_offset),
            ).fetchall()
        return [self._batch_row_to_summary(row) for row in rows]

    def get_batch(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            batch_row = connection.execute(
                "SELECT * FROM batches WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if batch_row is None:
                return None
            run_rows = connection.execute(
                """
                SELECT workflow_runs.*
                FROM batch_runs
                JOIN workflow_runs ON workflow_runs.request_id = batch_runs.request_id
                WHERE batch_runs.batch_request_id = ?
                ORDER BY batch_runs.rank_index ASC
                """,
                (request_id,),
            ).fetchall()
        batch = self._batch_row_to_summary(batch_row)
        batch["batch_report"] = batch_row["batch_report"]
        batch["payload"] = json.loads(batch_row["payload_json"])
        batch["runs"] = [self._row_to_dict(row) for row in run_rows]
        return batch

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

    def get_agent_runs(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM agent_runs
                WHERE request_id = ?
                ORDER BY agent_name ASC
                """,
                (request_id,),
            ).fetchall()
        return [
            {
                "request_id": row["request_id"],
                "agent_name": row["agent_name"],
                "status": row["status"],
                "confidence": row["confidence"],
                "duration_ms": row["duration_ms"],
                "model_name": row["model_name"],
                "provider": row["provider"],
                "token_usage": json.loads(row["token_usage_json"]),
                "output": json.loads(row["output_json"]),
            }
            for row in rows
        ]

    def get_supervisor_decisions(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM supervisor_decisions
                WHERE request_id = ?
                ORDER BY id ASC
                """,
                (request_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "request_id": row["request_id"],
                "stage": row["stage"],
                "active_agents": json.loads(row["active_agents_json"]),
                "skipped_agents": json.loads(row["skipped_agents_json"]),
                "decision": json.loads(row["decision_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def save_evaluation_job(
        self,
        *,
        job_id: str,
        kind: str,
        request_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evaluation_jobs (
                    job_id,
                    kind,
                    request_id,
                    status,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    kind=excluded.kind,
                    request_id=excluded.request_id,
                    status=excluded.status,
                    payload_json=excluded.payload_json,
                    result_json=NULL,
                    error_message=NULL,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    job_id,
                    kind,
                    request_id,
                    "queued",
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )
        return self.get_evaluation_job(job_id) or {}

    def mark_evaluation_job_running(self, job_id: str) -> None:
        self._update_evaluation_job_status(job_id, status="running")

    def complete_evaluation_job(self, job_id: str, result: dict[str, Any]) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE evaluation_jobs
                SET status = ?, result_json = ?, error_message = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                ("completed", json.dumps(result, ensure_ascii=False, default=str), job_id),
            )

    def fail_evaluation_job(self, job_id: str, error_message: str) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE evaluation_jobs
                SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                ("failed", error_message, job_id),
            )

    def get_evaluation_job(self, job_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evaluation_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return self._evaluation_job_row_to_dict(row) if row else None

    def list_evaluation_jobs(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        safe_limit = max(1, min(int(limit), 200))
        parameters: list[Any] = []
        where_clause = ""
        if status:
            where_clause = "WHERE status = ?"
            parameters.append(status)
        parameters.append(safe_limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM evaluation_jobs
                {where_clause}
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return [self._evaluation_job_row_to_dict(row) for row in rows]

    def _update_evaluation_job_status(self, job_id: str, *, status: str) -> None:
        self.initialize()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE evaluation_jobs
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                """,
                (status, job_id),
            )

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

    def save_email_delivery(
        self,
        *,
        recipient: str,
        subject: str,
        sent: bool,
        message: str,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO email_deliveries (
                    request_id,
                    recipient,
                    subject,
                    sent,
                    message
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, recipient, subject, 1 if sent else 0, message),
            )
            row = connection.execute(
                "SELECT * FROM email_deliveries WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return self._email_delivery_row_to_dict(row)

    def list_email_deliveries(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        safe_limit = max(1, min(int(limit), 200))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM email_deliveries
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [self._email_delivery_row_to_dict(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        payload = json.loads(row["payload_json"])
        return {
            "request_id": row["request_id"],
            "current_step": row["current_step"],
            "match_score": row["match_score"],
            "risk_score": row["risk_score"],
            "human_review_status": row["human_review_status"],
            "report": row["report"],
            "payload": payload,
            "trace": json.loads(row["trace_json"]),
            "agent_metrics": payload.get("agent_metrics") or {},
            "agent_outputs": payload.get("agent_outputs") or {},
            "supervisor_decisions": payload.get("supervisor_decisions") or [],
            "specialist_execution": payload.get("specialist_execution"),
            "active_agents": payload.get("active_agents") or [],
            "supervisor_plan": payload.get("supervisor_plan"),
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

    @staticmethod
    def _batch_row_to_summary(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "request_id": row["request_id"],
            "candidate_count": row["candidate_count"],
            "top_candidate_request_id": row["top_candidate_request_id"],
            "ranked_candidates": json.loads(row["ranked_candidates_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _email_delivery_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "request_id": row["request_id"],
            "recipient": row["recipient"],
            "subject": row["subject"],
            "sent": bool(row["sent"]),
            "message": row["message"],
            "created_at": row["created_at"],
        }

    @staticmethod
    def _evaluation_job_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        result_json = row["result_json"]
        return {
            "job_id": row["job_id"],
            "kind": row["kind"],
            "request_id": row["request_id"],
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "result": json.loads(result_json) if result_json else None,
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
