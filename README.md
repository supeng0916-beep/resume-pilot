# Agentic HR

基于 LangGraph 的多 Agent 招聘评估系统，采用 Hub-and-Spoke 工作流、FastAPI 服务层、SQLite 持久化和 React 控制舱。项目定位是“可演示、可解释、可继续落地”的工程原型，不是直接替代人工招聘决策的生产系统。

## Current Status

当前版本已经完成核心闭环：PDF/文本简历解析、简历与 JD 抽取、校验、分轨匹配评分、人工复核风险预测、报告生成、trace/replay/batch harness、SQLite 持久化、FastAPI API、React 控制舱、邮件发送入口、Docker 和 CI。

仍建议作为后续生产化增强的部分：

- 多用户部署时将 SQLite 替换为 PostgreSQL。
- 增加登录鉴权、角色权限和审计策略。
- 对长耗时 OCR/LLM 批处理引入 Redis + 异步任务队列。
- 用真实脱敏简历补充人工标注数据。
- 接入 hosted tracing、监控和告警。

## Quick Start

安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

如需启用本地 OCR fallback，再安装可选 OCR 依赖；默认演示链路不需要安装这些重型包：

```powershell
python -m pip install -r requirements-ocr.txt
```

安装前端依赖：

```powershell
cd frontend
npm install
cd ..
```

一键启动 React 控制舱和 FastAPI：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```

打开控制舱：

```text
http://127.0.0.1:5173
```

停止控制舱：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_control_cabin.ps1
```

## CLI Usage

运行内置示例：

```powershell
D:\python\python.exe main.py
```

指定简历 PDF：

```powershell
D:\python\python.exe main.py --resume data\examples\candidate.pdf
```

指定 JD：

```powershell
D:\python\python.exe main.py --resume data\examples\candidate.pdf --jd "招聘 Python 后端工程师，要求熟悉 FastAPI、PostgreSQL、Redis。"
```

批量评估并保存 Markdown 报告：

```powershell
D:\python\python.exe main.py --resume data\examples\candidate-a.pdf --resume data\examples\candidate-b.pdf --jd "校招 AI 工程师，要求 Python、机器学习和项目经历。" --output data\test_outputs\batch_report.md
```

LLM 开启时如需更快批处理，可关闭逐候选人报告增强：

```powershell
D:\python\python.exe main.py --resume data\examples\candidate-a.pdf --resume data\examples\candidate-b.pdf --jd "校招 AI 工程师，要求 Python、机器学习和项目经历。" --disable-llm-report-enhancement
```

## FastAPI Service

单独启动后端：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_api.ps1
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

运行一次评估：

```powershell
curl -X POST http://127.0.0.1:8000/evaluations `
  -H "Content-Type: application/json" `
  -d "{\"request_id\":\"api-demo-001\",\"resume_text\":\"Candidate Alice. Python FastAPI Redis project.\",\"jd_text\":\"Backend engineer requires Python, FastAPI and Redis.\",\"risk_model_path\":\"models/review_risk_model.json\"}"
```

查询持久化结果：

```powershell
curl http://127.0.0.1:8000/runs/api-demo-001
curl "http://127.0.0.1:8000/runs?status=pending&limit=20&offset=0"
curl "http://127.0.0.1:8000/batches?limit=20&offset=0"
```

## React Control Cabin

React 是唯一控制舱前端，位于 `frontend/`。它只通过 HTTP 调用 FastAPI，不直接读取本地文件、不调用 Python workflow、不写 SQLite。

已支持：

- 后端健康检查与 SQLite 状态展示。
- 文本简历批量评估。
- PDF/文本简历上传评估。
- 最近批次、候选人记录、运行详情。
- trace 时间线与 Markdown 报告预览。
- 人工复核提交。
- 候选人报告邮件发送。

开发模式：

```powershell
cd frontend
npm run dev
```

生产构建：

```powershell
cd frontend
npm run build
```

FastAPI 会在 `frontend/dist` 存在时托管构建后的 React 应用。

## Email Delivery

邮件发送通过 FastAPI 的 `POST /emails/report` 完成，React 控制舱在候选人详情页调用该接口。SMTP 配置来自环境变量或本地 `.env`，不要提交 `.env`。

```powershell
$env:HR_SMTP_HOST="smtp.example.com"
$env:HR_SMTP_PORT="465"
$env:HR_SMTP_USERNAME="your-email@example.com"
$env:HR_SMTP_PASSWORD="your-smtp-app-password"
$env:HR_SMTP_FROM="your-email@example.com"
$env:HR_SMTP_USE_SSL="true"
```

如果 SMTP 未配置，接口会返回“未发送”的结果并记录到 SQLite `email_deliveries` 表，报告仍可在控制舱预览。

## Dataset And ML

生成合成结构化数据：

```powershell
D:\python\python.exe scripts\generate_dataset.py --output-dir data\datasets --count 500 --seed 42
```

数据文件：

- `data/datasets/synthetic_candidates.jsonl`
- `data/datasets/synthetic_jobs.jsonl`
- `data/datasets/synthetic_labels.jsonl`
- `data/datasets/example_redacted_candidates.jsonl`
- `data/datasets/extraction_eval_cases.jsonl`

训练人工复核风险模型：

```powershell
D:\python\python.exe scripts\train_review_risk_model.py --dataset-dir data\datasets --output models\review_risk_model.json --model-card models\model_card_review_risk.md
```

当前提交包含基于 500 条合成数据训练的 `models/review_risk_model.json` 和模型卡 `models/model_card_review_risk.md`。该模型预测“是否需要人工复核”，不是预测录用结果。

人工标注建议参见 `docs/annotation_guideline.md`。数据结构参见 `docs/data_schema.md`。ML 流程参见 `docs/ml_pipeline.md`。

## LLM Enhancement

LLM 能力默认可选。创建本地 `.env` 并保持不入 git：

```powershell
HR_LLM_ENABLED=true
HR_LLM_API_KEY=your-api-key
HR_LLM_MODEL=your-model-name
HR_LLM_BASE_URL=https://api.openai.com/v1/chat/completions
HR_LLM_TIMEOUT_SECONDS=30
HR_LLM_IGNORE_PROXY=true
HR_LLM_PDF_MAX_PAGES=3
HR_IMAGE_PDF_PARSE_STRATEGY=vision_first
HR_ENABLE_LOCAL_OCR=false
HR_OCR_TIMEOUT_SECONDS=12
```

如果 LLM 关闭、配置缺失或请求失败，系统会回退到规则抽取和确定性报告。图片型 PDF 默认使用 Vision LLM 优先策略，必要时可开启本地 OCR fallback。

## Harness And Evaluation

运行全量测试：

```powershell
D:\python\python.exe -m pytest -q
```

运行前端测试和构建：

```powershell
cd frontend
npm test -- --run
npm run build
```

运行控制舱相关后端测试：

```powershell
D:\python\python.exe -m pytest tests\test_control_cabin.py tests\test_batch_runner.py tests\test_api_server.py -q
```

运行 LLM 抽取评估 harness：

```powershell
D:\python\python.exe scripts\run_llm_eval.py --cases data\datasets\extraction_eval_cases.jsonl --output data\test_outputs\llm_extraction_eval_report.md
```

## Architecture

架构图参见 `docs/architecture_diagrams.md`，覆盖：

- 系统上下文。
- Hub-and-Spoke agent workflow。
- Agent、Node、Tool、Harness 边界。
- React/FastAPI 前后端分层。
- SQLite 持久化模型。
- 数据与 ML 闭环。
- Redis 异步队列的生产演进方案。

## Tool Boundary

可复用工具适配器位于 `tools/hr_tools.py`：

- `parse_resume_pdf`
- `extract_resume_profile`
- `extract_jd_profile`
- `run_batch_evaluation`
- `save_batch_report`
- `send_report_email`
