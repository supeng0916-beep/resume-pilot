from __future__ import annotations

from harness.batch_runner import BatchResumeInput, run_batch_evaluation
from core.store_factory import create_run_store


def run_batch_evaluation_job(job_id: str, request_payload: dict) -> dict:
    store = create_run_store()
    store.mark_evaluation_job_running(job_id)
    try:
        resumes = [
            BatchResumeInput(
                candidate_id=item["candidate_id"],
                resume_text=item.get("resume_text"),
                resume_file_path=item.get("resume_file_path"),
            )
            for item in request_payload.get("resumes", [])
        ]
        result = run_batch_evaluation(
            resumes,
            jd_text=request_payload.get("jd_text"),
            request_id=request_payload.get("request_id") or "queued-batch",
            risk_model_path=request_payload.get("risk_model_path"),
            enable_llm_structured_extraction=request_payload.get("enable_llm_structured_extraction"),
            enable_llm_report_enhancement=request_payload.get("enable_llm_report_enhancement"),
        )
        for workflow_result in result.get("results", []):
            store.save_workflow_result(workflow_result)
        store.save_batch_result(result)
        store.complete_evaluation_job(job_id, result)
        return result
    except Exception as exc:
        store.fail_evaluation_job(job_id, str(exc))
        raise
