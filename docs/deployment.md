# Deployment

AgenticHR production-style deployment uses:

```text
FastAPI API
React static frontend bundled into the API image
PostgreSQL primary database
Redis queue
RQ worker
```

## Local Production Stack

Copy the production example environment and edit secrets before real deployment:

```powershell
Copy-Item .env.production.example .env.production
```

Start the stack:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8000
http://localhost:8000/runtime
```

## Database Selection

Local default:

```env
HR_SQLITE_PATH=data/hr_runs.sqlite3
```

PostgreSQL:

```env
HR_DATABASE_URL=postgresql+psycopg://agentic_hr:agentic_hr_password@postgres:5432/agentic_hr
```

If `HR_DATABASE_URL` or `DATABASE_URL` is set, the API uses `SQLAlchemyRunStore`. Otherwise it falls back to `SQLiteRunStore`.

## Async Job Flow

```text
POST /batch-evaluations/jobs
  -> persist evaluation_jobs.status = queued
  -> enqueue Redis/RQ job if Redis is available
  -> fallback to FastAPI background task if Redis is not available
  -> worker runs LangGraph batch evaluation
  -> worker writes runs, batches, agent metrics, Supervisor decisions, and final job result
GET /jobs/{job_id}
  -> poll status and result
```

Redis is not the source of truth. PostgreSQL stores trusted job status and evaluation results.

## Worker

Inside Docker Compose, the worker runs:

```text
python scripts/start_worker.py
```

For local development with a running Redis:

```powershell
$env:HR_REDIS_URL="redis://localhost:6379/0"
$env:HR_DATABASE_URL="sqlite+pysqlite:///data/dev_hr_runs.sqlite3"
D:\python\python.exe scripts\start_worker.py
```

## Minimal Server Checklist

- Configure HTTPS at a reverse proxy.
- Set real database and SMTP credentials through environment variables.
- Back up PostgreSQL daily.
- Keep Redis private to the server network.
- Do not expose Ollama directly to the public internet.
- Use `/runtime` to confirm database and queue readiness before demos.
