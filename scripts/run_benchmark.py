from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from harness.benchmark import BenchmarkInput, run_benchmark


def _load_jsonl(path: str | Path, *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
            if len(rows) >= limit:
                break
    return rows


def _candidate_to_resume_text(row: dict[str, Any]) -> str:
    skills = "、".join(str(skill) for skill in row.get("skills", []))
    projects = "；".join(str(project) for project in row.get("projects", []))
    salary = row.get("expected_salary_k")
    salary_text = f"{salary}k" if salary is not None else "unknown"
    return (
        f"姓名：{row.get('name', row.get('candidate_id', '未知候选人'))}\n"
        f"学历：{row.get('education', '未知')}\n"
        f"专业：{row.get('major', '未知')}\n"
        f"工作年限：{row.get('years_experience', 0)} 年\n"
        f"技能：{skills}\n"
        f"项目经历：{projects}\n"
        f"期望薪资：{salary_text}"
    )


def _build_inputs(rows: list[dict[str, Any]]) -> list[BenchmarkInput]:
    return [
        BenchmarkInput(
            candidate_id=str(row.get("candidate_id") or f"candidate-{index:03d}"),
            resume_text=_candidate_to_resume_text(row),
        )
        for index, row in enumerate(rows, start=1)
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AgenticHR benchmark over synthetic or redacted resumes.")
    parser.add_argument("--candidates", default="data/datasets/synthetic_candidates.jsonl")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--request-id", default="benchmark-50")
    parser.add_argument("--price-per-1k-tokens", type=float, default=0.0)
    parser.add_argument("--output", default="data/test_outputs/benchmark_report.json")
    parser.add_argument(
        "--jd",
        default="招聘 Python 后端工程师，要求 Python、FastAPI、Redis、SQL，有项目落地经验优先。",
    )
    parser.add_argument("--enable-llm-structured-extraction", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = _load_jsonl(args.candidates, limit=args.limit)
    result = run_benchmark(
        _build_inputs(rows),
        jd_text=args.jd,
        request_id=args.request_id,
        price_per_1k_tokens=args.price_per_1k_tokens,
        enable_llm_structured_extraction=args.enable_llm_structured_extraction,
        enable_llm_report_enhancement=False,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"Benchmark report saved to {output_path}")


if __name__ == "__main__":
    main()
