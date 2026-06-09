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
  const [requestId, setRequestId] = useState(
    `react-batch-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "")}`
  );
  const [jdText, setJdText] = useState(
    "后端工程师，要求熟悉 Python、FastAPI、Redis，有项目落地经验，能和业务团队沟通需求。"
  );
  const [resumeTexts, setResumeTexts] = useState(
    "候选人 Alice，本科，参与过 Python FastAPI Redis 项目，期望薪资 18k。\n---\n候选人 Bob，硕士，做过 PyTorch 与 SQL 数据管道项目，期望薪资 32k。"
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
        <div>
          <h2>创建评估批次</h2>
          <p>粘贴岗位 JD 与候选人简历，或上传 PDF/文本简历，生成可复核的候选人排序。</p>
        </div>
      </div>
      <form className="form-grid" onSubmit={submitForm}>
        <label>
          <span>批次编号</span>
          <input value={requestId} onChange={(event) => setRequestId(event.target.value)} />
        </label>
        <label>
          <span>复核风险模型</span>
          <input value={riskModelPath} onChange={(event) => setRiskModelPath(event.target.value)} />
        </label>
        <label className="wide">
          <span>岗位 JD / 招聘要求</span>
          <textarea value={jdText} onChange={(event) => setJdText(event.target.value)} rows={4} />
        </label>
        <label className="wide">
          <span>候选人简历文本</span>
          <textarea value={resumeTexts} onChange={(event) => setResumeTexts(event.target.value)} rows={7} />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmExtraction}
            onChange={(event) => setEnableLlmExtraction(event.target.checked)}
          />
          <span>使用 LLM 辅助抽取简历字段</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmReport}
            onChange={(event) => setEnableLlmReport(event.target.checked)}
          />
          <span>使用 LLM 增强面试建议</span>
        </label>
        <div className="form-actions wide">
          <button className="button-primary" type="submit" disabled={isRunning || splitResumeTexts(resumeTexts).length === 0}>
            {isRunning ? "评估中..." : "开始评估候选人"}
          </button>
        </div>
      </form>
      <form className="upload-form" onSubmit={submitUpload}>
        <label className="wide">
          <span>上传候选人简历</span>
          <input
            aria-label="简历文件"
            type="file"
            accept=".txt,.md,.pdf"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <div className="upload-summary">
          {files.length ? `已选择 ${files.length} 份简历` : "支持 .txt、.md 或 .pdf 简历"}
        </div>
        <div className="form-actions">
          <button className="button-secondary" type="submit" disabled={isRunning || files.length === 0}>
            上传并开始评估
          </button>
        </div>
      </form>
    </section>
  );
}
