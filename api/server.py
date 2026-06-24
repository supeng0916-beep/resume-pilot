from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from core.email_sender import send_report_email
from core.job_queue import enqueue_batch_evaluation_job
from core.persistence import SQLiteRunStore
from core.runtime_status import get_runtime_status
from core.store_factory import create_run_store
from harness.batch_runner import BatchResumeInput, run_batch_evaluation
from harness.runner import run_evaluation

DEFAULT_UPLOAD_DIR = Path("data/api_uploads")
DEFAULT_FRONTEND_DIST = Path("frontend/dist")


class EvaluationRequest(BaseModel):
    request_id: str = Field(default="api-run", min_length=1)
    resume_text: str | None = None
    resume_file_path: str | None = None
    jd_text: str | None = None
    risk_model_path: str | None = None
    enable_llm_structured_extraction: bool | None = None
    enable_llm_report_enhancement: bool | None = None


class BatchResumeRequest(BaseModel):
    candidate_id: str = Field(min_length=1)
    resume_text: str | None = None
    resume_file_path: str | None = None


class BatchEvaluationRequest(BaseModel):
    request_id: str = Field(default="api-batch", min_length=1)
    resumes: list[BatchResumeRequest] = Field(min_length=1)
    jd_text: str | None = None
    risk_model_path: str | None = None
    enable_llm_structured_extraction: bool | None = None
    enable_llm_report_enhancement: bool | None = None


class ReviewRequest(BaseModel):
    decision: str = Field(min_length=1)
    feedback: str | None = None
    reviewer: str | None = None


class EmailReportRequest(BaseModel):
    recipient: str = Field(min_length=1)
    subject: str | None = None
    request_id: str | None = None
    report_markdown: str | None = None


def _safe_upload_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip().replace("\x00", "")
    return safe_name or "resume.txt"


def create_app(
    *,
    store: SQLiteRunStore | None = None,
    upload_dir: str | Path = DEFAULT_UPLOAD_DIR,
    frontend_dist: str | Path = DEFAULT_FRONTEND_DIST,
) -> FastAPI:
    run_store = store or create_run_store()
    run_store.initialize()
    upload_root = Path(upload_dir)
    frontend_root = Path(frontend_dist)
    app = FastAPI(title="Agentic HR API", version="0.1.0")

    @app.middleware("http")
    async def strip_api_prefix(request: Request, call_next):
        path = request.scope.get("path", "")
        if path.startswith("/api/"):
            rewritten_path = path.removeprefix("/api") or "/"
            request.scope["path"] = rewritten_path
            request.scope["raw_path"] = rewritten_path.encode("utf-8")
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        run_store.initialize()
        return {"status": "ok", "storage": "sqlite"}

    @app.get("/runtime")
    def runtime() -> dict[str, object]:
        return {
            "status": "ok",
            "storage": "sqlalchemy" if run_store.__class__.__name__ == "SQLAlchemyRunStore" else "sqlite",
            "store": run_store.__class__.__name__,
            **get_runtime_status().as_dict(),
        }

    @app.post("/evaluations")
    def create_evaluation(request: EvaluationRequest) -> dict[str, Any]:
        result = run_evaluation(
            resume_file_path=request.resume_file_path,
            resume_text=request.resume_text,
            jd_text=request.jd_text,
            request_id=request.request_id,
            risk_model_path=request.risk_model_path,
            enable_llm_structured_extraction=request.enable_llm_structured_extraction,
            enable_llm_report_enhancement=request.enable_llm_report_enhancement,
            include_quality_check=True,
        )
        run_store.save_workflow_result(result)
        return result

    @app.post("/batch-evaluations")
    def create_batch_evaluation(request: BatchEvaluationRequest) -> dict[str, Any]:
        result = run_batch_evaluation(
            [
                BatchResumeInput(
                    candidate_id=item.candidate_id,
                    resume_text=item.resume_text,
                    resume_file_path=item.resume_file_path,
                )
                for item in request.resumes
            ],
            jd_text=request.jd_text,
            request_id=request.request_id,
            risk_model_path=request.risk_model_path,
            enable_llm_structured_extraction=request.enable_llm_structured_extraction,
            enable_llm_report_enhancement=request.enable_llm_report_enhancement,
        )
        for workflow_result in result.get("results", []):
            run_store.save_workflow_result(workflow_result)
        run_store.save_batch_result(result)
        return result

    def _run_batch_job(job_id: str, request: BatchEvaluationRequest) -> None:
        run_store.mark_evaluation_job_running(job_id)
        try:
            result = run_batch_evaluation(
                [
                    BatchResumeInput(
                        candidate_id=item.candidate_id,
                        resume_text=item.resume_text,
                        resume_file_path=item.resume_file_path,
                    )
                    for item in request.resumes
                ],
                jd_text=request.jd_text,
                request_id=request.request_id,
                risk_model_path=request.risk_model_path,
                enable_llm_structured_extraction=request.enable_llm_structured_extraction,
                enable_llm_report_enhancement=request.enable_llm_report_enhancement,
            )
            for workflow_result in result.get("results", []):
                run_store.save_workflow_result(workflow_result)
            run_store.save_batch_result(result)
            run_store.complete_evaluation_job(job_id, result)
        except Exception as exc:  # pragma: no cover - defensive production boundary.
            run_store.fail_evaluation_job(job_id, str(exc))

    @app.post("/batch-evaluations/jobs", status_code=status.HTTP_202_ACCEPTED)
    def create_batch_evaluation_job(
        request: BatchEvaluationRequest,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        job_id = f"batch-{uuid4().hex}"
        job = run_store.save_evaluation_job(
            job_id=job_id,
            kind="batch_evaluation",
            request_id=request.request_id,
            payload=request.model_dump(),
        )
        if enqueue_batch_evaluation_job(job_id, request.model_dump()):
            return job
        background_tasks.add_task(_run_batch_job, job_id, request)
        job["queue_backend"] = "fastapi_background_tasks"
        return job

    @app.post("/batch-evaluations/uploads")
    async def create_batch_evaluation_from_uploads(
        request_id: str = Form(default="api-upload-batch"),
        jd_text: str | None = Form(default=None),
        risk_model_path: str | None = Form(default=None),
        enable_llm_structured_extraction: bool | None = Form(default=None),
        enable_llm_report_enhancement: bool | None = Form(default=None),
        files: list[UploadFile] = File(...),
    ) -> dict[str, Any]:
        run_dir = upload_root / request_id
        run_dir.mkdir(parents=True, exist_ok=True)
        resumes: list[BatchResumeInput] = []
        seen_upload_hashes: dict[str, str] = {}
        uploaded_files: list[dict[str, str]] = []
        skipped_duplicates: list[dict[str, str]] = []

        for index, upload in enumerate(files, start=1):
            filename = _safe_upload_filename(upload.filename or f"resume-{index}.txt")
            content = await upload.read()
            content_hash = hashlib.sha256(content).hexdigest()
            if content_hash in seen_upload_hashes:
                skipped_duplicates.append(
                    {
                        "filename": filename,
                        "duplicate_of": seen_upload_hashes[content_hash],
                        "sha256": content_hash,
                    }
                )
                continue

            path = run_dir / f"{index:03d}_{filename}"
            path.write_bytes(content)
            seen_upload_hashes[content_hash] = filename
            uploaded_files.append(
                {
                    "filename": filename,
                    "stored_path": str(path),
                    "sha256": content_hash,
                }
            )
            candidate_id = Path(filename).stem or f"candidate-{index:03d}"
            if path.suffix.lower() in {".txt", ".md"}:
                resumes.append(
                    BatchResumeInput(
                        candidate_id=candidate_id,
                        resume_text=content.decode("utf-8", errors="ignore"),
                    )
                )
            else:
                resumes.append(BatchResumeInput(candidate_id=candidate_id, resume_file_path=str(path)))

        result = run_batch_evaluation(
            resumes,
            jd_text=jd_text,
            request_id=request_id,
            risk_model_path=risk_model_path,
            enable_llm_structured_extraction=enable_llm_structured_extraction,
            enable_llm_report_enhancement=enable_llm_report_enhancement,
        )
        for workflow_result in result.get("results", []):
            run_store.save_workflow_result(workflow_result)
        run_store.save_batch_result(result)
        result["uploaded_files"] = uploaded_files
        result["skipped_duplicates"] = skipped_duplicates
        result["skipped_duplicate_count"] = len(skipped_duplicates)
        return result

    @app.get("/runs")
    def list_runs(limit: int = 50, offset: int = 0, status: str | None = None) -> dict[str, Any]:
        return {"runs": run_store.list_runs(limit=limit, offset=offset, status=status)}

    @app.delete("/runs")
    def clear_runs() -> dict[str, Any]:
        deleted_count = run_store.clear_evaluation_data()
        return {"deleted_count": deleted_count}

    @app.get("/batches")
    def list_batches(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        return {"batches": run_store.list_batches(limit=limit, offset=offset)}

    @app.get("/batches/{request_id}")
    def get_batch(request_id: str) -> dict[str, Any]:
        batch = run_store.get_batch(request_id)
        if batch is None:
            raise HTTPException(status_code=404, detail="batch not found")
        return batch

    @app.get("/jobs")
    def list_jobs(limit: int = 50, status: str | None = None) -> dict[str, Any]:
        return {"jobs": run_store.list_evaluation_jobs(limit=limit, status=status)}

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = run_store.get_evaluation_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.get("/traces/{request_id}")
    def get_trace(request_id: str) -> dict[str, Any]:
        if run_store.get_run(request_id) is None:
            raise HTTPException(status_code=404, detail="run not found")
        return {"request_id": request_id, "trace": run_store.get_trace(request_id)}

    @app.get("/reports/{request_id}")
    def get_report(request_id: str) -> dict[str, Any]:
        report = run_store.get_report(request_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return report

    @app.get("/reviews")
    def list_reviews(limit: int = 50) -> dict[str, Any]:
        return {"reviews": run_store.list_reviews(limit=limit)}

    @app.post("/reviews/{request_id}")
    def save_review(request_id: str, request: ReviewRequest) -> dict[str, Any]:
        try:
            return run_store.save_review(
                request_id=request_id,
                decision=request.decision,
                feedback=request.feedback,
                reviewer=request.reviewer,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/emails/report")
    def send_report(request: EmailReportRequest) -> dict[str, Any]:
        report_markdown = request.report_markdown
        source_request_id = request.request_id.strip() if request.request_id else None
        if not report_markdown and source_request_id:
            saved_report = run_store.get_report(source_request_id)
            if saved_report is None:
                raise HTTPException(status_code=404, detail="report not found")
            report_markdown = saved_report.get("markdown")
        if not report_markdown:
            raise HTTPException(status_code=400, detail="report content is required")

        subject = request.subject or (
            f"Agentic HR 候选人评估报告 - {source_request_id}" if source_request_id else "Agentic HR 候选人评估报告"
        )
        result = send_report_email(
            recipient=request.recipient,
            subject=subject,
            report_markdown=report_markdown,
            attachment_name=f"{source_request_id or 'agentic-hr-report'}.md",
        )
        return run_store.save_email_delivery(
            request_id=source_request_id,
            recipient=request.recipient,
            subject=subject,
            sent=result.sent,
            message=result.message,
        )

    @app.get("/emails/deliveries")
    def list_email_deliveries(limit: int = 50) -> dict[str, Any]:
        return {"deliveries": run_store.list_email_deliveries(limit=limit)}

    @app.get("/runs/{request_id}")
    def get_run(request_id: str) -> dict[str, Any]:
        saved = run_store.get_run(request_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="run not found")
        return saved

    @app.delete("/runs/{request_id}")
    def delete_run(request_id: str) -> dict[str, Any]:
        if not run_store.delete_run(request_id):
            raise HTTPException(status_code=404, detail="run not found")
        return {"request_id": request_id, "deleted": True}

    @app.get("/", response_class=HTMLResponse)
    def serve_frontend_index():
        index_path = frontend_root / "index.html"
        if not index_path.exists():
            return HTMLResponse(
                "<h1>Agentic HR API</h1><p>Build frontend with: cd frontend && npm run build</p>",
                status_code=200,
            )
        return FileResponse(index_path)

    @app.get("/{full_path:path}")
    def serve_frontend_asset(full_path: str) -> FileResponse:
        candidate = (frontend_root / full_path).resolve()
        try:
            candidate.relative_to(frontend_root.resolve())
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc
        if candidate.is_file():
            return FileResponse(candidate)
        index_path = frontend_root / "index.html"
        if index_path.exists() and "." not in Path(full_path).name:
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="asset not found")

    return app


app = create_app()
