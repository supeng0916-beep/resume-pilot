import { useState } from "react";
import type { BatchEvaluationRequest, UploadBatchEvaluationRequest } from "../api/types";

interface BatchEvaluationPageProps {
  isRunning: boolean;
  onSubmit: (request: BatchEvaluationRequest) => Promise<void>;
  onUploadSubmit: (request: UploadBatchEvaluationRequest) => Promise<void>;
}

function splitResumeTexts(value: string) {
  return value
    .split(/\n---+\n/g)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((resumeText, index) => ({
      candidate_id: `candidate-${String(index + 1).padStart(3, "0")}`,
      resume_text: resumeText
    }));
}

export function BatchEvaluationPage({ isRunning, onSubmit, onUploadSubmit }: BatchEvaluationPageProps) {
  const [requestId, setRequestId] = useState(`react-batch-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "")}`);
  const [jdText, setJdText] = useState("Backend engineer requires Python, FastAPI and Redis.");
  const [resumeTexts, setResumeTexts] = useState(
    "Alice. Bachelor. Python FastAPI Redis project. Expected salary 18k CNY/month.\n---\nBob. Master. PyTorch SQL data pipeline. Expected salary 32k CNY/month."
  );
  const [riskModelPath, setRiskModelPath] = useState("models/review_risk_model.json");
  const [enableLlmExtraction, setEnableLlmExtraction] = useState(false);
  const [enableLlmReport, setEnableLlmReport] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  async function submitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      request_id: requestId.trim(),
      jd_text: jdText.trim(),
      risk_model_path: riskModelPath.trim() || undefined,
      enable_llm_structured_extraction: enableLlmExtraction,
      enable_llm_report_enhancement: enableLlmReport,
      resumes: splitResumeTexts(resumeTexts)
    });
  }

  async function submitUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onUploadSubmit({
      request_id: requestId.trim(),
      jd_text: jdText.trim(),
      risk_model_path: riskModelPath.trim() || undefined,
      enable_llm_structured_extraction: enableLlmExtraction,
      enable_llm_report_enhancement: enableLlmReport,
      files
    });
  }

  return (
    <section className="panel" id="new-batch">
      <div className="panel__header">
        <h2>新建批量评估</h2>
      </div>
      <form className="form-grid" onSubmit={submitForm}>
        <label>
          <span>请求 ID</span>
          <input value={requestId} onChange={(event) => setRequestId(event.target.value)} />
        </label>
        <label>
          <span>风险模型路径</span>
          <input value={riskModelPath} onChange={(event) => setRiskModelPath(event.target.value)} />
        </label>
        <label className="wide">
          <span>岗位 JD</span>
          <textarea value={jdText} onChange={(event) => setJdText(event.target.value)} rows={4} />
        </label>
        <label className="wide">
          <span>简历文本</span>
          <textarea value={resumeTexts} onChange={(event) => setResumeTexts(event.target.value)} rows={7} />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmExtraction}
            onChange={(event) => setEnableLlmExtraction(event.target.checked)}
          />
          <span>启用 LLM 结构化抽取</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmReport}
            onChange={(event) => setEnableLlmReport(event.target.checked)}
          />
          <span>启用 LLM 报告增强</span>
        </label>
        <div className="form-actions wide">
          <button className="button-primary" type="submit" disabled={isRunning || splitResumeTexts(resumeTexts).length === 0}>
            {isRunning ? "评估中..." : "运行批量评估"}
          </button>
        </div>
      </form>
      <form className="upload-form" onSubmit={submitUpload}>
        <label className="wide">
          <span>简历文件</span>
          <input
            aria-label="简历文件"
            type="file"
            accept=".txt,.md,.pdf"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <div className="upload-summary">
          {files.length ? `已选择 ${files.length} 个文件` : "上传 .txt、.md 或 .pdf 简历"}
        </div>
        <div className="form-actions">
          <button className="button-secondary" type="submit" disabled={isRunning || files.length === 0}>
            上传并评估
          </button>
        </div>
      </form>
    </section>
  );
}
