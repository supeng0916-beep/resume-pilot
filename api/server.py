from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.persistence import SQLiteRunStore
from harness.batch_runner import BatchResumeInput, run_batch_evaluation
from harness.runner import run_evaluation


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


def create_app(*, store: SQLiteRunStore | None = None) -> FastAPI:
    run_store = store or SQLiteRunStore()
    run_store.initialize()
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

    @app.get("/runs")
    def list_runs(limit: int = 50) -> dict[str, Any]:
        return {"runs": run_store.list_runs(limit=limit)}

    @app.get("/runs/{request_id}")
    def get_run(request_id: str) -> dict[str, Any]:
        saved = run_store.get_run(request_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="run not found")
        return saved

    return app


app = create_app()
