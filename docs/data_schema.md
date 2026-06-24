# Data Schema

This project uses JSONL for datasets and a FastAPI-managed runtime store. Production deployments should use PostgreSQL through SQLAlchemy; SQLite remains only as a local fallback when `HR_DATABASE_URL` is not configured. React reads runtime data only through FastAPI.

## Dataset Files

Default directory: `data/datasets/`

### `synthetic_candidates.jsonl`

One candidate per line.

```json
{
  "candidate_id": "cand-0001",
  "name": "Candidate 0001",
  "education": "硕士",
  "major": "计算机科学",
  "years_experience": 0,
  "candidate_track": "campus",
  "skills": ["Python", "FastAPI", "SQL"],
  "projects": ["校园招聘系统后端服务"],
  "expected_salary_k": 18
}
```

### `synthetic_jobs.jsonl`

One job per line.

```json
{
  "job_id": "job-0001",
  "title": "后端工程师",
  "recruitment_track": "campus",
  "required_years": 0,
  "required_skills": ["Python", "FastAPI", "Redis"],
  "salary_min_k": 12,
  "salary_max_k": 25
}
```

### `synthetic_labels.jsonl`

One candidate-job label per line.

```json
{
  "candidate_id": "cand-0001",
  "job_id": "job-0001",
  "match_score": 86.5,
  "needs_human_review": true,
  "review_reasons": ["salary_expectation_high", "evidence_missing"]
}
```

### `example_redacted_candidates.jsonl`

Committed examples showing the expected redacted format for real manually reviewed resumes. Do not commit private resumes or raw personally identifiable information.

### `extraction_eval_cases.jsonl`

Evaluation cases for comparing rule extraction, LLM extraction, and golden answers.

## Runtime Database

Production database: PostgreSQL via `HR_DATABASE_URL`.

Local fallback path: `data/hr_runs.sqlite3`.

Runtime databases are ignored by git. PostgreSQL is the intended deployment store; the SQLite file is only for local single-user development.

### Tables

`workflow_runs`

- `request_id`: primary key.
- `current_step`: latest workflow node.
- `match_score`: candidate-job score.
- `risk_score`: manual-review risk score.
- `human_review_status`: pending/reviewed status.
- `report`: generated Markdown report.
- `payload_json`: complete workflow payload.
- `trace_json`: complete trace payload.
- `created_at`, `updated_at`.

`candidates`

- `request_id`: primary key and workflow FK.
- `name`, `education`, `years_experience`, `candidate_track`, `expected_salary`.
- `profile_json`: full candidate profile.

`jobs`

- `request_id`: primary key and workflow FK.
- `title`, `required_years`, `recruitment_track`.
- `required_skills_json`, `profile_json`.

`traces`

- Node-level trace events for debugging, replay explanation, and React timeline rendering.

`reports`

- Markdown report and report-quality metadata.

`reviews`

- Human review decision, feedback, reviewer, and timestamp.

`batches`

- Batch-level summary, candidate count, top candidate, batch report, ranked candidates, and full batch payload.

`batch_runs`

- Join table between a batch and workflow runs, preserving candidate id and rank order.

`email_deliveries`

- Email audit log for report delivery attempts.
- Stores `request_id`, recipient, subject, sent flag, message, and timestamp.

## Privacy Boundaries

- `.env`, local database files, uploaded resumes, and private raw resumes must not be committed.
- Real samples should be redacted before entering JSONL datasets.
- The ML target is `needs_human_review`; do not label or present the model as a hiring-decision predictor.
