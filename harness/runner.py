from __future__ import annotations

from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case


def run_demo() -> dict:
    workflow = build_workflow()
    initial_state = sample_candidate_case()
    return workflow.invoke(initial_state)


def print_result(result: dict) -> None:
    print("\n=== Agentic HR Walking Skeleton ===")
    print(f"Request: {result.get('request_id')}")
    print(f"Current step: {result.get('current_step')}")
    print(f"Match score: {result.get('match_score')}")
    print(f"Risk score: {result.get('risk_score')}")
    print("\n--- Report ---")
    print(result.get("report"))
    print("\n--- Trace ---")
    for item in result.get("trace", []):
        print(f"{item['node']}: {item['output_summary']}")
