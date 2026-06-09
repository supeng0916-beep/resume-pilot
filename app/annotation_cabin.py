from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.dataset_builder import append_annotation_record, load_jsonl  # noqa: E402


DEFAULT_DATASET_DIR = Path("data/datasets")
DEFAULT_ANNOTATION_PATH = DEFAULT_DATASET_DIR / "annotations.jsonl"


def _find_row(rows: list[dict], key: str, value: str) -> dict:
    return next((row for row in rows if row.get(key) == value), {})


def main() -> None:
    st.set_page_config(page_title="Agentic HR 标注舱", layout="wide")
    st.title("Agentic HR 标注舱")

    with st.sidebar:
        dataset_dir = Path(st.text_input("数据集目录", value=str(DEFAULT_DATASET_DIR)))
        annotation_path = Path(st.text_input("标注输出", value=str(DEFAULT_ANNOTATION_PATH)))
        annotator = st.text_input("标注人", value="human_001")

    candidates = load_jsonl(dataset_dir / "synthetic_candidates.jsonl")
    jobs = load_jsonl(dataset_dir / "synthetic_jobs.jsonl")
    labels = load_jsonl(dataset_dir / "synthetic_labels.jsonl")
    if not candidates or not jobs or not labels:
        st.warning("请先运行 scripts/generate_dataset.py 生成 synthetic_candidates/jobs/labels.jsonl。")
        return

    label_options = {
        f"{label.get('sample_id')} | {label.get('candidate_id')} -> {label.get('jd_id')}": label
        for label in labels
    }
    selected = st.selectbox("选择样本", options=list(label_options))
    label = label_options[selected]
    candidate = _find_row(candidates, "candidate_id", label["candidate_id"])
    job = _find_row(jobs, "jd_id", label["jd_id"])

    left, middle, right = st.columns([1, 1, 1])
    with left:
        st.subheader("候选人画像")
        st.json(candidate)
    with middle:
        st.subheader("岗位画像")
        st.json(job)
    with right:
        st.subheader("当前标签")
        st.json(label)

    st.divider()
    st.subheader("人工修正与标注")
    candidate_json = st.text_area(
        "修正后的候选人画像 JSON",
        value=json.dumps(candidate, ensure_ascii=False, indent=2),
        height=260,
    )
    job_json = st.text_area(
        "修正后的岗位画像 JSON",
        value=json.dumps(job, ensure_ascii=False, indent=2),
        height=220,
    )

    col_label, col_review, col_evidence = st.columns(3)
    with col_label:
        match_label = st.selectbox(
            "匹配标签",
            options=["strong_match", "partial_match", "weak_match"],
            index=["strong_match", "partial_match", "weak_match"].index(label.get("match_label", "partial_match")),
        )
    with col_review:
        needs_human_review = st.checkbox("需要人工复核", value=bool(label.get("needs_human_review")))
    with col_evidence:
        evidence_quality = st.selectbox(
            "证据质量",
            options=["strong", "medium", "weak", "unsupported"],
            index=["strong", "medium", "weak", "unsupported"].index(label.get("evidence_quality", "medium")),
        )

    risk_options = ["salary_pressure", "evidence_gap", "experience_gap", "parse_low_quality", "track_unknown"]
    risk_labels = st.multiselect("风险标签", options=risk_options, default=label.get("risk_labels", []))
    notes = st.text_area("标注备注", value=label.get("label_reason", ""), height=100)

    if st.button("保存标注", type="primary"):
        try:
            corrected_candidate = json.loads(candidate_json)
            corrected_job = json.loads(job_json)
        except json.JSONDecodeError as exc:
            st.error(f"JSON 格式错误：{exc}")
            return

        record = append_annotation_record(
            annotation_path,
            sample_id=label["sample_id"],
            resume_id=label["resume_id"],
            jd_id=label["jd_id"],
            corrected_candidate_profile=corrected_candidate,
            corrected_job_profile=corrected_job,
            labels={
                "match_label": match_label,
                "needs_human_review": needs_human_review,
                "risk_labels": risk_labels,
                "evidence_quality": evidence_quality,
            },
            annotator=annotator,
            notes=notes,
        )
        st.success(f"已保存标注：{record['sample_id']} -> {annotation_path}")


if __name__ == "__main__":
    main()
