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

Start the local control cabin:

```powershell
D:\python\python.exe -m streamlit run app\streamlit_app.py
```

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

The current version runs an end-to-end LangGraph HR evaluation workflow with batch ranking, OCR fallback, replay harness, human review, report export, a Streamlit control cabin, and optional email delivery. It still runs without a real LLM, database, or trained cloud model by default.

## Optional LLM Enhancement

The report writer can append an LLM-assisted summary and interview-question enhancement. It is disabled by default. Create a local `.env` file in the project root and keep it out of git:

```powershell
HR_LLM_ENABLED=true
HR_LLM_API_KEY=your-api-key
HR_LLM_MODEL=your-model-name
HR_LLM_BASE_URL=https://api.openai.com/v1/chat/completions
HR_LLM_TIMEOUT_SECONDS=30
HR_LLM_IGNORE_PROXY=true
```

`HR_LLM_BASE_URL` expects an OpenAI-compatible Chat Completions endpoint. If the LLM is disabled, missing config, or the request fails, the deterministic report is still generated.

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
