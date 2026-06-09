# Agentic HR

LangGraph-based multi-agent recruitment evaluation workflow.

## Quick Start

```powershell
python -m pip install -r requirements.txt
D:\python\python.exe main.py
```

Run with a resume PDF:

```powershell
D:\python\python.exe main.py --resume data\examples\candidate.pdf
```

Run with a custom JD:

```powershell
D:\python\python.exe main.py --resume data\examples\candidate.pdf --jd "招聘 Python 后端工程师，要求熟悉 FastAPI、PostgreSQL、Redis。"
```

Run a batch evaluation and save a Markdown report:

```powershell
D:\python\python.exe main.py --resume data\examples\candidate-a.pdf --resume data\examples\candidate-b.pdf --jd "校招 AI 工程师，要求 Python、机器学习和项目经历。" --output data\test_outputs\batch_report.md
```

For faster batch runs when LLM is enabled:

```powershell
D:\python\python.exe main.py --resume data\examples\candidate-a.pdf --resume data\examples\candidate-b.pdf --jd "校招 AI 工程师，要求 Python、机器学习和项目经历。" --disable-llm-report-enhancement
```

Start the local control cabin:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```

Open:

```text
http://127.0.0.1:8501
```

The Streamlit cabin is now kept as the legacy demo surface. The primary frontend direction is the React control cabin in `frontend/`.

Stop the local control cabin after testing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_control_cabin.ps1
```

If you run `D:\python\python.exe -m streamlit run app\streamlit_app.py` directly, the terminal will stay occupied because Streamlit is a long-running web server. That is expected behavior, not a hang.

Send batch reports from the control cabin by configuring SMTP environment variables:

```powershell
$env:HR_SMTP_HOST="smtp.example.com"
$env:HR_SMTP_PORT="465"
$env:HR_SMTP_USERNAME="your-email@example.com"
$env:HR_SMTP_PASSWORD="your-smtp-app-password"
$env:HR_SMTP_FROM="your-email@example.com"
$env:HR_SMTP_USE_SSL="true"
```

If SMTP is not configured, the control cabin will keep the report available for preview and download without sending email.

The current version runs an end-to-end LangGraph HR evaluation workflow with batch ranking, OCR fallback, replay harness, human review, report export, SQLite run persistence, a FastAPI service layer, a Streamlit control cabin, and optional email delivery. It still runs without a real LLM or trained cloud model by default.

## FastAPI Service

Start the API service:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_api.ps1
```

Open:

```text
http://127.0.0.1:8000/docs
```

Run one evaluation through the backend layer:

```powershell
curl -X POST http://127.0.0.1:8000/evaluations `
  -H "Content-Type: application/json" `
  -d "{\"request_id\":\"api-demo-001\",\"resume_text\":\"Candidate Alice. Python FastAPI Redis project.\",\"jd_text\":\"Backend engineer requires Python, FastAPI and Redis.\",\"risk_model_path\":\"models/review_risk_model.json\"}"
```

The service persists workflow runs to `data/hr_runs.sqlite3` by default. The database is ignored by git. Query a saved run:

```powershell
curl http://127.0.0.1:8000/runs/api-demo-001
```

## React Control Cabin

The React frontend is the new primary control cabin. It talks to FastAPI through HTTP and does not import Python workflow code directly.

Start FastAPI first:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_api.ps1
```

Then start the React dev server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_react_cabin.ps1
```

Open:

```text
http://127.0.0.1:5173
```

Frontend checks:

```powershell
cd frontend
npm test -- --run
npm run build
```

The current React cabin includes the app shell, health indicator, persisted run metrics, recent run table, and reusable detail components for trace/report views. It is intentionally API-first; new UI features should be backed by FastAPI endpoints rather than direct workflow calls.

The React cabin can run a demo batch from pasted resume text or uploaded resume files. Separate pasted resumes with a line containing `---`. The upload control calls FastAPI's multipart endpoint:

```text
POST /batch-evaluations/uploads
```

Accepted upload files:

- `.txt` / `.md`: read as resume text directly.
- `.pdf`: saved under `data/api_uploads/` and passed through the document parser.

Uploaded files are ignored by git.

## Docker

Build and run the demo control cabin without copying local secrets into the image:

```powershell
docker build -t agentic-hr .
docker run --rm -p 8501:8501 --env-file .env agentic-hr
```

If you do not need LLM, OCR, or SMTP integrations, omit `--env-file .env`.

The Docker image installs only `requirements.txt`. Local OCR dependencies stay optional in `requirements-ocr.txt` because EasyOCR/PaddleOCR are large and can make demo builds slow.

## Testing

Run the full regression suite:

```powershell
D:\python\python.exe -m pytest -q
```

Run frontend tests and build:

```powershell
cd frontend
npm test -- --run
npm run build
```

Run the control-cabin focused tests:

```powershell
D:\python\python.exe -m pytest tests\test_control_cabin.py tests\test_batch_runner.py -q
```

Run the LLM extraction evaluation harness. The committed sample cases include rule output, simulated LLM output, and golden answers so the report format is reproducible without calling a paid model:

```powershell
D:\python\python.exe scripts\run_llm_eval.py --cases data\datasets\extraction_eval_cases.jsonl --output data\test_outputs\llm_extraction_eval_report.md
```

The report compares rule extraction vs LLM extraction against the standard answer on field accuracy and skill F1.

## Dataset and Annotation

Generate a synthetic structured dataset for training, regression checks, and Colab experiments:

```powershell
D:\python\python.exe scripts\generate_dataset.py --output-dir data\datasets --count 60 --seed 42
```

The generator writes JSONL files:

- `data/datasets/synthetic_candidates.jsonl`
- `data/datasets/synthetic_jobs.jsonl`
- `data/datasets/synthetic_labels.jsonl`
- `data/datasets/example_redacted_candidates.jsonl` is a committed redacted sample format.
- `data/datasets/extraction_eval_cases.jsonl` is the committed extraction-eval harness sample.

Open the lightweight annotation cabin:

```powershell
D:\python\python.exe -m streamlit run app\annotation_cabin.py
```

Manual annotations are appended to `data/datasets/annotations.jsonl`. The recommended ML target is `needs_human_review`, not a direct hiring decision. See `docs/annotation_guideline.md` for label definitions and Colab handoff notes.

See `docs/data_schema.md` for JSONL schemas, privacy boundaries, and the SQLite persistence shape. See `docs/ml_pipeline.md` for the manual-review risk model training and deployment flow.

Train the lightweight manual-review risk model:

```powershell
D:\python\python.exe scripts\train_review_risk_model.py --dataset-dir data\datasets --output models\review_risk_model.json --model-card models\model_card_review_risk.md
```

The repository includes a demo `models\review_risk_model.json` trained on the 500-row synthetic dataset, plus `models\model_card_review_risk.md`. The model predicts whether a case needs human review. It is a process-risk model, not a hiring prediction model. Use it in CLI or the control cabin by setting the risk model path to `models\review_risk_model.json`.

The risk node supports two JSON model families:

- `logistic_risk_v1`: legacy synthetic risk score model.
- `review_risk_logistic_v1`: recommended manual-review risk model trained from `data/datasets/*.jsonl`.

## Optional LLM Enhancement

The report writer can append an LLM-assisted summary and interview-question enhancement. It is disabled by default. Create a local `.env` file in the project root and keep it out of git:

```powershell
HR_LLM_ENABLED=true
HR_LLM_API_KEY=your-api-key
HR_LLM_MODEL=your-model-name
HR_LLM_BASE_URL=https://api.openai.com/v1/chat/completions
HR_LLM_TIMEOUT_SECONDS=30
HR_LLM_IGNORE_PROXY=true
HR_LLM_PDF_MAX_PAGES=3
HR_IMAGE_PDF_PARSE_STRATEGY=vision_first
HR_ENABLE_LOCAL_OCR=false
HR_OCR_TIMEOUT_SECONDS=12
```

`HR_LLM_BASE_URL` expects an OpenAI-compatible Chat Completions endpoint. If the LLM is disabled, missing config, or the request fails, the deterministic report is still generated. For image-only PDFs, the parser defaults to `vision_first` and keeps local OCR disabled to avoid slow batch uploads. Set `HR_ENABLE_LOCAL_OCR=true` if you want EasyOCR/PaddleOCR fallback, with `HR_OCR_TIMEOUT_SECONDS` as the soft timeout.

The Streamlit control cabin disables per-candidate LLM report enhancement by default to keep batch uploads responsive. Turn on "逐候选人 LLM 报告增强" in the sidebar when you want richer individual reports.

## HR Tools

Reusable tool adapters live in `tools/hr_tools.py`. They wrap existing capabilities so future LLM agents can call them through a stable tool boundary:

- `parse_resume_pdf`
- `extract_resume_profile`
- `extract_jd_profile`
- `run_batch_evaluation`
- `save_batch_report`
- `send_report_email`

## OCR for Scanned Resumes

Image-only PDF resumes are detected with `needs_ocr=True`. The parser has optional local OCR adapters. EasyOCR is used first on the current Windows demo environment, with PaddleOCR kept as an additional provider:

```powershell
python -m pip install -r requirements-ocr.txt
```

When OCR dependencies are available, scanned PDFs are rendered page by page and passed through local OCR. If OCR dependencies or model files are not available, the workflow keeps running and marks the candidate for OCR/manual review instead of ranking them as a reliable match.
