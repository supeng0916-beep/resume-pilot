# Architecture Diagrams

这些图用于 README、答辩和面试讲解。图中分为两类：

- 已实现：当前仓库已经具备的能力。
- 生产化演进：面向真实部署的扩展设计，例如 Redis、异步队列、PostgreSQL 和鉴权。

## 1. 系统上下文

```mermaid
flowchart LR
    HR["招聘官 / 面试官"]
    React["React 招聘评估工作台"]
    API["FastAPI 服务层"]
    Workflow["LangGraph Agentic Workflow"]
    Store["SQLite 持久化<br/>run / trace / report / review / batch"]
    LLM["可选 LLM 服务<br/>结构化抽取 / 图片 PDF / 报告增强"]
    OCR["可选本地 OCR<br/>EasyOCR / PaddleOCR"]
    SMTP["可选 SMTP 邮件发送"]

    HR --> React
    React --> API
    API --> Workflow
    Workflow --> Store
    Workflow -.可选.-> LLM
    Workflow -.可选.-> OCR
    React -.邮件入口.-> API
    API -.可选.-> SMTP
```

## 2. Hub-and-Spoke Agent 工作流

```mermaid
flowchart TD
    Start(["Start"])
    Hub["Orchestrator / Hub<br/>状态路由、错误处理、复核决策"]
    Parser["Document Parser Node<br/>PDF 文本解析 / 质量评分 / OCR 标记"]
    Resume["Resume Extraction Agent<br/>规则抽取 + 可选 LLM 抽取"]
    JD["JD Extraction Agent<br/>岗位要求结构化"]
    Validator["Validation Node<br/>Pydantic Schema 校验"]
    Retry{"校验是否通过？"}
    Rubric["Rubric Selector<br/>校招 / 社招 / 实习分轨"]
    Match["Matching Node<br/>技能、年限、学历、薪资、证据评分"]
    Risk["Risk Evaluator<br/>人工复核风险预测"]
    Report["Report Agent<br/>生成招聘评估报告"]
    Review["Human Review Node<br/>人工审批与反馈沉淀"]
    End(["End"])

    Start --> Hub
    Hub --> Parser --> Resume --> JD --> Validator --> Retry
    Retry -- 否，未超过重试上限 --> Resume
    Retry -- 是 --> Rubric --> Match --> Risk --> Report --> Review --> End
    Review -.反馈记忆.-> Hub
```

## 3. Agent、Node、Tool、Harness 边界

```mermaid
flowchart TB
    subgraph Agentic["Agentic Workflow 层"]
        Hub["Orchestrator Agent"]
        Extract["Extraction Agent"]
        ReportAgent["Report Agent"]
    end

    subgraph Nodes["确定性 Node / Skill 层"]
        Parser["PDF Parser"]
        Validator["Pydantic Validator"]
        Matcher["Matcher"]
        Risk["Risk Model"]
        Rubric["Rubric Selector"]
    end

    subgraph Tools["Tool 层"]
        PDF["PDF / OCR Tool"]
        LLMTool["LLM Tool"]
        Email["Email Tool"]
        StoreTool["Persistence Tool"]
    end

    subgraph Harness["Harness 层"]
        Batch["Batch Runner"]
        Trace["Trace"]
        Replay["Replay"]
        Eval["Eval / Quality Check"]
        LLMEval["LLM Extraction Eval"]
    end

    Hub --> Extract
    Hub --> ReportAgent
    Extract --> Validator
    Extract --> Parser
    Parser --> PDF
    Extract -.可选.-> LLMTool
    ReportAgent -.可选.-> LLMTool
    ReportAgent --> Email
    Nodes --> StoreTool
    Harness --> Agentic
    Harness --> Nodes
```

## 4. 前后端分层

```mermaid
flowchart LR
    subgraph Frontend["Frontend: React + TypeScript + Vite"]
        Dashboard["招聘评估工作台"]
        BatchPage["创建评估批次"]
        ReviewPage["人工复核队列"]
        DetailPage["候选人详情 / 流程追踪 / 报告预览"]
    end

    subgraph Backend["Backend: FastAPI"]
        EvalAPI["POST /evaluations"]
        BatchAPI["POST /batch-evaluations"]
        UploadAPI["POST /batch-evaluations/uploads"]
        RunAPI["GET /runs /runs/{id}"]
        TraceAPI["GET /traces/{id}"]
        ReportAPI["GET /reports/{id}"]
        ReviewAPI["GET/POST /reviews"]
        BatchReadAPI["GET /batches /batches/{id}"]
    end

    subgraph Core["Core Workflow"]
        Runner["Harness Runner"]
        Workflow["LangGraph Workflow"]
        Persistence["SQLiteRunStore"]
    end

    Dashboard --> RunAPI
    Dashboard --> BatchReadAPI
    BatchPage --> BatchAPI
    BatchPage --> UploadAPI
    ReviewPage --> ReviewAPI
    DetailPage --> RunAPI
    DetailPage --> TraceAPI
    DetailPage --> ReportAPI
    EvalAPI --> Runner
    BatchAPI --> Runner
    UploadAPI --> Runner
    Runner --> Workflow
    Runner --> Persistence
```

## 5. 数据与 ML 闭环

```mermaid
flowchart TD
    Synthetic["合成结构化数据<br/>500 条候选人 / JD / 标签"]
    Annotation["人工标注规范<br/>annotations.jsonl，默认不提交"]
    Train["训练脚本<br/>train_review_risk_model.py"]
    Model["review_risk_model.json<br/>人工复核风险模型"]
    Workflow["Risk Evaluator Node"]
    Review["人工复核结果"]
    Memory["反馈记忆<br/>review_feedback.json，默认不提交"]
    Docs["Model Card / Data Schema"]

    Synthetic --> Train
    Annotation -.补充真实脱敏样本.-> Train
    Train --> Model
    Model --> Workflow
    Workflow --> Review
    Review --> Memory
    Synthetic --> Docs
    Model --> Docs
```

## 6. SQLite 持久化表关系

```mermaid
erDiagram
    workflow_runs ||--o| candidates : has
    workflow_runs ||--o| jobs : has
    workflow_runs ||--o{ traces : records
    workflow_runs ||--o| reports : produces
    workflow_runs ||--o{ reviews : receives
    workflow_runs ||--o{ email_deliveries : sends
    batches ||--o{ batch_runs : contains
    workflow_runs ||--o{ batch_runs : belongs_to

    workflow_runs {
        string request_id PK
        string current_step
        float match_score
        float risk_score
        string human_review_status
        string payload_json
        string trace_json
    }

    candidates {
        string request_id PK
        string name
        string education
        int years_experience
        string candidate_track
        string profile_json
    }

    jobs {
        string request_id PK
        string title
        int required_years
        string recruitment_track
        string required_skills_json
    }

    traces {
        int id PK
        string request_id FK
        string node
        string timestamp
        string output_summary
        string extra_json
    }

    reports {
        string request_id PK
        string markdown
        string quality_json
    }

    reviews {
        int id PK
        string request_id FK
        string decision
        string feedback
        string reviewer
    }

    email_deliveries {
        int id PK
        string request_id FK
        string recipient
        string subject
        bool sent
        string message
    }

    batches {
        string request_id PK
        int candidate_count
        string top_candidate_request_id
        string payload_json
    }

    batch_runs {
        string batch_request_id FK
        string request_id FK
        string candidate_id
        float rank_score
        int rank_index
    }
```

## 7. Harness 运行、评估与回放

```mermaid
flowchart LR
    Cases["测试样本 / 批量简历 / JD"]
    Runner["Scenario Harness<br/>runner / batch_runner"]
    Workflow["LangGraph Workflow"]
    Trace["Observability Harness<br/>节点 trace / 错误 / 耗时"]
    Replay["Replay Harness<br/>保存输入与节点输出"]
    Eval["Eval Harness<br/>报告质量 / 抽取准确率 / 回归检查"]
    Report["测试报告 / LLM eval report"]

    Cases --> Runner
    Runner --> Workflow
    Workflow --> Trace
    Workflow --> Replay
    Trace --> Eval
    Replay --> Eval
    Eval --> Report
```

## 8. 当前本地部署架构

```mermaid
flowchart TB
    User["用户浏览器"]
    ReactDev["React Dev Server<br/>127.0.0.1:5173"]
    FastAPI["FastAPI / Uvicorn<br/>127.0.0.1:8000"]
    Static["frontend/dist<br/>Docker 或生产静态托管"]
    SQLite["data/hr_runs.sqlite3"]
    Uploads["data/api_uploads<br/>默认不提交"]
    Env[".env<br/>本地密钥，默认不提交"]

    User --> ReactDev
    ReactDev --> FastAPI
    User -.Docker / build 后.-> FastAPI
    FastAPI --> Static
    FastAPI --> SQLite
    FastAPI --> Uploads
    FastAPI -.读取配置.-> Env
```

## 9. 生产化异步并发演进

当前版本为了演示稳定采用同步 API 调用。真实部署可演进为异步任务架构：

```mermaid
flowchart LR
    React["React 工作台"]
    API["FastAPI<br/>鉴权 / 创建任务 / 查询状态"]
    DB["PostgreSQL<br/>任务、运行、报告、复核最终状态"]
    Redis["Redis<br/>队列 Broker / 短期进度 / 幂等锁"]
    WorkerA["Worker A<br/>PDF / OCR"]
    WorkerB["Worker B<br/>LLM 抽取"]
    WorkerC["Worker C<br/>LangGraph 评分与报告"]
    LLM["LLM Provider"]
    OCR["OCR Provider"]

    React --> API
    API --> DB
    API --> Redis
    Redis --> WorkerA
    Redis --> WorkerB
    Redis --> WorkerC
    WorkerA --> OCR
    WorkerB --> LLM
    WorkerC --> LLM
    WorkerA --> DB
    WorkerB --> DB
    WorkerC --> DB
    React -.轮询 / WebSocket.-> API
```

面试表述要点：

- 当前没有强行把 Redis 放进 MVP，因为本地演示同步流程更稳定。
- 架构已经通过 `request_id`、批次表、trace 表和 review 表做好并发隔离。
- 长耗时任务如 OCR、Vision LLM、批量评估适合迁移到 Redis Queue + Worker。
- Redis 用作 broker、短期进度缓存和幂等锁；PostgreSQL 保存最终业务状态。

## 10. LLM 与工具调用路径

```mermaid
flowchart TD
    State["WorkflowState"]
    ParserDecision{"PDF 是否低质量<br/>或图片型？"}
    TextParser["PyMuPDF 文本解析"]
    VisionLLM["Vision LLM PDF 解析<br/>可选开关"]
    LocalOCR["Local OCR<br/>可选开关"]
    ExtractDecision{"是否启用 LLM 结构化抽取？"}
    RuleExtract["规则抽取兜底"]
    LLMExtract["LLM JSON 抽取<br/>Pydantic 校验"]
    ReportDecision{"是否启用 LLM 报告增强？"}
    RuleReport["确定性 Markdown 报告"]
    LLMReport["LLM 增强摘要与面试问题"]
    Validation["Schema 校验 / retry / graceful fallback"]

    State --> ParserDecision
    ParserDecision -- 文本型 PDF --> TextParser
    ParserDecision -- 图片型 / 低质量 --> VisionLLM
    ParserDecision -- 本地 OCR 开启 --> LocalOCR
    TextParser --> ExtractDecision
    VisionLLM --> ExtractDecision
    LocalOCR --> ExtractDecision
    ExtractDecision -- 否 --> RuleExtract
    ExtractDecision -- 是 --> LLMExtract --> Validation
    Validation -- 失败 --> RuleExtract
    RuleExtract --> ReportDecision
    Validation -- 通过 --> ReportDecision
    ReportDecision -- 否 --> RuleReport
    ReportDecision -- 是 --> LLMReport
    LLMReport -.失败兜底.-> RuleReport
```
