from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.dataset_builder import generate_synthetic_dataset, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic structured HR dataset JSONL files.")
    parser.add_argument("--output-dir", default="data/datasets")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset = generate_synthetic_dataset(count=args.count, seed=args.seed)
    output_dir = Path(args.output_dir)
    candidates_path = write_jsonl(output_dir / "synthetic_candidates.jsonl", dataset.candidates)
    jobs_path = write_jsonl(output_dir / "synthetic_jobs.jsonl", dataset.jobs)
    labels_path = write_jsonl(output_dir / "synthetic_labels.jsonl", dataset.labels)

    print(f"Wrote {len(dataset.candidates)} candidates to {candidates_path}")
    print(f"Wrote {len(dataset.jobs)} jobs to {jobs_path}")
    print(f"Wrote {len(dataset.labels)} labels to {labels_path}")


if __name__ == "__main__":
    main()
