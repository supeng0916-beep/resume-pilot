from __future__ import annotations

from graph.workflow import build_workflow
from harness.replay import (
    build_replay_case,
    compare_replay_result,
    initial_state_from_replay_case,
    load_replay_case,
    save_replay_case,
)
from harness.runner import replay_evaluation, run_evaluation
from harness.test_cases import sample_candidate_case


def test_replay_case_can_be_saved_and_loaded() -> None:
    initial_state = sample_candidate_case()
    result = build_workflow().invoke(initial_state)

    replay_case = build_replay_case(initial_state=initial_state, result=result)
    replay_path = save_replay_case(replay_case, replay_dir="data/test_outputs/replay_cases")
    loaded = load_replay_case(replay_path)

    assert loaded["schema_version"] == 1
    assert loaded["request_id"] == "demo-001"
    assert loaded["input"]["jd_text"] == initial_state["jd_text"]
    assert loaded["observed"]["match_score"] == result["match_score"]
    assert loaded["observed"]["report_quality"]["passed"] is True
    assert loaded["observed"]["trace"][0]["node"] == "supervisor"


def test_replay_case_can_rebuild_initial_state_and_compare_result() -> None:
    initial_state = sample_candidate_case()
    result = build_workflow().invoke(initial_state)
    replay_case = build_replay_case(initial_state=initial_state, result=result)

    replay_state = initial_state_from_replay_case(replay_case)
    replay_result = build_workflow().invoke(replay_state)
    comparison = compare_replay_result(replay_case=replay_case, result=replay_result)

    assert replay_state["request_id"] == "demo-001"
    assert comparison["passed"] is True


def test_runner_can_save_and_replay_case() -> None:
    result = run_evaluation(
        request_id="runner-replay-test",
        save_replay=True,
        replay_dir="data/test_outputs/replay_cases",
    )

    replay_result = replay_evaluation(result["replay_path"])

    assert result["replay_path"].endswith(".json")
    assert replay_result["request_id"] == "runner-replay-test"
    assert replay_result["replay_comparison"]["passed"] is True
