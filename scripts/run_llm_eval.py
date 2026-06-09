from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.llm_eval import evaluate_extraction_case, render_extraction_eval_report


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    cases = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rule-vs-LLM extraction eval harness.")
    parser.add_argument(
        "--cases",
        default="data/datasets/extraction_eval_cases.jsonl",
        help="JSONL cases with resume_text, jd_text, golden_candidate and golden_job.",
    )
    parser.add_argument(
        "--output",
        default="data/test_outputs/llm_extraction_eval_report.md",
        help="Markdown report output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = [
        evaluate_extraction_case(
            case_id=case["case_id"],
            resume_text=case["resume_text"],
            jd_text=case["jd_text"],
            golden_candidate=case["golden_candidate"],
            golden_job=case["golden_job"],
            llm_candidate=case.get("llm_candidate"),
            llm_job=case.get("llm_job"),
        )
        for case in load_cases(args.cases)
    ]
    report = render_extraction_eval_report(results)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
