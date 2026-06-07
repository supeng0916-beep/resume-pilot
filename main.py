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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print_result(
        run_evaluation(
            resume_file_path=args.resume,
            jd_text=args.jd,
            request_id=args.request_id,
        )
    )
