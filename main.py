from __future__ import annotations

import argparse

from harness.runner import print_result, run_evaluation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Agentic HR evaluation workflow.")
    parser.add_argument(
        "--resume",
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print_result(
        run_evaluation(
            resume_file_path=args.resume,
            jd_text=args.jd,
            request_id=args.request_id,
            human_decision=args.human_decision,
            human_feedback=args.human_feedback,
            persist_human_feedback=args.persist_human_feedback,
            feedback_memory_path=args.feedback_memory_path,
        )
    )
