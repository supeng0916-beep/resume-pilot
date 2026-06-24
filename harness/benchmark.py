from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from harness.runner import run_evaluation


@dataclass(frozen=True)
class BenchmarkInput:
    candidate_id: str
    resume_text: str | None = None
    resume_file_path: str | None = None


def _sum_token_usage(results: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    for result in results:
        metrics = result.get("agent_metrics") or {}
        for item in metrics.values():
            if not isinstance(item, dict):
                continue
            usage = item.get("token_usage")
            if not isinstance(usage, dict):
                continue
            totals["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
            totals["completion_tokens"] += int(usage.get("completion_tokens") or 0)
            totals["total_tokens"] += int(usage.get("total_tokens") or 0)
    return totals


def summarize_benchmark_results(
    results: list[dict[str, Any]],
    *,
    input_count: int,
    price_per_1k_tokens: float = 0.0,
) -> dict[str, Any]:
    total_duration_ms = sum(int(result.get("duration_ms") or 0) for result in results)
    passed_schema = sum(1 for result in results if not result.get("validation_errors"))
    token_usage = _sum_token_usage(results)
    return {
        "candidate_count": input_count,
        "completed_count": len(results),
        "schema_pass_rate": round(passed_schema / max(input_count, 1), 4),
        "total_duration_ms": total_duration_ms,
        "average_duration_ms": round(total_duration_ms / max(len(results), 1), 2),
        "total_retry_count": sum(int(result.get("retry_count") or 0) for result in results),
        "token_usage": token_usage,
        "estimated_cost": round(token_usage["total_tokens"] / 1000 * price_per_1k_tokens, 8),
    }


def run_benchmark(
    inputs: list[BenchmarkInput],
    *,
    jd_text: str,
    request_id: str = "benchmark",
    price_per_1k_tokens: float = 0.0,
    enable_llm_structured_extraction: bool | None = None,
    enable_llm_report_enhancement: bool | None = False,
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for index, item in enumerate(inputs, start=1):
        started = perf_counter()
        result = run_evaluation(
            resume_file_path=item.resume_file_path,
            resume_text=item.resume_text,
            jd_text=jd_text,
            request_id=f"{request_id}-{index:03d}-{item.candidate_id}",
            enable_llm_structured_extraction=enable_llm_structured_extraction,
            enable_llm_report_enhancement=enable_llm_report_enhancement,
        )
        duration_ms = int((perf_counter() - started) * 1000)
        runs.append(
            {
                "candidate_id": item.candidate_id,
                "request_id": result.get("request_id"),
                "duration_ms": duration_ms,
                "match_score": result.get("match_score"),
                "risk_score": result.get("risk_score"),
                "validation_errors": result.get("validation_errors", []),
                "retry_count": result.get("retry_count", 0),
                "agent_metrics": result.get("agent_metrics", {}),
                "specialist_execution": result.get("specialist_execution"),
                "supervisor_decisions": result.get("supervisor_decisions", []),
                "trace": result.get("trace", []),
            }
        )

    return {
        "request_id": request_id,
        "summary": summarize_benchmark_results(
            runs,
            input_count=len(inputs),
            price_per_1k_tokens=price_per_1k_tokens,
        ),
        "runs": runs,
    }
