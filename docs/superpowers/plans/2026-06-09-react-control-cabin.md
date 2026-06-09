# React Control Cabin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-oriented React control cabin while extending FastAPI and SQLite so the frontend no longer depends on Streamlit or direct workflow calls.

**Architecture:** React + TypeScript + Vite lives in `frontend/` and calls only FastAPI. FastAPI continues to invoke LangGraph workflows and persists normalized run, trace, report, review, candidate, job, batch, and email-delivery data through `SQLiteRunStore`. React is the only control cabin entry.

**Tech Stack:** React, TypeScript, Vite, Vitest, FastAPI, Pydantic, SQLite, pytest.

---

### Task 1: Normalize SQLite Persistence

**Files:**
- Modify: `core/persistence.py`
- Test: `tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

Add tests that save one workflow result and assert `get_trace`, `get_report`, `list_reviews`, and normalized candidate/job data are available.

- [ ] **Step 2: Run tests to verify failure**

Run: `D:\python\python.exe -m pytest tests\test_persistence.py -q`

Expected: FAIL because the new store methods do not exist yet.

- [ ] **Step 3: Implement tables and read methods**

Add tables: `candidates`, `jobs`, `traces`, `reviews`, `reports`. Keep `workflow_runs.payload_json` for replay compatibility.

- [ ] **Step 4: Run tests to verify pass**

Run: `D:\python\python.exe -m pytest tests\test_persistence.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add core\persistence.py tests\test_persistence.py
git commit -m "Normalize SQLite workflow persistence"
```

### Task 2: Add Review, Report, and Trace API Endpoints

**Files:**
- Modify: `api/server.py`
- Test: `tests/test_api_server.py`

- [ ] **Step 1: Write failing API tests**

Add tests for:

- `GET /traces/{request_id}`
- `GET /reports/{request_id}`
- `GET /reviews`
- `POST /reviews/{request_id}`

- [ ] **Step 2: Run tests to verify failure**

Run: `D:\python\python.exe -m pytest tests\test_api_server.py -q`

Expected: FAIL with 404 or missing method.

- [ ] **Step 3: Implement endpoints**

Use `SQLiteRunStore` methods only. Do not call workflow code from review/report/trace endpoints.

- [ ] **Step 4: Run tests to verify pass**

Run: `D:\python\python.exe -m pytest tests\test_api_server.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add api\server.py tests\test_api_server.py
git commit -m "Add run detail API endpoints"
```

### Task 3: Scaffold React Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/app.css`
- Test: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing frontend test**

Create a Vitest test that mocks `fetch` and checks `listRuns()` calls `/runs`.

- [ ] **Step 2: Run test to verify failure**

Run: `cd frontend; npm install; npm test -- --run`

Expected: FAIL because API client is not implemented.

- [ ] **Step 3: Implement React scaffold and API client**

Create minimal app shell, dashboard, run detail placeholder, and API client methods.

- [ ] **Step 4: Run frontend tests**

Run: `cd frontend; npm test -- --run`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend package-lock.json
git commit -m "Scaffold React control cabin"
```

### Task 4: Connect React Dashboard to FastAPI

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/components/MetricTile.tsx`
- Create: `frontend/src/components/StatusChip.tsx`
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/RunDetailPage.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing rendering tests**

Test that recent runs and trace/report panels render with mocked API responses.

- [ ] **Step 2: Run test to verify failure**

Run: `cd frontend; npm test -- --run`

Expected: FAIL because pages are not implemented.

- [ ] **Step 3: Implement pages and components**

Use the design tokens from `DESIGN-react-control-cabin.md`. Keep the UI dense, operational, and table-first.

- [ ] **Step 4: Run frontend tests**

Run: `cd frontend; npm test -- --run`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend
git commit -m "Build React dashboard views"
```

### Task 5: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `Dockerfile` if needed
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update docs**

Document:

- FastAPI startup
- React dev server startup
- test commands
- React-only control cabin status

- [ ] **Step 2: Run backend tests**

Run: `D:\python\python.exe -m pytest -q`

Expected: PASS.

- [ ] **Step 3: Run frontend tests/build**

Run:

```powershell
cd frontend
npm test -- --run
npm run build
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add README.md .github\workflows\ci.yml Dockerfile frontend
git commit -m "Document React control cabin workflow"
```

## Self-Review

- Spec coverage: React frontend, FastAPI boundary, SQLite normalized schema, control cabin migration, and tests are covered.
- Placeholder scan: no implementation placeholder remains in this plan.
- Type consistency: API methods map to endpoints in `DESIGN-react-control-cabin.md`.
