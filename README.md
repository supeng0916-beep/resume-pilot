# Agentic HR

基于 LangGraph 的中心调度型多 Agent 招聘评估系统，采用 `Supervisor Agent + Specialist Agents` 的 Hub-and-Spoke 架构，并结合 FastAPI、SQLite、React 控制舱与 Harness 工程体系，构建一个可解释、可回放、可持续验证的招聘评估原型。

项目定位不是替代 HR 做最终录用决策，而是把简历解析、岗位理解、匹配评分、风险提示、报告生成和人工复核串成一个可治理的 Agentic workflow。

## Current Status

当前版本已经完成核心闭环：

- Supervisor Agent 任务编排与状态路由
- Candidate Analyst Agent 候选人画像与信息缺口分析
- Job Analyst Agent 岗位重点与评估优先级分析
- Memory Agent 历史人工反馈检索
- Reporting Agent 匹配结果与风险结果汇总
- PDF/文本简历解析
- 简历与 JD 结构化抽取
- Pydantic Schema 校验与失败重试
- 分轨匹配评分与证据引用
- 人工复核风险预测
- Markdown 评估报告生成
- trace / replay / batch harness
- SQLite 持久化
- FastAPI API
- React 控制舱
- 邮件发送入口
- Docker 和 CI

仍建议作为后续生产化增强的部分：

- 多用户部署时将 SQLite 替换为 PostgreSQL
- 增加登录鉴权、角色权限和审计策略
- 对长耗时 OCR / LLM 批处理引入 Redis + 异步任务队列
- 用真实脱敏简历补充人工标注数据
- 接入 hosted tracing、监控和告警

## Architecture

系统采用 Supervisor-centered Hub-and-Spoke 架构：

- `Supervisor Agent` 负责请求识别、任务拆解、子 Agent 激活、状态路由
- `Resume Extraction Agent` 和 `JD Extraction Agent` 负责结构化抽取
- `Candidate Analyst Agent` 负责候选人优势、证据缺口和画像摘要
- `Job Analyst Agent` 负责岗位重点、评估维度和优先级
- `Memory Agent` 负责检索同类岗位历史人工反馈
- `Reporting Agent` 负责汇总匹配结果和风险结果，形成最终建议
- `Document Parser`、`Validator`、`Matcher`、`Risk Evaluator`、`Report Writer`、`Human Review` 作为确定性或半确定性节点，支撑整条工作流

工作流主链路如下：

`Supervisor -> Document Parser -> Resume Extractor -> JD Extractor -> Validator -> Candidate Analyst -> Job Analyst -> Memory Agent -> Rubric Selector -> Matcher -> Risk Evaluator -> Reporting Agent -> Report Writer -> Human Review`

架构图详见 [docs/architecture_diagrams.md](D:/项目/Agentic%20HR%20-%20基于%20Hub-and-Spoke%20架构与控制舱的智能评估系统/docs/architecture_diagrams.md)。

## Quick Start

安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

如需启用本地 OCR fallback，再安装可选 OCR 依赖：

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

关闭可选 LLM 报告增强以加快批量处理：

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

React 前端位于 `frontend/`，仅通过 HTTP 调用 FastAPI，不直接读取本地文件、不直接运行 Python workflow、不直接写 SQLite。

已支持：

- 后端健康检查与 SQLite 状态展示
- 文本简历批量评估
- PDF / 文本简历上传评估
- 最近批次、候选人记录、运行详情
- trace 时间线与 Markdown 报告预览
- 报告中的 Supervisor / Agent 协作摘要展示
- 人工复核提交
- 候选人报告邮件发送

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

当前模型目标是 `needs_human_review`，用于预测是否需要人工复核，而不是预测录用结果。

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

如果 LLM 关闭、配置缺失或请求失败，系统会回退到规则抽取和确定性报告。图片型 PDF 默认优先走 Vision LLM，必要时可以启用本地 OCR fallback。

## Harness And Evaluation

运行后端测试：

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

## Tool Boundary

可复用工具适配器位于 `tools/hr_tools.py`：

- `parse_resume_pdf`
- `extract_resume_profile`
- `extract_jd_profile`
- `run_batch_evaluation`
- `save_batch_report`
- `send_report_email`
