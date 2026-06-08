from __future__ import annotations

import argparse
from pathlib import Path

from harness.batch_runner import resume_inputs_from_paths, run_batch_evaluation
from harness.runner import print_result, replay_evaluation, run_evaluation


def write_report_output(output_path: str, report: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Agentic HR evaluation workflow.")
    parser.add_argument(
        "--resume",
        action="append",
        help="Path to a candidate resume PDF. Falls back to mock resume text if omitted.",
    )
    parser.add_argument(
        "--jd",
        help="Job description text. Uses the demo JD if omitted.",
    )
    parser.add_argument(
        "--request-id",
        default="cli-run",
        help="Request id shown in traces and output.",
    )
    parser.add_argument(
        "--human-decision",
        choices=["approve", "reject", "revise", "need_more_info"],
        help="Optional human review decision to record after the report is generated.",
    )
    parser.add_argument(
        "--human-feedback",
        help="Optional human reviewer feedback. Used together with --human-decision.",
    )
    parser.add_argument(
        "--persist-human-feedback",
        action="store_true",
        help="Persist human review feedback to a local JSON memory file.",
    )
    parser.add_argument(
        "--feedback-memory-path",
        help="Path for persisted human feedback memory. Defaults to memory/review_feedback.json.",
    )
    parser.add_argument(
        "--risk-model-path",
        help="Optional JSON risk model path. Falls back to rule-based risk scoring if omitted or missing.",
    )
    parser.add_argument(
        "--save-replay",
        action="store_true",
        help="Save this run as a replay case for regression testing.",
    )
    parser.add_argument(
        "--replay-dir",
        help="Directory for saved replay cases. Defaults to data/replay_cases.",
    )
    parser.add_argument(
        "--replay",
        help="Run the workflow from a saved replay case JSON file.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the generated Markdown report.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.replay:
        print_result(replay_evaluation(args.replay))
        raise SystemExit(0)

    if args.resume and len(args.resume) > 1:
        batch_result = run_batch_evaluation(
            resume_inputs_from_paths(args.resume),
            jd_text=args.jd,
            request_id=args.request_id,
            feedback_memory_path=args.feedback_memory_path,
            risk_model_path=args.risk_model_path,
        )
        print(batch_result["batch_report"])
        if args.output:
            write_report_output(args.output, batch_result["batch_report"])
        raise SystemExit(0)

    result = run_evaluation(
        resume_file_path=args.resume[0] if args.resume else None,
        jd_text=args.jd,
        request_id=args.request_id,
        human_decision=args.human_decision,
        human_feedback=args.human_feedback,
        persist_human_feedback=args.persist_human_feedback,
        feedback_memory_path=args.feedback_memory_path,
        risk_model_path=args.risk_model_path,
        save_replay=args.save_replay,
        replay_dir=args.replay_dir,
    )
    print_result(result)
    if args.output:
        write_report_output(args.output, result.get("report") or "")
