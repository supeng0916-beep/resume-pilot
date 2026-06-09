from __future__ import annotations

from core.risk_model import (
    DEFAULT_RISK_MODEL_PATH,
    build_model_risk_factors,
    extract_risk_features,
    extract_salary_number,
    extract_salary_range,
    load_risk_model,
    predict_risk_score,
)
from core.review_risk_model import (
    build_review_risk_factors,
    extract_review_risk_features_from_state,
    predict_review_risk_score,
)
from core.state import WorkflowState
from harness.trace import add_trace


def _evaluate_with_model(state: WorkflowState) -> dict | None:
    model_path = state.get("risk_model_path") or DEFAULT_RISK_MODEL_PATH
    model = load_risk_model(model_path)
    if model is None:
        return None

    if model.get("model_type") == "review_risk_logistic_v1":
        features = extract_review_risk_features_from_state(state)
        risk_score = predict_review_risk_score(model, features)
        risk_factors = build_review_risk_factors(features, risk_score)
        return {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "risk_features": features,
            "risk_model_used": "review_risk_logistic_json",
            "risk_model_path": model_path,
            "current_step": "risk_evaluator",
            "trace": add_trace(
                state,
                "risk_evaluator",
                f"Estimated manual-review risk score: {risk_score}.",
                {
                    "risk_model_used": "review_risk_logistic_json",
                    "risk_model_path": model_path,
                    "risk_features": features,
                    "risk_factors": risk_factors,
                },
            ),
        }

    features = extract_risk_features(state)
    risk_score = predict_risk_score(model, features)
    risk_factors = build_model_risk_factors(features)

    return {
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "risk_features": features,
        "risk_model_used": "ml_logistic_json",
        "risk_model_path": model_path,
        "current_step": "risk_evaluator",
        "trace": add_trace(
            state,
            "risk_evaluator",
            f"Estimated ML risk score: {risk_score}.",
            {
                "risk_model_used": "ml_logistic_json",
                "risk_model_path": model_path,
                "risk_features": features,
                "risk_factors": risk_factors,
            },
        ),
    }


def risk_evaluator_node(state: WorkflowState) -> WorkflowState:
    model_result = _evaluate_with_model(state)
    if model_result is not None:
        return model_result

    match_score = state.get("match_score") or 0
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}

    risk_score = 0.18 if match_score >= 85 else 0.30 if match_score >= 70 else 0.42
    risk_factors: list[str] = []

    expected_salary = extract_salary_number(candidate.get("expected_salary"))
    salary_range = extract_salary_range(job.get("salary_range"))

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
        "risk_features": extract_risk_features(state),
        "risk_model_used": "rule_based",
        "current_step": "risk_evaluator",
        "trace": add_trace(
            state,
            "risk_evaluator",
            f"Estimated rule-based risk score: {risk_score}.",
            {"risk_model_used": "rule_based", "risk_factors": risk_factors},
        ),
    }
