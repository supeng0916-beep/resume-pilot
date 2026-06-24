from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class WorkflowRunRow(Base):
    __tablename__ = "workflow_runs"

    request_id: Mapped[str] = mapped_column(String, primary_key=True)
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    human_review_status: Mapped[str | None] = mapped_column(String, nullable=True)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    trace_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)


class CandidateRow(Base):
    __tablename__ = "candidates"

    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    education: Mapped[str | None] = mapped_column(String, nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_track: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_salary: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_json: Mapped[str] = mapped_column(Text)


class JobRow(Base):
    __tablename__ = "jobs"

    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), primary_key=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    required_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recruitment_track: Mapped[str | None] = mapped_column(String, nullable=True)
    required_skills_json: Mapped[str] = mapped_column(Text)
    profile_json: Mapped[str] = mapped_column(Text)


class TraceRow(Base):
    __tablename__ = "traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), index=True)
    node: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_json: Mapped[str] = mapped_column(Text)


class ReportRow(Base):
    __tablename__ = "reports"

    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), primary_key=True)
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)


class ReviewRow(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), index=True)
    decision: Mapped[str] = mapped_column(String)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)


class BatchRow(Base):
    __tablename__ = "batches"

    request_id: Mapped[str] = mapped_column(String, primary_key=True)
    candidate_count: Mapped[int] = mapped_column(Integer)
    top_candidate_request_id: Mapped[str | None] = mapped_column(String, nullable=True)
    batch_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    ranked_candidates_json: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)


class BatchRunRow(Base):
    __tablename__ = "batch_runs"

    batch_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), primary_key=True)
    candidate_id: Mapped[str | None] = mapped_column(String, nullable=True)
    rank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_index: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EmailDeliveryRow(Base):
    __tablename__ = "email_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str | None] = mapped_column(String, ForeignKey("workflow_runs.request_id"), nullable=True)
    recipient: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    sent: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)


class AgentRunRow(Base):
    __tablename__ = "agent_runs"

    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    token_usage_json: Mapped[str] = mapped_column(Text)
    output_json: Mapped[str] = mapped_column(Text)


class SupervisorDecisionRow(Base):
    __tablename__ = "supervisor_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String, ForeignKey("workflow_runs.request_id"), index=True)
    stage: Mapped[str | None] = mapped_column(String, nullable=True)
    active_agents_json: Mapped[str] = mapped_column(Text)
    skipped_agents_json: Mapped[str] = mapped_column(Text)
    decision_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)


class EvaluationJobRow(Base):
    __tablename__ = "evaluation_jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String)
    request_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    return json.loads(value)


class SQLAlchemyRunStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_engine(database_url, future=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def save_workflow_result(self, result: dict[str, Any]) -> None:
        self.initialize()
        request_id = str(result.get("request_id") or "").strip()
        if not request_id:
            raise ValueError("workflow result must include request_id")

        trace = result.get("trace") or []
        candidate = result.get("candidate_profile") or {}
        job = result.get("job_profile") or {}
        with self.Session.begin() as session:
            session.merge(
                WorkflowRunRow(
                    request_id=request_id,
                    current_step=result.get("current_step"),
                    match_score=result.get("match_score"),
                    risk_score=result.get("risk_score"),
                    human_review_status=result.get("human_review_status"),
                    report=result.get("report"),
                    payload_json=_json(result),
                    trace_json=_json(trace),
                )
            )
            if isinstance(candidate, dict) and candidate:
                session.merge(
                    CandidateRow(
                        request_id=request_id,
                        name=candidate.get("name"),
                        education=candidate.get("education"),
                        years_experience=candidate.get("years_experience"),
                        candidate_track=candidate.get("candidate_track"),
                        expected_salary=candidate.get("expected_salary"),
                        profile_json=_json(candidate),
                    )
                )
            if isinstance(job, dict) and job:
                session.merge(
                    JobRow(
                        request_id=request_id,
                        title=job.get("title"),
                        required_years=job.get("required_years"),
                        recruitment_track=job.get("recruitment_track"),
                        required_skills_json=_json(job.get("required_skills") or []),
                        profile_json=_json(job),
                    )
                )
            session.query(TraceRow).filter_by(request_id=request_id).delete()
            for item in trace:
                if isinstance(item, dict):
                    session.add(
                        TraceRow(
                            request_id=request_id,
                            node=item.get("node"),
                            timestamp=item.get("timestamp"),
                            output_summary=item.get("output_summary"),
                            extra_json=_json(item.get("extra") or item.get("metadata") or {}),
                        )
                    )
            session.merge(
                ReportRow(
                    request_id=request_id,
                    markdown=result.get("report"),
                    quality_json=_json(result.get("report_quality") or {}),
                )
            )
            session.query(AgentRunRow).filter_by(request_id=request_id).delete()
            agent_outputs = result.get("agent_outputs") or {}
            for agent_name, metric in (result.get("agent_metrics") or {}).items():
                if isinstance(metric, dict):
                    session.add(
                        AgentRunRow(
                            request_id=request_id,
                            agent_name=agent_name,
                            status=metric.get("status"),
                            confidence=metric.get("confidence"),
                            duration_ms=metric.get("duration_ms"),
                            model_name=metric.get("model_name"),
                            provider=metric.get("provider"),
                            token_usage_json=_json(metric.get("token_usage") or {}),
                            output_json=_json(agent_outputs.get(agent_name) or {}),
                        )
                    )
            session.query(SupervisorDecisionRow).filter_by(request_id=request_id).delete()
            for decision in result.get("supervisor_decisions") or []:
                if isinstance(decision, dict):
                    session.add(
                        SupervisorDecisionRow(
                            request_id=request_id,
                            stage=decision.get("stage"),
                            active_agents_json=_json(decision.get("active_agents") or []),
                            skipped_agents_json=_json(decision.get("skipped_agents") or {}),
                            decision_json=_json(decision),
                        )
                    )

    def get_run(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            row = session.get(WorkflowRunRow, request_id)
            return self._run_row_to_dict(row) if row else None

    def list_runs(self, *, limit: int = 50, offset: int = 0, status: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        safe_limit = max(1, min(int(limit), 200))
        with self.Session() as session:
            statement = select(WorkflowRunRow)
            if status:
                statement = statement.where(WorkflowRunRow.human_review_status == status)
            rows = session.execute(statement.offset(max(0, int(offset))).limit(safe_limit)).scalars().all()
            return [self._run_row_to_dict(row) for row in rows]

    def delete_run(self, request_id: str) -> bool:
        self.initialize()
        with self.Session.begin() as session:
            row = session.get(WorkflowRunRow, request_id)
            if row is None:
                return False
            for model in (
                TraceRow,
                ReportRow,
                ReviewRow,
                EmailDeliveryRow,
                CandidateRow,
                JobRow,
                AgentRunRow,
                SupervisorDecisionRow,
            ):
                session.query(model).filter_by(request_id=request_id).delete()
            session.query(BatchRunRow).filter_by(request_id=request_id).delete()
            session.query(EvaluationJobRow).filter_by(request_id=request_id).delete()
            session.delete(row)
            batch_ids = [item.request_id for item in session.execute(select(BatchRow)).scalars().all()]
            for batch_id in batch_ids:
                has_runs = session.execute(
                    select(BatchRunRow).where(BatchRunRow.batch_request_id == batch_id)
                ).first()
                if has_runs is None:
                    batch = session.get(BatchRow, batch_id)
                    if batch is not None:
                        session.delete(batch)
            return True

    def clear_evaluation_data(self) -> int:
        self.initialize()
        with self.Session.begin() as session:
            count = session.query(WorkflowRunRow).count()
            for model in (
                EmailDeliveryRow,
                ReviewRow,
                ReportRow,
                TraceRow,
                CandidateRow,
                JobRow,
                AgentRunRow,
                SupervisorDecisionRow,
                BatchRunRow,
                BatchRow,
                EvaluationJobRow,
                WorkflowRunRow,
            ):
                session.query(model).delete()
            return int(count)

    def save_batch_result(self, batch_result: dict[str, Any]) -> None:
        self.initialize()
        request_id = str(batch_result.get("request_id") or "").strip()
        if not request_id:
            raise ValueError("batch result must include request_id")
        ranked_candidates = batch_result.get("ranked_candidates") or []
        top_candidate_request_id = ranked_candidates[0].get("request_id") if ranked_candidates and isinstance(ranked_candidates[0], dict) else None
        with self.Session.begin() as session:
            session.merge(
                BatchRow(
                    request_id=request_id,
                    candidate_count=int(batch_result.get("candidate_count") or len(ranked_candidates)),
                    top_candidate_request_id=top_candidate_request_id,
                    batch_report=batch_result.get("batch_report"),
                    ranked_candidates_json=_json(ranked_candidates),
                    payload_json=_json(batch_result),
                )
            )
            session.query(BatchRunRow).filter_by(batch_request_id=request_id).delete()
            for index, item in enumerate(ranked_candidates, start=1):
                if isinstance(item, dict) and item.get("request_id"):
                    session.add(
                        BatchRunRow(
                            batch_request_id=request_id,
                            request_id=item.get("request_id"),
                            candidate_id=item.get("candidate_id"),
                            rank_score=item.get("rank_score"),
                            rank_index=index,
                        )
                    )

    def list_batches(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(select(BatchRow).offset(max(0, int(offset))).limit(max(1, min(int(limit), 200)))).scalars().all()
            return [self._batch_row_to_summary(row) for row in rows]

    def get_batch(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            batch = session.get(BatchRow, request_id)
            if batch is None:
                return None
            run_ids = session.execute(
                select(BatchRunRow).where(BatchRunRow.batch_request_id == request_id).order_by(BatchRunRow.rank_index)
            ).scalars().all()
            runs = [self._run_row_to_dict(session.get(WorkflowRunRow, item.request_id)) for item in run_ids]
            payload = self._batch_row_to_summary(batch)
            payload["batch_report"] = batch.batch_report
            payload["payload"] = _loads(batch.payload_json, {})
            payload["runs"] = [item for item in runs if item is not None]
            return payload

    def get_candidate(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            row = session.get(CandidateRow, request_id)
            if row is None:
                return None
            return {
                "request_id": row.request_id,
                "name": row.name,
                "education": row.education,
                "years_experience": row.years_experience,
                "candidate_track": row.candidate_track,
                "expected_salary": row.expected_salary,
                "profile": _loads(row.profile_json, {}),
            }

    def get_job(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            row = session.get(JobRow, request_id)
            if row is None:
                return None
            return {
                "request_id": row.request_id,
                "title": row.title,
                "required_years": row.required_years,
                "recruitment_track": row.recruitment_track,
                "required_skills": _loads(row.required_skills_json, []),
                "profile": _loads(row.profile_json, {}),
            }

    def get_trace(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(select(TraceRow).where(TraceRow.request_id == request_id).order_by(TraceRow.id)).scalars().all()
            return [
                {
                    "id": row.id,
                    "request_id": row.request_id,
                    "node": row.node,
                    "timestamp": row.timestamp,
                    "output_summary": row.output_summary,
                    "extra": _loads(row.extra_json, {}),
                }
                for row in rows
            ]

    def get_report(self, request_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            row = session.get(ReportRow, request_id)
            if row is None:
                return None
            return {
                "request_id": row.request_id,
                "markdown": row.markdown,
                "quality": _loads(row.quality_json, {}),
                "created_at": row.created_at,
            }

    def save_review(self, *, request_id: str, decision: str, feedback: str | None = None, reviewer: str | None = None) -> dict[str, Any]:
        self.initialize()
        with self.Session.begin() as session:
            run = session.get(WorkflowRunRow, request_id)
            if run is None:
                raise ValueError(f"run not found: {request_id}")
            review = ReviewRow(request_id=request_id, decision=decision, feedback=feedback, reviewer=reviewer)
            session.add(review)
            session.flush()
            run.human_review_status = f"reviewed_{decision}"
            return self._review_row_to_dict(review)

    def list_reviews(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(select(ReviewRow).order_by(ReviewRow.id.desc()).limit(max(1, min(int(limit), 200)))).scalars().all()
            return [self._review_row_to_dict(row) for row in rows]

    def save_email_delivery(self, *, recipient: str, subject: str, sent: bool, message: str, request_id: str | None = None) -> dict[str, Any]:
        self.initialize()
        with self.Session.begin() as session:
            row = EmailDeliveryRow(request_id=request_id, recipient=recipient, subject=subject, sent=1 if sent else 0, message=message)
            session.add(row)
            session.flush()
            return self._email_delivery_row_to_dict(row)

    def list_email_deliveries(self, *, limit: int = 50) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(select(EmailDeliveryRow).order_by(EmailDeliveryRow.id.desc()).limit(max(1, min(int(limit), 200)))).scalars().all()
            return [self._email_delivery_row_to_dict(row) for row in rows]

    def get_agent_runs(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(select(AgentRunRow).where(AgentRunRow.request_id == request_id).order_by(AgentRunRow.agent_name)).scalars().all()
            return [
                {
                    "request_id": row.request_id,
                    "agent_name": row.agent_name,
                    "status": row.status,
                    "confidence": row.confidence,
                    "duration_ms": row.duration_ms,
                    "model_name": row.model_name,
                    "provider": row.provider,
                    "token_usage": _loads(row.token_usage_json, {}),
                    "output": _loads(row.output_json, {}),
                }
                for row in rows
            ]

    def get_supervisor_decisions(self, request_id: str) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            rows = session.execute(
                select(SupervisorDecisionRow).where(SupervisorDecisionRow.request_id == request_id).order_by(SupervisorDecisionRow.id)
            ).scalars().all()
            return [
                {
                    "id": row.id,
                    "request_id": row.request_id,
                    "stage": row.stage,
                    "active_agents": _loads(row.active_agents_json, []),
                    "skipped_agents": _loads(row.skipped_agents_json, {}),
                    "decision": _loads(row.decision_json, {}),
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    def save_evaluation_job(self, *, job_id: str, kind: str, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.initialize()
        with self.Session.begin() as session:
            session.merge(
                EvaluationJobRow(
                    job_id=job_id,
                    kind=kind,
                    request_id=request_id,
                    status="queued",
                    payload_json=_json(payload),
                    result_json=None,
                    error_message=None,
                )
            )
        return self.get_evaluation_job(job_id) or {}

    def mark_evaluation_job_running(self, job_id: str) -> None:
        self._update_job(job_id, status="running")

    def complete_evaluation_job(self, job_id: str, result: dict[str, Any]) -> None:
        self._update_job(job_id, status="completed", result_json=_json(result), error_message=None)

    def fail_evaluation_job(self, job_id: str, error_message: str) -> None:
        self._update_job(job_id, status="failed", error_message=error_message)

    def get_evaluation_job(self, job_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self.Session() as session:
            row = session.get(EvaluationJobRow, job_id)
            return self._evaluation_job_row_to_dict(row) if row else None

    def list_evaluation_jobs(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        with self.Session() as session:
            statement = select(EvaluationJobRow)
            if status:
                statement = statement.where(EvaluationJobRow.status == status)
            rows = session.execute(statement.limit(max(1, min(int(limit), 200)))).scalars().all()
            return [self._evaluation_job_row_to_dict(row) for row in rows]

    def _update_job(self, job_id: str, **values: Any) -> None:
        self.initialize()
        with self.Session.begin() as session:
            row = session.get(EvaluationJobRow, job_id)
            if row is None:
                return
            for key, value in values.items():
                setattr(row, key, value)

    @staticmethod
    def _run_row_to_dict(row: WorkflowRunRow | None) -> dict[str, Any] | None:
        if row is None:
            return None
        payload = _loads(row.payload_json, {})
        return {
            "request_id": row.request_id,
            "current_step": row.current_step,
            "match_score": row.match_score,
            "risk_score": row.risk_score,
            "human_review_status": row.human_review_status,
            "report": row.report,
            "payload": payload,
            "trace": _loads(row.trace_json, []),
            "agent_metrics": payload.get("agent_metrics") or {},
            "agent_outputs": payload.get("agent_outputs") or {},
            "supervisor_decisions": payload.get("supervisor_decisions") or [],
            "specialist_execution": payload.get("specialist_execution"),
            "active_agents": payload.get("active_agents") or [],
            "supervisor_plan": payload.get("supervisor_plan"),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def _batch_row_to_summary(row: BatchRow) -> dict[str, Any]:
        return {
            "request_id": row.request_id,
            "candidate_count": row.candidate_count,
            "top_candidate_request_id": row.top_candidate_request_id,
            "ranked_candidates": _loads(row.ranked_candidates_json, []),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def _review_row_to_dict(row: ReviewRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "request_id": row.request_id,
            "decision": row.decision,
            "feedback": row.feedback,
            "reviewer": row.reviewer,
            "created_at": row.created_at,
        }

    @staticmethod
    def _email_delivery_row_to_dict(row: EmailDeliveryRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "request_id": row.request_id,
            "recipient": row.recipient,
            "subject": row.subject,
            "sent": bool(row.sent),
            "message": row.message,
            "created_at": row.created_at,
        }

    @staticmethod
    def _evaluation_job_row_to_dict(row: EvaluationJobRow) -> dict[str, Any]:
        return {
            "job_id": row.job_id,
            "kind": row.kind,
            "request_id": row.request_id,
            "status": row.status,
            "payload": _loads(row.payload_json, {}),
            "result": _loads(row.result_json, None),
            "error_message": row.error_message,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
