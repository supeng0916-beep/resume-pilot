from __future__ import annotations

import json
from pathlib import Path

from core.risk_model import extract_risk_features, predict_risk_score
from nodes.risk_evaluator import risk_evaluator_node


def _sample_state() -> dict:
    return {
        "match_score": 80,
        "candidate_profile": {
            "expected_salary": "40k CNY/month",
            "years_experience": 1,
            "candidate_track": "experienced",
        },
        "job_profile": {
            "salary_range": "25k-35k CNY/month",
            "required_years": 3,
        },
        "match_breakdown": {
            "matched_skills": ["Python", "Redis"],
            "evidence_notes": ["Redis: 暂未找到项目证据。"],
        },
        "trace": [],
    }


def test_extract_risk_features_captures_salary_and_experience_pressure() -> None:
    features = extract_risk_features(_sample_state())

    assert features["match_gap"] == 0.2
    assert features["salary_pressure"] > 0
    assert features["experience_gap"] > 0.6
    assert features["evidence_gap"] == 0.5


def test_predict_risk_score_uses_json_model_weights() -> None:
    features = {
        "match_gap": 0.2,
        "salary_unknown": 0,
        "salary_pressure": 1,
        "experience_gap": 0.6,
        "evidence_gap": 0.5,
        "track_unknown": 0,
    }
    model = {
        "model_type": "logistic_risk_v1",
        "feature_order": list(features.keys()),
        "bias": -2.0,
        "weights": {
            "match_gap": 2.0,
            "salary_unknown": 0.5,
            "salary_pressure": 1.0,
            "experience_gap": 1.5,
            "evidence_gap": 1.0,
            "track_unknown": 0.5,
        },
    }

    assert predict_risk_score(model, features) == 0.69


def test_risk_evaluator_uses_model_when_path_exists() -> None:
    model_path = Path("data/test_outputs/test_risk_model.json")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text(
        json.dumps(
            {
                "model_type": "logistic_risk_v1",
                "feature_order": [
                    "match_gap",
                    "salary_unknown",
                    "salary_pressure",
                    "experience_gap",
                    "evidence_gap",
                    "track_unknown",
                ],
                "bias": -2.0,
                "weights": {
                    "match_gap": 2.0,
                    "salary_unknown": 0.5,
                    "salary_pressure": 1.0,
                    "experience_gap": 1.5,
                    "evidence_gap": 1.0,
                    "track_unknown": 0.5,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    state = _sample_state()
    state["risk_model_path"] = str(model_path)

    result = risk_evaluator_node(state)

    assert result["risk_model_used"] == "ml_logistic_json"
    assert result["risk_score"] == 0.67
    assert result["risk_features"]["experience_gap"] > 0
    assert "ML risk score" in result["trace"][-1]["output_summary"]
