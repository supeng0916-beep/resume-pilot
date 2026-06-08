from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


FEATURES = [
    "match_gap",
    "salary_unknown",
    "salary_pressure",
    "experience_gap",
    "evidence_gap",
    "track_unknown",
]


def _risk_probability(row: dict[str, float]) -> float:
    score = (
        -2.0
        + 2.8 * row["match_gap"]
        + 0.6 * row["salary_unknown"]
        + 1.2 * row["salary_pressure"]
        + 1.6 * row["experience_gap"]
        + 1.1 * row["evidence_gap"]
        + 0.5 * row["track_unknown"]
    )
    return 1.0 / (1.0 + pow(2.718281828, -score))


def generate_rows(count: int, seed: int) -> list[dict[str, float | int]]:
    rng = random.Random(seed)
    rows: list[dict[str, float | int]] = []
    for _ in range(count):
        row = {
            "match_gap": round(rng.betavariate(2, 5), 4),
            "salary_unknown": float(rng.random() < 0.18),
            "salary_pressure": round(rng.betavariate(1.5, 5), 4),
            "experience_gap": round(rng.betavariate(1.5, 6), 4),
            "evidence_gap": round(rng.betavariate(1.3, 5), 4),
            "track_unknown": float(rng.random() < 0.08),
        }
        probability = _risk_probability(row)
        row["label"] = int(rng.random() < probability)
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic HR risk training data.")
    parser.add_argument("--output", default="data/synthetic_risk_data.csv")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(args.count, args.seed)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[*FEATURES, "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic rows to {output_path}")


if __name__ == "__main__":
    main()
