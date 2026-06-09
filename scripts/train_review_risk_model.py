from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.dataset_builder import load_jsonl
from core.review_risk_model import (
    build_review_risk_rows,
    evaluate_classifier,
    render_model_card,
    train_review_risk_model,
)


def _labels_with_annotations(labels: list[dict], annotations: list[dict]) -> list[dict]:
    by_sample_id = {str(label.get("sample_id")): dict(label) for label in labels}
    for annotation in annotations:
        sample_id = str(annotation.get("sample_id"))
        if sample_id not in by_sample_id:
            continue
        annotation_labels = annotation.get("labels") or {}
        merged = dict(by_sample_id[sample_id])
        merged.update(
            {
                "match_label": annotation_labels.get("match_label", merged.get("match_label")),
                "needs_human_review": annotation_labels.get(
                    "needs_human_review",
                    merged.get("needs_human_review"),
                ),
                "risk_labels": annotation_labels.get("risk_labels", merged.get("risk_labels", [])),
                "evidence_quality": annotation_labels.get(
                    "evidence_quality",
                    merged.get("evidence_quality"),
                ),
                "label_reason": (annotation.get("annotation") or {}).get(
                    "notes",
                    merged.get("label_reason"),
                ),
            }
        )
        by_sample_id[sample_id] = merged
    return list(by_sample_id.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Train manual-review risk model from Agentic HR JSONL data.")
    parser.add_argument("--dataset-dir", default="data/datasets")
    parser.add_argument("--annotations", default="data/datasets/annotations.jsonl")
    parser.add_argument("--output", default="models/review_risk_model.json")
    parser.add_argument("--model-card", default="models/model_card_review_risk.md")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--learning-rate", type=float, default=0.06)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    candidates = load_jsonl(dataset_dir / "synthetic_candidates.jsonl")
    jobs = load_jsonl(dataset_dir / "synthetic_jobs.jsonl")
    labels = load_jsonl(dataset_dir / "synthetic_labels.jsonl")
    annotations = load_jsonl(args.annotations)
    labels = _labels_with_annotations(labels, annotations)

    rows = build_review_risk_rows(candidates, jobs, labels)
    model = train_review_risk_model(rows, epochs=args.epochs, learning_rate=args.learning_rate)
    metrics = evaluate_classifier(model, rows, threshold=args.threshold)
    model["evaluation"] = metrics

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    model_card_path = Path(args.model_card)
    model_card_path.parent.mkdir(parents=True, exist_ok=True)
    model_card_path.write_text(render_model_card(model, metrics), encoding="utf-8")

    print(f"Rows: {len(rows)}")
    print(f"Annotations merged: {len(annotations)}")
    print(f"Metrics: {metrics}")
    print(f"Wrote model: {output_path}")
    print(f"Wrote model card: {model_card_path}")


if __name__ == "__main__":
    main()
