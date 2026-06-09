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
        <h2>New batch evaluation</h2>
      </div>
      <form className="form-grid" onSubmit={submitForm}>
        <label>
          <span>Request ID</span>
          <input value={requestId} onChange={(event) => setRequestId(event.target.value)} />
        </label>
        <label>
          <span>Risk model path</span>
          <input value={riskModelPath} onChange={(event) => setRiskModelPath(event.target.value)} />
        </label>
        <label className="wide">
          <span>Job description</span>
          <textarea value={jdText} onChange={(event) => setJdText(event.target.value)} rows={4} />
        </label>
        <label className="wide">
          <span>Resume texts</span>
          <textarea value={resumeTexts} onChange={(event) => setResumeTexts(event.target.value)} rows={7} />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmExtraction}
            onChange={(event) => setEnableLlmExtraction(event.target.checked)}
          />
          <span>Enable LLM structured extraction</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={enableLlmReport}
            onChange={(event) => setEnableLlmReport(event.target.checked)}
          />
          <span>Enable LLM report enhancement</span>
        </label>
        <div className="form-actions wide">
          <button className="button-primary" type="submit" disabled={isRunning || splitResumeTexts(resumeTexts).length === 0}>
            {isRunning ? "Running..." : "Run batch"}
          </button>
        </div>
      </form>
      <form className="upload-form" onSubmit={submitUpload}>
        <label className="wide">
          <span>Resume files</span>
          <input
            aria-label="Resume files"
            type="file"
            accept=".txt,.md,.pdf"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <div className="upload-summary">
          {files.length ? `${files.length} file(s) selected` : "Upload .txt, .md, or .pdf resumes"}
        </div>
        <div className="form-actions">
          <button className="button-secondary" type="submit" disabled={isRunning || files.length === 0}>
            Upload and run
          </button>
        </div>
      </form>
    </section>
  );
}
