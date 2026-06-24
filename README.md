# Resume Pilot

Resume Pilot 是一个基于 LangGraph 的 Supervisor-centered 多 Agent 招聘评估系统。它把简历解析、岗位理解、证据化评分、风险复核、报告生成和人工复核串成一条可追踪、可回放、可持续验证的招聘评估流程。

项目定位不是替代 HR 做最终录用决策，而是构建一个可治理的招聘评估控制舱：每个评分要有证据，每个专家 Agent 要留下结构化输出和 trace，高风险结果要进入人工复核。

## 核心能力

- **中心化 Supervisor + LangGraph**：Supervisor 负责任务拆解、状态路由和复核路由，保留 Hub-and-Spoke 架构。
- **动态路由**：Schema 校验失败、证据缺口、Critic 冲突、风险复核结果都会影响后续节点，而不是固定串行 demo。
- **专家 Agent 分工**：Candidate Analyst、Job Analyst、Memory、Evidence Auditor、Critic、Consensus、Reporting 等 Agent 输出有边界、有契约、可审计。
- **本地大模型接入**：通过统一 model gateway 支持 OpenAI-compatible API 和 Ollama，本地默认推荐 `qwen3:1.7b`。
- **文档解析链路**：文本型 PDF 使用 PyMuPDF；图片型 PDF 可按配置走 OCR 或 Vision LLM fallback。
- **生产化数据层**：本地开发默认 SQLite，部署环境可切 PostgreSQL；长任务可接 Redis/RQ。
- **Harness 工程体系**：包含 batch runner、trace/replay、报告质量评估、LLM 抽取评估、benchmark 和回归测试。
- **React Web 控制舱**：支持批量评估、候选人记录、复核队列、运行详情、报告预览和记录删除。

## 项目结构

```text
api/          FastAPI 服务和 REST API
core/         Schema、解析、LLM gateway、持久化、风险模型和 Agent 契约
graph/        LangGraph 工作流和 Supervisor 路由
nodes/        工作流节点、专家 Agent 和规则节点
harness/      批量运行、trace/replay、benchmark 和评估工具
frontend/     React + Vite 控制舱
scripts/      启动、benchmark、LLM eval、模型训练脚本
tests/        后端回归测试
docs/         架构、部署、生产化和评估文档
workers/      Redis/RQ 异步任务 worker
```

## 工作流

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

关键实现位置：

- `graph/workflow.py`：LangGraph 节点编排。
- `graph/routing.py`：Supervisor-centered 动态路由。
- `nodes/parallel_specialists.py`：候选人、岗位、历史记忆三个专家并行执行。
- `core/agent_contracts.py`：Agent 输出契约和 token usage 记录。
- `core/model_gateway.py`：Ollama / OpenAI-compatible 模型网关。
- `core/persistence.py`：SQLite 本地持久化。
- `core/sqlalchemy_store.py`：SQLAlchemy / PostgreSQL 持久化。
- `harness/`：持续验证、回放、评估和 benchmark。
- `frontend/src/`：Web 控制舱。

更多说明：

- `docs/multi_agent_architecture.md`
- `docs/architecture_diagrams.md`
- `docs/production_readiness.md`
- `docs/deployment.md`
- `docs/benchmark_usage.md`

## 快速启动

### 1. 安装后端依赖

```powershell
python -m pip install -r requirements.txt
```

如需启用本地 OCR fallback：

```powershell
python -m pip install -r requirements-ocr.txt
```

### 2. 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 3. 配置环境变量

```powershell
Copy-Item .env.example .env
```

本地 Ollama + Qwen 示例：

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

本地开发不配置 `HR_DATABASE_URL` 时使用 SQLite。部署 PostgreSQL 时可配置：

```text
HR_DATABASE_URL=postgresql+psycopg://agentic_hr:agentic_hr_password@localhost:5432/agentic_hr
```

### 4. 启动控制舱

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```

打开前端：

```text
http://127.0.0.1:5173
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## CLI 使用

运行内置样例：

```powershell
python main.py
```

评估本地 PDF 简历：

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "Backend engineer with Python, FastAPI, PostgreSQL and Redis experience."
```

批量评估多个本地 PDF：

```powershell
python main.py --resume C:\path\to\candidate-a.pdf --resume C:\path\to\candidate-b.pdf --jd "AI engineer with Python and ML project experience."
```

关闭 LLM 报告增强，便于确定性批量回归：

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "AI engineer with Python and ML project experience." --disable-llm-report-enhancement
```

## API 示例

运行一次文本评估：

```powershell
curl -X POST http://127.0.0.1:8000/evaluations `
  -H "Content-Type: application/json" `
  -d "{\"request_id\":\"api-demo-001\",\"resume_text\":\"Candidate Alice. Python FastAPI Redis project.\",\"jd_text\":\"Backend engineer requires Python, FastAPI and Redis.\",\"risk_model_path\":\"models/review_risk_model.json\"}"
```

查询结果：

```powershell
curl http://127.0.0.1:8000/runs/api-demo-001
curl "http://127.0.0.1:8000/runs?status=pending&limit=20&offset=0"
curl "http://127.0.0.1:8000/batches?limit=20&offset=0"
```

删除本地评估记录：

```powershell
curl -X DELETE http://127.0.0.1:8000/runs/api-demo-001
curl -X DELETE http://127.0.0.1:8000/runs
```

## Harness 与验证

后端测试：

```powershell
python -m pytest -q
```

前端测试和构建：

```powershell
cd frontend
npm test -- --run
npm run build
```

Benchmark：

```powershell
python scripts\run_benchmark.py --count 5 --output data\test_outputs\benchmark_smoke.json
```

LLM 抽取评估：

```powershell
python scripts\run_llm_eval.py --cases data\datasets\extraction_eval_cases.jsonl --output data\test_outputs\llm_extraction_eval_report.md
```

## Docker 部署

Compose 栈包含 FastAPI、PostgreSQL、Redis 和 RQ worker：

```powershell
docker compose --env-file .env.production.example up --build
```

如果 Docker 内服务需要访问宿主机 Ollama：

```text
HR_LLM_BASE_URL=http://host.docker.internal:11434/v1
```

## 仓库清理策略

以下内容不会提交到 GitHub：

- `.env` 和本地密钥
- SQLite 数据库
- 上传过的简历和 PDF
- OCR / 模型缓存
- 生成的报告、回放文件和测试输出
- `node_modules` 和前端构建产物
- Python cache 目录

`data/datasets/` 下保留的是合成或脱敏样例数据，用于测试和 harness 示例。

## License

当前尚未选择开源许可证。正式公开使用前建议补充 `LICENSE` 文件。
