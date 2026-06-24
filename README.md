# Resume Pilot

Resume Pilot is a Supervisor-centered multi-agent recruiting evaluation system built with LangGraph, FastAPI, PostgreSQL, Redis/RQ, and React.

It is designed to support structured resume screening workflows, not to make automated hiring decisions. The system focuses on evidence-grounded evaluation, traceable agent outputs, batch processing, human review, and repeatable regression testing.

## Features

- **Supervisor-centered LangGraph workflow**: a central Supervisor routes state across deterministic nodes and specialist agents.
- **Specialist agents**: Candidate Analyst, Job Analyst, Memory Agent, Evidence Auditor, Critic Agent, Consensus Agent, and Reporting Agent.
- **Evidence-based evaluation**: scoring is tied to extracted skills, job requirements, document quality, and review risk.
- **Production-oriented data layer**: PostgreSQL via SQLAlchemy for deployment, Redis/RQ for asynchronous jobs, and SQLite only as a local fallback.
- **Local model support**: OpenAI-compatible providers and Ollama are supported through a shared model gateway.
- **Document processing**: PyMuPDF for text PDFs, optional OCR for scanned PDFs, and optional LLM-assisted extraction.
- **Batch upload deduplication**: uploaded resumes are hashed with SHA-256; duplicate files in the same batch are skipped before parsing and evaluation.
- **Harness and regression testing**: batch runner, replay, benchmark, LLM extraction evaluation, report quality checks, and automated tests.
- **React operations console**: batch evaluation, candidate run history, review queue, run detail, report preview, and record deletion.

## Architecture

```text
Supervisor
  -> Document Parser
  -> Resume Extractor
  -> JD Extractor
  -> Schema Validator
  -> Parallel Specialists
       - Candidate Analyst
       - Job Analyst
       - Memory Agent
  -> Rubric Selector
  -> Matcher
  -> Risk Evaluator
  -> Evidence Auditor
  -> Critic Agent
  -> Consensus Agent
  -> Report Writer
  -> Supervisor Review Router
  -> Human Review
```

Key modules:

```text
api/          FastAPI service and REST endpoints
core/         schemas, parsing, model gateway, stores, risk model, agent contracts
graph/        LangGraph workflow and routing
nodes/        workflow nodes and specialist agents
harness/      batch runner, replay, benchmark, and evaluation utilities
frontend/     React + Vite web console
scripts/      startup, benchmark, LLM evaluation, and training scripts
tests/        backend regression tests
docs/         architecture, deployment, and production-readiness notes
workers/      Redis/RQ worker entry points
```

Further reading:

- `docs/multi_agent_architecture.md`
- `docs/architecture_diagrams.md`
- `docs/production_readiness.md`
- `docs/deployment.md`
- `docs/benchmark_usage.md`

## Requirements

- Python 3.11+
- Node.js 20+
- PostgreSQL and Redis for deployment
- Optional: Ollama for local LLM inference
- Optional: OCR dependencies for scanned PDF parsing

## Quick Start

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install optional OCR dependencies:

```powershell
python -m pip install -r requirements-ocr.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Start the backend and frontend in development mode:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```

Open the web console:

```text
http://127.0.0.1:5173
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Configuration

### PostgreSQL

Production deployments should set `HR_DATABASE_URL`:

```text
HR_DATABASE_URL=postgresql+psycopg://agentic_hr:agentic_hr_password@localhost:5432/agentic_hr
```

If `HR_DATABASE_URL` is not set, the application falls back to local SQLite for single-user development.

### Ollama

Example local Ollama configuration:

```text
HR_LLM_ENABLED=true
HR_LLM_PROVIDER=ollama
HR_LLM_API_KEY=local
HR_LLM_MODEL=qwen3:1.7b
HR_LLM_BASE_URL=http://localhost:11434/v1
HR_LLM_TIMEOUT_SECONDS=120
HR_LLM_STRUCTURED_EXTRACTION_ENABLED=false
HR_AGENT_LLM_ENABLED=true
```

### Redis/RQ

Set `HR_REDIS_URL` to enable Redis-backed queueing:

```text
HR_REDIS_URL=redis://localhost:6379/0
```

Without Redis, local development falls back to FastAPI background tasks.

## CLI Usage

Run the built-in sample:

```powershell
python main.py
```

Evaluate one local PDF:

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "Backend engineer with Python, FastAPI, PostgreSQL and Redis experience."
```

Evaluate multiple local PDFs:

```powershell
python main.py --resume C:\path\to\candidate-a.pdf --resume C:\path\to\candidate-b.pdf --jd "AI engineer with Python and ML project experience."
```

Disable LLM report enhancement for deterministic regression runs:

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "AI engineer with Python and ML project experience." --disable-llm-report-enhancement
```

## API Examples

Run a text-based evaluation:

```powershell
curl -X POST http://127.0.0.1:8000/evaluations `
  -H "Content-Type: application/json" `
  -d "{\"request_id\":\"api-demo-001\",\"resume_text\":\"Candidate Alice. Python FastAPI Redis project.\",\"jd_text\":\"Backend engineer requires Python, FastAPI and Redis.\",\"risk_model_path\":\"models/review_risk_model.json\"}"
```

Query results:

```powershell
curl http://127.0.0.1:8000/runs/api-demo-001
curl "http://127.0.0.1:8000/runs?status=pending&limit=20&offset=0"
curl "http://127.0.0.1:8000/batches?limit=20&offset=0"
```

Delete evaluation records:

```powershell
curl -X DELETE http://127.0.0.1:8000/runs/api-demo-001
curl -X DELETE http://127.0.0.1:8000/runs
```

## Batch Upload Deduplication

For `/batch-evaluations/uploads`, the backend computes a SHA-256 hash for each uploaded file. If two files in the same batch have identical content, only the first file is saved and evaluated. Duplicates are returned in the response:

```json
{
  "skipped_duplicate_count": 1,
  "skipped_duplicates": [
    {
      "filename": "alice-copy.pdf",
      "duplicate_of": "alice.pdf",
      "sha256": "..."
    }
  ]
}
```

This prevents duplicated parsing work and avoids unnecessary OCR/LLM token usage within a batch.

## Testing

Run backend tests:

```powershell
python -m pytest -q
```

Run frontend tests and build:

```powershell
cd frontend
npm test -- --run
npm run build
```

Run benchmark smoke checks:

```powershell
python scripts\run_benchmark.py --count 5 --output data\test_outputs\benchmark_smoke.json
```

Run LLM extraction evaluation:

```powershell
python scripts\run_llm_eval.py --cases data\datasets\extraction_eval_cases.jsonl --output data\test_outputs\llm_extraction_eval_report.md
```

## Docker Deployment

The Docker Compose stack includes FastAPI, PostgreSQL, Redis, and an RQ worker:

```powershell
docker compose --env-file .env.production.example up --build
```

When services inside Docker need to call Ollama on the host machine, use:

```text
HR_LLM_BASE_URL=http://host.docker.internal:11434/v1
```

## Repository Hygiene

The following files are intentionally excluded from version control:

- `.env` and local secrets
- local SQLite fallback databases
- uploaded resumes and PDFs
- OCR/model caches
- generated reports, replay cases, and test outputs
- `node_modules` and frontend build output
- Python cache directories

Tracked files under `data/datasets/` are synthetic or redacted examples used for tests and harness workflows.

## Privacy And Safety

Resume Pilot should be used as a decision-support and review-assistance tool. It should not be presented as an automated hiring decision system. Real resumes should be redacted or handled under appropriate privacy controls before being used for evaluation, testing, or demonstration.

## License

No open-source license has been selected yet. Add a `LICENSE` file before distributing this project as open-source software.
