# Resume Pilot Architecture Diagrams

这些图用于 README、答辩和面试讲解。当前项目口径统一为：

- 后端服务：FastAPI。
- 工作流编排：Supervisor-centered LangGraph。
- 生产主库：PostgreSQL，通过 `SQLAlchemyRunStore` 接入。
- 异步任务与运行状态：Redis + RQ worker。
- 本地 fallback：未配置 `HR_DATABASE_URL` 时才使用 SQLite。

## 1. System Context

```mermaid
flowchart LR
    User["HR / Interviewer"]
    React["React Web Console"]
    API["FastAPI Backend"]
    Workflow["LangGraph Workflow"]
    DB["PostgreSQL<br/>runs / traces / reports / reviews / batches / jobs"]
    Redis["Redis + RQ<br/>async jobs / runtime status"]
    LLM["Ollama or OpenAI-compatible LLM"]
    OCR["Optional OCR<br/>EasyOCR / PaddleOCR"]
    SMTP["Optional SMTP"]

    User --> React
    React --> API
    API --> Workflow
    API --> DB
    API --> Redis
    Redis --> Worker["RQ Worker"]
    Worker --> Workflow
    Workflow --> DB
    Workflow -.optional.-> LLM
    Workflow -.optional.-> OCR
    API -.optional.-> SMTP
```

## 2. Supervisor-Centered Workflow

```mermaid
flowchart TD
    Start["Request"]
    Supervisor["Supervisor Agent<br/>task decomposition + route decision"]
    Parser["Document Parser"]
    Resume["Resume Extractor"]
    JD["JD Extractor"]
    Validator["Schema Validator"]
    Specialists["Parallel Specialists"]
    Candidate["Candidate Analyst"]
    Job["Job Analyst"]
    Memory["Memory Agent"]
    Rubric["Rubric Selector"]
    Matcher["Matcher"]
    Risk["Risk Evaluator"]
    Evidence["Evidence Auditor"]
    Critic["Critic Agent"]
    Consensus["Consensus Agent"]
    Report["Report Writer"]
    ReviewRouter["Supervisor Review Router"]
    Human["Human Review"]
    Done["Persisted Result"]

    Start --> Supervisor
    Supervisor --> Parser
    Parser --> Resume
    Resume --> JD
    JD --> Validator
    Validator --> Specialists
    Specialists --> Candidate
    Specialists --> Job
    Specialists --> Memory
    Candidate --> Rubric
    Job --> Rubric
    Memory --> Rubric
    Rubric --> Matcher
    Matcher --> Risk
    Risk --> Evidence
    Evidence --> Critic
    Critic --> Consensus
    Consensus --> Report
    Report --> ReviewRouter
    ReviewRouter --> Human
    ReviewRouter --> Done
    Human --> Done
```

## 3. Parallel Specialist Fan-Out/Fan-In

```mermaid
flowchart LR
    State["WorkflowState"]
    Fanout["parallel_specialists_node"]
    Candidate["Candidate Analyst<br/>strengths / gaps / candidate evidence"]
    Job["Job Analyst<br/>job priorities / evaluation dimensions"]
    Memory["Memory Agent<br/>similar review feedback"]
    Merge["merge agent_results<br/>record trace + token usage"]

    State --> Fanout
    Fanout --> Candidate
    Fanout --> Job
    Fanout --> Memory
    Candidate --> Merge
    Job --> Merge
    Memory --> Merge
```

## 4. Data And Runtime Store

```mermaid
flowchart TB
    API["FastAPI"]
    StoreFactory["create_run_store()"]
    Postgres["SQLAlchemyRunStore<br/>PostgreSQL production store"]
    SQLite["SQLiteRunStore<br/>local fallback only"]
    Redis["Redis<br/>queue + runtime probe"]

    API --> StoreFactory
    StoreFactory -->|"HR_DATABASE_URL set"| Postgres
    StoreFactory -->|"HR_DATABASE_URL empty"| SQLite
    API --> Redis
```

## 5. Persistence Tables

PostgreSQL and SQLite share the same logical run-store responsibilities.

```mermaid
erDiagram
    workflow_runs ||--o| candidates : has
    workflow_runs ||--o| jobs : has
    workflow_runs ||--o{ traces : records
    workflow_runs ||--o| reports : emits
    workflow_runs ||--o{ agent_runs : records
    workflow_runs ||--o{ supervisor_decisions : records
    workflow_runs ||--o{ reviews : receives
    batches ||--o{ batch_runs : contains
    evaluation_jobs ||--o{ workflow_runs : creates
```

## 6. Document Parsing Strategy

```mermaid
flowchart TD
    PDF["Resume PDF"]
    PyMuPDF["PyMuPDF text extraction"]
    Quality["Text quality check"]
    OCR["OCR fallback"]
    Vision["Vision LLM fallback"]
    Clean["clean_extracted_text"]
    ResumeExtractor["Resume Extractor"]

    PDF --> PyMuPDF
    PyMuPDF --> Quality
    Quality -->|"enough text"| Clean
    Quality -->|"image-like PDF"| OCR
    Quality -->|"configured vision_first"| Vision
    OCR --> Clean
    Vision --> Clean
    Clean --> ResumeExtractor
```

## 7. Harness Verification Loop

```mermaid
flowchart LR
    Cases["test cases / datasets"]
    Runner["batch runner"]
    Trace["trace capture"]
    Replay["replay"]
    Eval["report + extraction evaluation"]
    Benchmark["benchmark"]
    Tests["pytest + vitest + build"]

    Cases --> Runner
    Runner --> Trace
    Trace --> Replay
    Replay --> Eval
    Eval --> Benchmark
    Benchmark --> Tests
```

## 8. Deployment Shape

```mermaid
flowchart LR
    Browser["Browser"]
    API["FastAPI container"]
    Worker["RQ worker container"]
    DB["PostgreSQL"]
    Redis["Redis"]
    Ollama["Host Ollama<br/>optional"]

    Browser --> API
    API --> DB
    API --> Redis
    Redis --> Worker
    Worker --> DB
    Worker --> Ollama
    API --> Ollama
```
