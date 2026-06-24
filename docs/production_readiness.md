# Production Readiness

AgenticHR is no longer framed as a toy demo. It is a production-oriented prototype with explicit boundaries, observability, and validation harnesses. It is not yet a production hiring system.

## Already Implemented

- LangGraph supervisor-centered orchestration
- typed schema validation with retry and failure report
- structured multi-agent outputs via `AgentResult`
- Supervisor dynamic routing with skipped-agent reasons
- parallel specialist fan-out/fan-in for Supervisor-selected CandidateAnalyst, JobAnalyst, and MemoryAgent
- conditional evidence audit, critic, and consensus agents
- embedded deterministic skills for CandidateAnalyst and JobAnalyst with optional local LLM reasoning
- FastAPI service boundary
- React control cabin
- SQLAlchemy/PostgreSQL persistence for production runs, batches, agent runs, Supervisor decisions, reviews, email deliveries, and async jobs
- SQLite persistence as a local fallback when `HR_DATABASE_URL` is not configured
- trace and replay harness
- batch runner and benchmark runner
- report quality evaluation
- LLM extraction evaluation
- OpenAI-compatible local model gateway
- async batch job API with persisted job status
- Redis runtime readiness probe via `HR_REDIS_URL`

## Not Production Yet

- no authentication or role-based access control
- authentication and role-based access control are still not enforced
- long-running OCR and LLM jobs still run in-process unless an external worker is introduced
- no hosted tracing or alerting
- no formal bias audit
- no real redacted resume evaluation dataset committed
- no human reviewer identity and approval policy enforcement

## Current Production Direction

The current codebase is moving toward production by making every non-trivial decision observable and replayable:

- Supervisor records which agents were activated and which were skipped.
- Specialist agents emit the same `AgentResult` contract whether they use deterministic skills, local LLM reasoning, or fallback logic.
- MemoryAgent is no longer decorative; it is routed only when a feedback memory source is present.
- EvidenceAuditor and CriticAgent are conditional review agents, so low-risk, fully supported cases do not pay unnecessary latency or token cost.
- OCR-first parsing is separated from text LLM reasoning, so `qwen3:1.7b` is not misused as a vision parser.
- Batch evaluation can be submitted as a persisted job through `POST /batch-evaluations/jobs` and polled through `GET /jobs/{job_id}`.
- `GET /runtime` reports whether Redis is configured and reachable. Local development falls back to FastAPI background tasks.
- The control cabin run detail page now shows Supervisor routing decisions and per-agent execution metrics.

## Runtime Endpoints

```text
GET  /runtime
POST /batch-evaluations/jobs
GET  /jobs
GET  /jobs/{job_id}
```

`/runtime` does not require Redis. If `HR_REDIS_URL` is unset, the queue backend is reported as `fastapi_background_tasks`. If Redis is configured and reachable, the runtime reports `redis_ready`, which is the deployment signal for replacing in-process background execution with an external worker.

## Current Honest Positioning

The system should be described as:

> A supervisor-centered multi-agent recruiting evaluation prototype focused on explainability, evidence grounding, human review, replayability, and continuous evaluation.

It should not be described as:

> An autonomous hiring decision system.

The model target and recommendation output are intended to support human review, not replace final hiring judgment.
