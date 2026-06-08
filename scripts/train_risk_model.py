from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


FEATURES = [
    "match_gap",
    "salary_unknown",
    "salary_pressure",
    "experience_gap",
    "evidence_gap",
    "track_unknown",
]


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _load_rows(path: str) -> list[dict[str, float]]:
    with Path(path).open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            {name: float(row[name]) for name in [*FEATURES, "label"]}
            for row in reader
        ]


def train_logistic_model(rows: list[dict[str, float]], *, epochs: int, learning_rate: float) -> dict:
    weights = {name: 0.0 for name in FEATURES}
    bias = 0.0

    for _ in range(epochs):
        for row in rows:
            logit = bias + sum(weights[name] * row[name] for name in FEATURES)
            prediction = _sigmoid(logit)
            error = prediction - row["label"]
            bias -= learning_rate * error
            for name in FEATURES:
                weights[name] -= learning_rate * error * row[name]

    return {
        "model_type": "logistic_risk_v1",
        "feature_order": FEATURES,
        "bias": round(bias, 6),
        "weights": {name: round(value, 6) for name, value in weights.items()},
        "training": {
            "rows": len(rows),
            "epochs": epochs,
            "learning_rate": learning_rate,
            "data_source": "synthetic",
            "disclaimer": "Synthetic data is only for project demonstration, not real hiring prediction.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a lightweight synthetic HR risk model.")
    parser.add_argument("--input", default="data/synthetic_risk_data.csv")
    parser.add_argument("--output", default="models/risk_model.json")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    args = parser.parse_args()

    rows = _load_rows(args.input)
    model = train_logistic_model(rows, epochs=args.epochs, learning_rate=args.learning_rate)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote risk model to {output_path}")


if __name__ == "__main__":
    main()
