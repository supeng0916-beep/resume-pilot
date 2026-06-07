from __future__ import annotations

import re

from core.state import WorkflowState
from harness.trace import add_trace


def _extract_salary_number(value: str | None) -> float | None:
    if not value or value == "unknown":
        return None
    match = re.search(r"([\d.]+)\s*(k|K|万)?", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "万":
        return number * 10
    return number


def _extract_salary_range(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    match = re.search(r"([\d.]+)\s*k?\s*-\s*([\d.]+)\s*k?", value, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def risk_evaluator_node(state: WorkflowState) -> WorkflowState:
    match_score = state.get("match_score") or 0
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}

    risk_score = 0.18 if match_score >= 85 else 0.30 if match_score >= 70 else 0.42
    risk_factors: list[str] = []

    expected_salary = _extract_salary_number(candidate.get("expected_salary"))
    salary_range = _extract_salary_range(job.get("salary_range"))

    if expected_salary is None:
        risk_score += 0.05
        risk_factors.append("候选人期望薪资未知，需要人工确认薪资预期和到岗时间。")
    elif salary_range is not None:
        _, upper = salary_range
        if expected_salary > upper:
            risk_score += 0.12
            risk_factors.append("候选人期望薪资高于岗位预算上限，需要确认 offer 接受可能性。")
        elif expected_salary >= upper * 0.9:
            risk_score += 0.05
            risk_factors.append("候选人期望薪资接近岗位预算上沿，需要面试确认稳定性。")

    if not risk_factors:
        risk_factors.append("当前未发现显著流程级风险，建议继续通过面试核实项目深度。")

    risk_score = round(min(risk_score, 0.95), 2)

    return {
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "current_step": "risk_evaluator",
        "trace": add_trace(
            state,
            "risk_evaluator",
            f"Estimated rule-based risk score: {risk_score}.",
            {"risk_factors": risk_factors},
        ),
    }
