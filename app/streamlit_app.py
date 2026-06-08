from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.control_cabin import (  # noqa: E402
    apply_human_review,
    build_ranking_rows,
    candidates_needing_review,
    save_batch_report,
    save_uploaded_resumes,
)
from core.email_sender import send_report_email  # noqa: E402
from harness.batch_runner import resume_inputs_from_paths, run_batch_evaluation  # noqa: E402


DEFAULT_JD = "校招 AI 工程师，要求 Python、机器学习、深度学习和项目经历。"


def main() -> None:
    st.set_page_config(page_title="Agentic HR 控制舱", layout="wide")
    st.title("Agentic HR 控制舱")

    with st.sidebar:
        st.subheader("评估配置")
        request_id = st.text_input(
            "请求 ID",
            value=f"cabin-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )
        feedback_memory_path = st.text_input("反馈记忆路径", value="memory/review_feedback.json")
        risk_model_path = st.text_input("风险模型路径", value="")
        enable_llm_report_enhancement = st.checkbox("逐候选人 LLM 报告增强", value=False)

    jd_text = st.text_area("岗位 JD", value=DEFAULT_JD, height=140)
    uploaded_files = st.file_uploader(
        "候选人简历 PDF",
        type=["pdf"],
        accept_multiple_files=True,
    )

    run_clicked = st.button("运行批量评估", type="primary", disabled=not uploaded_files)
    if run_clicked:
        with st.spinner("正在解析简历并评估候选人..."):
            saved_paths = save_uploaded_resumes(uploaded_files, request_id=request_id)
            progress_bar = st.progress(0)
            status_box = st.empty()

            def update_progress(index, total, resume, status):
                completed = index if status == "completed" else index - 1
                current = min(completed / max(total, 1), 1.0)
                progress_bar.progress(current)
                status_label = "正在处理" if status == "started" else "已完成"
                current_file = Path(resume.resume_file_path or resume.candidate_id).name
                status_box.info(f"{status_label} {index}/{total}: {current_file}")

            batch_result = run_batch_evaluation(
                resume_inputs_from_paths(saved_paths),
                jd_text=jd_text,
                request_id=request_id,
                feedback_memory_path=feedback_memory_path or None,
                risk_model_path=risk_model_path or None,
                enable_llm_report_enhancement=enable_llm_report_enhancement,
                progress_callback=update_progress,
            )
            progress_bar.progress(1.0)
            status_box.success(f"批量评估完成：{len(saved_paths)} 份简历")
            report_path = save_batch_report(batch_result, request_id=request_id)
            st.session_state["batch_result"] = batch_result
            st.session_state["report_path"] = str(report_path)

    batch_result = st.session_state.get("batch_result")
    if not batch_result:
        st.info("上传多份 PDF 简历并运行评估后，这里会显示候选人排名、人工复核队列和批量报告。")
        return

    review_needed = candidates_needing_review(batch_result)
    col_count, col_review, col_report = st.columns(3)
    col_count.metric("候选人数", batch_result.get("candidate_count", 0))
    col_review.metric("人工复核", len(review_needed))
    col_report.metric("报告文件", Path(st.session_state["report_path"]).name)

    st.subheader("候选人排名")
    st.dataframe(build_ranking_rows(batch_result), use_container_width=True, hide_index=True)

    report_text = batch_result.get("batch_report") or ""
    tab_report, tab_review, tab_email, tab_detail = st.tabs(["报告预览", "人工复核", "邮件发送", "候选人详情"])

    with tab_report:
        st.markdown(report_text)
        st.download_button(
            "下载 Markdown 报告",
            data=report_text.encode("utf-8"),
            file_name=Path(st.session_state["report_path"]).name,
            mime="text/markdown",
        )

    with tab_review:
        if not review_needed:
            st.success("当前批次暂无额外人工复核标记。")
        for candidate in review_needed:
            st.warning(
                f"{candidate.get('name')}（{candidate.get('candidate_id')}）："
                f"{'; '.join(candidate.get('review_reasons') or ['需人工确认'])}"
            )

        st.divider()
        candidate_options = {
            f"{item.get('name')}（{item.get('candidate_id')}）": item.get("request_id")
            for item in batch_result.get("ranked_candidates", [])
            if item.get("request_id")
        }
        if candidate_options:
            with st.form("human_review_form"):
                selected_label = st.selectbox("审批候选人", options=list(candidate_options))
                decision = st.selectbox(
                    "审批结果",
                    options=["approve", "reject", "revise", "need_more_info"],
                )
                feedback = st.text_area("审批反馈", height=100)
                submitted = st.form_submit_button("记录审批反馈")

            if submitted:
                record = apply_human_review(
                    batch_result,
                    request_id=candidate_options[selected_label],
                    decision=decision,
                    feedback=feedback,
                    feedback_memory_path=feedback_memory_path or None,
                )
                st.session_state["batch_result"] = batch_result
                st.success(f"已记录审批反馈：{record['request_id']}")

    with tab_email:
        with st.form("email_report_form"):
            recipient = st.text_input("HR 邮箱")
            subject = st.text_input(
                "邮件主题",
                value=f"Agentic HR 批量候选人评估报告 - {batch_result.get('request_id')}",
            )
            send_clicked = st.form_submit_button("发送报告邮件")

        if send_clicked:
            delivery = send_report_email(
                recipient=recipient,
                subject=subject,
                report_markdown=report_text,
                attachment_name=Path(st.session_state["report_path"]).name,
            )
            if delivery.sent:
                st.success(delivery.message)
            else:
                st.warning(delivery.message)

    with tab_detail:
        results = batch_result.get("results", [])
        for index, result in enumerate(results, start=1):
            candidate = result.get("candidate_profile") or {}
            request = result.get("request_id") or f"candidate-{index}"
            with st.expander(f"{candidate.get('name', '未知候选人')} - {request}"):
                st.write(
                    {
                        "document_meta": result.get("document_meta"),
                        "human_review_status": result.get("human_review_status"),
                        "errors": result.get("errors"),
                    }
                )
                st.markdown(result.get("report") or "")


if __name__ == "__main__":
    main()
