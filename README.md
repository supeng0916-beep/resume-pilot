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

The current version is a walking skeleton with text-based PDF parsing and mock extraction/evaluation nodes. It runs end to end without LLMs, databases, or trained ML models.

## OCR for Scanned Resumes

Image-only PDF resumes are detected with `needs_ocr=True`. The parser has optional local OCR adapters. EasyOCR is used first on the current Windows demo environment, with PaddleOCR kept as an additional provider:

```powershell
python -m pip install -r requirements-ocr.txt
```

When OCR dependencies are available, scanned PDFs are rendered page by page and passed through local OCR. If OCR dependencies or model files are not available, the workflow keeps running and marks the candidate for OCR/manual review instead of ranking them as a reliable match.
