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

The current version is a walking skeleton with text-based PDF parsing and mock extraction/evaluation nodes. It runs end to end without LLMs, databases, or trained ML models.

## OCR for Scanned Resumes

Image-only PDF resumes are detected with `needs_ocr=True`. The parser has optional local OCR adapters. EasyOCR is used first on the current Windows demo environment, with PaddleOCR kept as an additional provider:

```powershell
python -m pip install -r requirements-ocr.txt
```

When OCR dependencies are available, scanned PDFs are rendered page by page and passed through local OCR. If OCR dependencies or model files are not available, the workflow keeps running and marks the candidate for OCR/manual review instead of ranking them as a reliable match.
