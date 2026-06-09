from __future__ import annotations

from core.dataset_builder import generate_synthetic_dataset
from core.review_risk_model import (
    build_review_risk_rows,
    evaluate_classifier,
    predict_review_risk_score,
    render_model_card,
    split_train_validation,
    train_review_risk_model,
)


def test_build_review_risk_rows_joins_dataset_and_extracts_features() -> None:
    dataset = generate_synthetic_dataset(count=9, seed=11)

    rows = build_review_risk_rows(dataset.candidates, dataset.jobs, dataset.labels)

    assert len(rows) == 9
    assert rows[0]["sample_id"] == "case_0001"
    assert set(rows[0]["features"]) == {
        "required_skill_coverage",
        "parse_quality_gap",
        "salary_pressure",
        "experience_gap",
        "evidence_gap",
        "track_unknown",
        "weak_match",
    }
    assert rows[0]["label"] in {0.0, 1.0}


def test_train_review_risk_model_returns_predictable_json_model() -> None:
    dataset = generate_synthetic_dataset(count=30, seed=12)
    rows = build_review_risk_rows(dataset.candidates, dataset.jobs, dataset.labels)

    model = train_review_risk_model(rows, epochs=20, learning_rate=0.08)
    score = predict_review_risk_score(model, rows[0]["features"])

    assert model["model_type"] == "review_risk_logistic_v1"
    assert model["target"] == "needs_human_review"
    assert model["training"]["rows"] == 30
    assert 0.0 <= score <= 1.0


def test_split_train_validation_is_reproducible_and_stratified_enough() -> None:
    dataset = generate_synthetic_dataset(count=120, seed=15)
    rows = build_review_risk_rows(dataset.candidates, dataset.jobs, dataset.labels)

    first_train, first_validation = split_train_validation(rows, validation_ratio=0.2, seed=3)
    second_train, second_validation = split_train_validation(rows, validation_ratio=0.2, seed=3)

    assert first_train == second_train
    assert first_validation == second_validation
    assert len(first_train) == 96
    assert len(first_validation) == 24
    assert {row["label"] for row in first_train} == {0.0, 1.0}
    assert {row["label"] for row in first_validation} == {0.0, 1.0}


def test_evaluate_classifier_and_model_card_include_landing_disclaimer() -> None:
    dataset = generate_synthetic_dataset(count=30, seed=13)
    rows = build_review_risk_rows(dataset.candidates, dataset.jobs, dataset.labels)
    model = train_review_risk_model(rows, epochs=15, learning_rate=0.08)

    metrics = evaluate_classifier(model, rows, threshold=0.5)
    model_card = render_model_card(model, metrics)

    assert set(metrics) >= {"accuracy", "precision", "recall", "f1", "positive_rate"}
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert "人工复核风险模型" in model_card
    assert "不用于自动录用或淘汰候选人" in model_card
