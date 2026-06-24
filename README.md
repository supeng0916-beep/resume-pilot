# Resume Pilot

Resume Pilot 是一个面向招聘评估场景的 Supervisor-centered 多 Agent 系统，基于 LangGraph、FastAPI、PostgreSQL、Redis/RQ 和 React 构建。

系统用于辅助 HR 和面试官完成结构化简历筛选、岗位匹配分析、证据化评分、风险复核和批量评估，不用于自动做出录用或淘汰决策。

## 核心能力

- **中心化 Supervisor 工作流**：由 Supervisor 统一进行任务拆解、状态路由、异常分支和复核路由。
- **专家 Agent 分工**：Candidate Analyst、Job Analyst、Memory Agent、Evidence Auditor、Critic Agent、Consensus Agent、Reporting Agent 各自处理边界清晰的分析任务。
- **证据化评估**：评分与简历证据、岗位要求、文档解析质量、历史人工反馈和风险因素关联。
- **生产化数据层**：部署环境使用 PostgreSQL + SQLAlchemy；Redis/RQ 支持异步任务；SQLite 仅作为本地免配置 fallback。
- **本地大模型接入**：通过统一 Model Gateway 支持 Ollama 和 OpenAI-compatible API，适配本地模型推理。
- **文档解析链路**：文本型 PDF 使用 PyMuPDF，图片型 PDF 可配置 OCR 或 Vision LLM fallback。
- **批量上传去重**：上传简历按 SHA-256 计算内容哈希，同一批次内重复文件会被跳过，避免重复解析和重复消耗 OCR/LLM token。
- **Harness 验证体系**：包含 batch runner、trace/replay、benchmark、LLM 抽取评估、报告质量评估和回归测试。
- **React 控制舱**：支持批量评估、候选人库、人工复核队列、运行详情、报告预览和记录删除。

## 系统架构

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

## 目录结构

```text
api/          FastAPI 服务与 REST API
core/         Schema、解析器、模型网关、数据存储、风险模型和 Agent 契约
graph/        LangGraph 工作流与动态路由
nodes/        工作流节点、专家 Agent 和规则节点
harness/      批量运行、回放、benchmark 和评估工具
frontend/     React + Vite 控制舱
scripts/      启动、benchmark、LLM eval 和模型训练脚本
tests/        后端回归测试
docs/         架构、部署、数据和生产化文档
workers/      Redis/RQ 异步任务 worker
```

更多文档：

- `docs/multi_agent_architecture.md`
- `docs/architecture_diagrams.md`
- `docs/production_readiness.md`
- `docs/deployment.md`
- `docs/benchmark_usage.md`

## 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 和 Redis，用于部署环境
- 可选：Ollama，用于本地大模型推理
- 可选：OCR 依赖，用于图片型 PDF 解析

## 快速启动

安装后端依赖：

```powershell
python -m pip install -r requirements.txt
```

如需启用本地 OCR fallback：

```powershell
python -m pip install -r requirements-ocr.txt
```

安装前端依赖：

```powershell
cd frontend
npm install
cd ..
```

创建本地环境变量文件：

```powershell
Copy-Item .env.example .env
```

启动 FastAPI 后端和 React 控制舱：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```

打开控制舱：

```text
http://127.0.0.1:5173
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## 配置

### PostgreSQL

部署环境建议配置 `HR_DATABASE_URL`：

```text
HR_DATABASE_URL=postgresql+psycopg://agentic_hr:agentic_hr_password@localhost:5432/agentic_hr
```

未配置 `HR_DATABASE_URL` 时，系统会使用本地 SQLite 作为单机开发 fallback。

### Ollama

本地 Ollama 示例配置：

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

配置 `HR_REDIS_URL` 后会启用 Redis 队列：

```text
HR_REDIS_URL=redis://localhost:6379/0
```

未配置 Redis 时，本地开发会 fallback 到 FastAPI background tasks。

## CLI 使用

运行内置样例：

```powershell
python main.py
```

评估一份本地 PDF：

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "招聘 Python 后端工程师，要求 FastAPI、PostgreSQL、Redis 项目经验。"
```

批量评估多份本地 PDF：

```powershell
python main.py --resume C:\path\to\candidate-a.pdf --resume C:\path\to\candidate-b.pdf --jd "招聘 AI 工程师，要求 Python、机器学习和项目经验。"
```

关闭 LLM 报告增强，便于确定性回归测试：

```powershell
python main.py --resume C:\path\to\candidate.pdf --jd "招聘 AI 工程师，要求 Python 和机器学习项目经验。" --disable-llm-report-enhancement
```

## API 示例

运行一次文本评估：

```powershell
curl -X POST http://127.0.0.1:8000/evaluations `
  -H "Content-Type: application/json" `
  -d "{\"request_id\":\"api-demo-001\",\"resume_text\":\"候选人 Alice，做过 Python FastAPI Redis 项目。\",\"jd_text\":\"招聘后端工程师，要求 Python、FastAPI、Redis。\",\"risk_model_path\":\"models/review_risk_model.json\"}"
```

查询结果：

```powershell
curl http://127.0.0.1:8000/runs/api-demo-001
curl "http://127.0.0.1:8000/runs?status=pending&limit=20&offset=0"
curl "http://127.0.0.1:8000/batches?limit=20&offset=0"
```

删除评估记录：

```powershell
curl -X DELETE http://127.0.0.1:8000/runs/api-demo-001
curl -X DELETE http://127.0.0.1:8000/runs
```

## 批量上传去重

`/batch-evaluations/uploads` 会对每个上传文件计算 SHA-256。若同一批次内出现内容完全相同的简历，只保留第一份进入解析和评估，重复文件会在响应中返回：

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

这可以避免同一批次内重复解析、重复评分和重复消耗 OCR/LLM token。

## 测试

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

Benchmark smoke：

```powershell
python scripts\run_benchmark.py --count 5 --output data\test_outputs\benchmark_smoke.json
```

LLM 抽取评估：

```powershell
python scripts\run_llm_eval.py --cases data\datasets\extraction_eval_cases.jsonl --output data\test_outputs\llm_extraction_eval_report.md
```

## Docker 部署

Docker Compose 包含 FastAPI、PostgreSQL、Redis 和 RQ worker：

```powershell
docker compose --env-file .env.production.example up --build
```

如果 Docker 内服务需要访问宿主机 Ollama：

```text
HR_LLM_BASE_URL=http://host.docker.internal:11434/v1
```

## 仓库边界

以下内容不会提交到版本库：

- `.env` 和本地密钥
- 本地 SQLite fallback 数据库
- 上传过的简历和 PDF
- OCR / 模型缓存
- 生成的报告、replay case 和测试输出
- `node_modules` 和前端构建产物
- Python cache 目录

`data/datasets/` 下保留的是合成或脱敏样例数据，用于测试和 harness 示例。

## 隐私与安全

Resume Pilot 是招聘评估辅助工具，不应被包装为自动录用决策系统。真实简历应在合规、脱敏和权限控制前提下使用，避免把原始个人信息提交到公开仓库或测试数据集中。

## License

当前尚未选择开源许可证。正式开源分发前请补充 `LICENSE` 文件。
