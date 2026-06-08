from __future__ import annotations

from graph.workflow import build_workflow
from harness.evaluator import evaluate_workflow_result
from harness.replay import build_replay_case, initial_state_from_replay_case, load_replay_case, save_replay_case
from harness.test_cases import sample_candidate_case


def run_evaluation(
    *,
    resume_file_path: str | None = None,
    resume_text: str | None = None,
    jd_text: str | None = None,
    request_id: str | None = None,
    human_decision: str | None = None,
    human_feedback: str | None = None,
    persist_human_feedback: bool = False,
    feedback_memory_path: str | None = None,
    risk_model_path: str | None = None,
    enable_llm_report_enhancement: bool | None = None,
    include_quality_check: bool = False,
    save_replay: bool = False,
    replay_dir: str | None = None,
) -> dict:
    workflow = build_workflow()
    initial_state = sample_candidate_case()

    if resume_file_path is not None:
        initial_state["resume_file_path"] = resume_file_path
    if resume_text is not None:
        initial_state["resume_text"] = resume_text
    if jd_text is not None:
        initial_state["jd_text"] = jd_text
    if request_id is not None:
        initial_state["request_id"] = request_id
    if human_decision is not None:
        initial_state["human_decision"] = human_decision
    if human_feedback is not None:
        initial_state["human_feedback"] = human_feedback
    if persist_human_feedback:
        initial_state["persist_human_feedback"] = True
    if feedback_memory_path is not None:
        initial_state["feedback_memory_path"] = feedback_memory_path
    if risk_model_path is not None:
        initial_state["risk_model_path"] = risk_model_path
    if enable_llm_report_enhancement is not None:
        initial_state["enable_llm_report_enhancement"] = enable_llm_report_enhancement

    result = workflow.invoke(initial_state)
    if include_quality_check:
        result["report_quality"] = evaluate_workflow_result(result).as_dict()
    if save_replay:
        replay_case = build_replay_case(initial_state=initial_state, result=result)
        result["replay_path"] = str(save_replay_case(replay_case, replay_dir=replay_dir or "data/replay_cases"))
    return result


def replay_evaluation(replay_path: str, *, include_comparison: bool = True) -> dict:
    workflow = build_workflow()
    replay_case = load_replay_case(replay_path)
    result = workflow.invoke(initial_state_from_replay_case(replay_case))
    if include_comparison:
        from harness.replay import compare_replay_result

        result["replay_comparison"] = compare_replay_result(
            replay_case=replay_case,
            result=result,
        )
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
    if result.get("replay_path"):
        print(f"Replay case: {result.get('replay_path')}")
    if result.get("replay_comparison"):
        print(f"Replay comparison: {result.get('replay_comparison')}")
    print(f"Document parser: {(result.get('document_meta') or {}).get('parser')}")
    print(f"Needs OCR: {(result.get('document_meta') or {}).get('needs_ocr')}")
    print("\n--- Report ---")
    print(result.get("report"))
    print("\n--- Trace ---")
    for item in result.get("trace", []):
        print(f"{item['node']}: {item['output_summary']}")
