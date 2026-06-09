# Remove Streamlit Control Cabin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make React + FastAPI the only control cabin path and remove Streamlit from runtime dependencies, scripts, docs, and user workflows.

**Architecture:** React owns the HR operator UI and calls FastAPI only. FastAPI owns workflow execution, SQLite persistence, review submission, report retrieval, and email delivery. Streamlit files, scripts, dependency entries, and documentation references are removed or rewritten as historical project-plan notes.

**Tech Stack:** FastAPI, SQLite, React, TypeScript, Vite, pytest, Vitest.

---

### Task 1: Remove Streamlit Runtime Surface

**Files:**
- Delete: `app/streamlit_app.py`
- Delete: `app/annotation_cabin.py`
- Delete: `.streamlit/config.toml`
- Modify: `requirements.txt`
- Modify: `scripts/start_control_cabin.ps1`

- [x] Delete Streamlit Python entrypoints and local Streamlit config.
- [x] Remove `streamlit>=1.36.0` from `requirements.txt`.
- [x] Rewrite `scripts/start_control_cabin.ps1` to build React and start FastAPI on port 8000.
- [x] Run `rg -n "streamlit|Streamlit" requirements.txt scripts app .streamlit` and confirm no runtime Streamlit path remains.

### Task 2: Move Email Sending Behind FastAPI

**Files:**
- Modify: `api/server.py`
- Modify: `core/persistence.py`
- Modify: `tests/test_api_server.py`

- [x] Add `EmailReportRequest` with recipient, subject, request id, and optional markdown body.
- [x] Add `POST /emails/report` that loads a saved report when only `request_id` is provided, calls `send_report_email`, and records the delivery result in SQLite.
- [x] Add `email_deliveries` persistence methods for auditability.
- [x] Add API tests for sending saved reports and rejecting missing report content.

### Task 3: Add React Email Workflow

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/pages/RunDetailPage.tsx`
- Modify: `frontend/src/components/ReportPreview.tsx`
- Modify: `frontend/src/styles/app.css`
- Modify: relevant frontend tests

- [x] Add typed API client method for `POST /emails/report`.
- [x] Add a report email panel on the run detail page with recipient, subject, and delivery status.
- [x] Keep report preview readable and Chinese HR-facing.
- [x] Run Vitest and Vite build.

### Task 4: Sync Documentation And Verify

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_PLAN.md`
- Modify: `docs/architecture_diagrams.md`
- Modify: `docs/data_schema.md`
- Modify: `DESIGN-react-control-cabin.md`

- [x] Rewrite current-status and run commands around React + FastAPI only.
- [x] Remove claims that Streamlit remains as a legacy/fallback control cabin.
- [x] Run backend pytest, frontend tests, frontend build.
- [x] Confirm `.env` is not staged.
- [x] Commit all completed changes.
