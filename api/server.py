from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.persistence import SQLiteRunStore
from harness.batch_runner import BatchResumeInput, run_batch_evaluation
from harness.runner import run_evaluation

DEFAULT_UPLOAD_DIR = Path("data/api_uploads")


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


def _safe_upload_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip().replace("\x00", "")
    return safe_name or "resume.txt"


def create_app(*, store: SQLiteRunStore | None = None, upload_dir: str | Path = DEFAULT_UPLOAD_DIR) -> FastAPI:
    run_store = store or SQLiteRunStore()
    run_store.initialize()
    upload_root = Path(upload_dir)
    app = FastAPI(title="Agentic HR API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        run_store.initialize()
        return {"status": "ok", "storage": "sqlite"}

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
        return result

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

        for index, upload in enumerate(files, start=1):
            filename = _safe_upload_filename(upload.filename or f"resume-{index}.txt")
            content = await upload.read()
            path = run_dir / f"{index:03d}_{filename}"
            path.write_bytes(content)
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
        return result

    @app.get("/runs")
    def list_runs(limit: int = 50) -> dict[str, Any]:
        return {"runs": run_store.list_runs(limit=limit)}

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

    @app.get("/runs/{request_id}")
    def get_run(request_id: str) -> dict[str, Any]:
        saved = run_store.get_run(request_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="run not found")
        return saved

    return app


app = create_app()
