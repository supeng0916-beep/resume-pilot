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
