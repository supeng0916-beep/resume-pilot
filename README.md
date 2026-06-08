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

The current version runs an end-to-end LangGraph HR evaluation workflow with batch ranking, OCR fallback, replay harness, human review, report export, a Streamlit control cabin, and optional email delivery. It still runs without a real LLM, database, or trained cloud model by default.

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

Run the control-cabin focused tests:

```powershell
D:\python\python.exe -m pytest tests\test_control_cabin.py tests\test_batch_runner.py -q
```

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
