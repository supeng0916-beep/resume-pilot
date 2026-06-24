from __future__ import annotations

from harness.benchmark import BenchmarkInput, run_benchmark, summarize_benchmark_results


def test_summarize_benchmark_results_calculates_schema_latency_and_tokens() -> None:
    summary = summarize_benchmark_results(
        [
            {
                "duration_ms": 100,
                "validation_errors": [],
                "retry_count": 0,
                "agent_metrics": {
                    "candidate_analyst": {
                        "token_usage": {
                            "prompt_tokens": 10,
                            "completion_tokens": 5,
                            "total_tokens": 15,
                        }
                    }
                },
            },
            {
                "duration_ms": 300,
                "validation_errors": ["candidate_profile.name: missing"],
                "retry_count": 2,
                "agent_metrics": {
                    "critic_agent": {
                        "token_usage": {
                            "prompt_tokens": 20,
                            "completion_tokens": 10,
                            "total_tokens": 30,
                        }
                    }
                },
            },
        ],
        input_count=2,
        price_per_1k_tokens=0.002,
    )

    assert summary["candidate_count"] == 2
    assert summary["schema_pass_rate"] == 0.5
    assert summary["total_duration_ms"] == 400
    assert summary["average_duration_ms"] == 200
    assert summary["total_retry_count"] == 2
    assert summary["token_usage"]["total_tokens"] == 45
    assert summary["estimated_cost"] == 0.00009


def test_run_benchmark_executes_multiple_resumes() -> None:
    result = run_benchmark(
        [
            BenchmarkInput(
                candidate_id="a",
                resume_text="姓名：Alice\n本科\nPython FastAPI Redis 项目\n期望薪资：20k",
            ),
            BenchmarkInput(
                candidate_id="b",
                resume_text="姓名：Bob\n本科\nJavaScript Vue 项目\n期望薪资：18k",
            ),
        ],
        jd_text="招聘 Python 后端工程师，要求 Python、FastAPI、Redis。",
        request_id="benchmark-test",
    )

    assert result["summary"]["candidate_count"] == 2
    assert len(result["runs"]) == 2
    assert result["runs"][0]["candidate_id"] == "a"
    assert result["runs"][0]["duration_ms"] >= 0


def test_run_benchmark_records_supervisor_decisions() -> None:
    result = run_benchmark(
        [BenchmarkInput(candidate_id="a", resume_text="Alice Python FastAPI project")],
        jd_text="Backend engineer with Python and FastAPI.",
        request_id="decision-benchmark",
    )

    decisions = result["runs"][0]["supervisor_decisions"]
    assert decisions
    assert decisions[0]["stage"] == "initial_plan"
