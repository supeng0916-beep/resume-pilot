from __future__ import annotations

from graph.workflow import build_workflow
from harness.evaluator import evaluate_workflow_result
from harness.test_cases import sample_candidate_case


def run_evaluation(
    *,
    resume_file_path: str | None = None,
    jd_text: str | None = None,
    request_id: str | None = None,
    human_decision: str | None = None,
    human_feedback: str | None = None,
    include_quality_check: bool = False,
) -> dict:
    workflow = build_workflow()
    initial_state = sample_candidate_case()

    if resume_file_path is not None:
        initial_state["resume_file_path"] = resume_file_path
    if jd_text is not None:
        initial_state["jd_text"] = jd_text
    if request_id is not None:
        initial_state["request_id"] = request_id
    if human_decision is not None:
        initial_state["human_decision"] = human_decision
    if human_feedback is not None:
        initial_state["human_feedback"] = human_feedback

    result = workflow.invoke(initial_state)
    if include_quality_check:
        result["report_quality"] = evaluate_workflow_result(result).as_dict()
    return result


def run_demo() -> dict:
    return run_evaluation()


def print_result(result: dict) -> None:
    print("\n=== Agentic HR Walking Skeleton ===")
    print(f"Request: {result.get('request_id')}")
    print(f"Current step: {result.get('current_step')}")
    print(f"Match score: {result.get('match_score')}")
    print(f"Risk score: {result.get('risk_score')}")
    print(f"Human review: {result.get('human_review_status')}")
    print(f"Document parser: {(result.get('document_meta') or {}).get('parser')}")
    print(f"Needs OCR: {(result.get('document_meta') or {}).get('needs_ocr')}")
    print("\n--- Report ---")
    print(result.get("report"))
    print("\n--- Trace ---")
    for item in result.get("trace", []):
        print(f"{item['node']}: {item['output_summary']}")
