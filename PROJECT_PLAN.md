# Agentic HR Project Plan


本项目已经完成可本地演示、可放简历、可讲工程架构的版本。当前系统不是初学者 demo，而是生产导向工程原型：核心招聘评估链路可运行，控制舱已切换为 React + FastAPI，数据、评估、持久化、模型和 harness 均有落点。

已完成：

- LangGraph Hub-and-Spoke 主工作流：PDF/文本解析、简历抽取、JD 抽取、校验、匹配评分、风险评估、报告生成、人工复核。
- Harness 工程层：批量运行、trace、replay、报告质量检查、LLM 抽取评估、回归测试。
- PDF 鲁棒解析：文字型 PDF、图片型 PDF Vision LLM 路径、本地 OCR 可选、解析质量评分、人工复核标记。
- 校招、社招、实习分轨评分：避免用同一套权重评价所有候选人。
- 证据溯源与反关键词堆砌：技能命中会结合项目/经历证据影响置信度。
- 数据集与 ML：500 条合成结构化数据、标注规范、`needs_human_review` 风险目标、训练脚本、模型卡和本地可用模型。
- 服务与持久化：FastAPI 服务层、SQLite workflow/run/candidate/job/trace/report/review/batch/email delivery 表。
- React 控制舱：健康检查、批量文本评估、文件上传、批次归档、候选人详情、trace、报告预览、人工复核、邮件发送。
- 工程化：Dockerfile、GitHub Actions CI、后端测试、前端测试、构建命令、启动/停止脚本。

## 1. 项目定位

Agentic HR 是一个招聘评估辅助系统，不直接替代 HR 做录用或淘汰决策。系统提供结构化抽取、评分、风险提示、证据链、报告和人工复核工作台。

面试表述建议：

```text
我用 LangGraph 构建了 Hub-and-Spoke 多 Agent 招聘评估系统，
将 LLM 信息抽取、Pydantic 校验、规则评分、人工复核风险模型、
Human-in-the-Loop 审批和 Harness 评估体系整合为可追踪的端到端 HR 工作流。
```

## 2. 架构选择

### 2.1 为什么是中心化 Hub-and-Spoke

招聘评估天然是有顺序、有状态、有校验、有回退的业务流程。中心化 orchestrator 适合控制：

- 节点执行顺序。
- 状态对象传递。
- 条件分支和失败回退。
- 人工复核中断点。
- trace 和 replay。

各节点不互相随意调用，而是通过共享状态交接，降低不可控 agent 对话带来的复杂度。

### 2.2 Agent / Node 分工

- `pdf_parser`: 解析 PDF 或文本，输出原文、质量分和解析元信息。
- `resume_extractor`: 抽取候选人结构化 profile。
- `jd_extractor`: 抽取岗位结构化 profile。
- `validator`: 校验字段完整性和可用性。
- `matcher`: 分轨匹配评分并生成证据。
- `risk_assessor`: 预测是否需要人工复核。
- `report_writer`: 生成 Markdown 评估报告。
- `human_review`: 处理复核状态、反馈和记忆写入。

## 3. Harness 思想如何体现

项目不只实现 workflow，还实现了围绕 workflow 的工程 harness：

- 批量 runner：同一 JD 下批量评估候选人并排序。
- trace：记录每个节点输入输出摘要、错误和元信息。
- replay：使用已保存 payload 复现运行。
- evaluation：规则抽取、LLM 抽取和标准答案对比。
- report quality check：检查报告是否包含关键解释、风险和建议。
- tests：覆盖核心节点、工具、API、控制舱和数据/模型流程。

面试重点：Harness 是“让 agentic workflow 可测试、可回放、可评估、可观测”的工程外壳。

## 4. 记忆机制

短期记忆：

- LangGraph 状态对象保存当前 request 的候选人、JD、解析质量、匹配结果、风险、报告和 trace。
- 主要以 Python dict / Pydantic model / JSON payload 形式在节点间传递。

长期记忆：

- SQLite 保存 run、candidate、job、trace、report、review、batch、email delivery。
- 人工复核反馈可写入 JSONL，作为后续标注和偏好沉淀来源。
- 数据集使用 JSONL，便于人工标注、抽样检查和 Colab/本地训练。

## 5. 前后端架构

前端：

- React + TypeScript + Vite。
- 只调用 FastAPI，不直接导入 Python workflow。
- 负责 HR 工作台交互：批次、候选人、详情、复核、邮件。

后端：

- FastAPI 提供 API 边界。
- LangGraph workflow 由后端触发。
- SQLiteRunStore 负责本地持久化。
- 邮件发送、批量上传、报告查询都在后端处理。

API 示例：

- `POST /evaluations`
- `POST /batch-evaluations`
- `POST /batch-evaluations/uploads`
- `GET /runs`
- `GET /runs/{request_id}`
- `GET /traces/{request_id}`
- `GET /reports/{request_id}`
- `POST /reviews/{request_id}`
- `POST /emails/report`

## 6. 数据集与 ML

当前模型目标是 `needs_human_review`，不是录用预测。

数据设计：

- 候选人 JSONL：学历、专业、年限、技能、项目、期望薪资、候选人类型。
- 岗位 JSONL：岗位类型、技能要求、年限、学历偏好、薪资区间。
- 标签 JSONL：匹配分、风险原因、是否需要人工复核。

合成数据遵循更真实的分布：

- 工作年限 0 到 10 年，应届生占比更高。
- 期望薪资 8k 到 50k。
- 学历与期望薪资正相关。
- 技能、年限、岗位要求和风险标签联动生成。

模型：

- 本地训练脚本：`scripts/train_review_risk_model.py`
- 模型：`models/review_risk_model.json`
- 模型卡：`models/model_card_review_risk.md`

## 7. 并发与异步演进

当前本地版本采用同步 FastAPI 调用，足够支持面试 demo 和小批量本地运行。

生产化演进建议：

- FastAPI 接收请求后写入 job 表。
- Redis Queue / Celery / RQ 执行 OCR、LLM 和批量评估。
- 前端轮询或 WebSocket 查看 job 状态。
- 大文件上传走对象存储或受控文件目录。
- 节点级 trace 逐步写入数据库，避免长任务卡住无反馈。

面试表述：

```text
我在当前版本保留了同步路径，降低本地 demo 复杂度；
但架构边界已经分好，长耗时 OCR/LLM 节点可以自然迁移到 Redis 异步任务队列。
```

## 8. 生产化剩余优化

优先级建议：

1. 鉴权与权限：登录、HR/reviewer/admin 角色、API token。
2. PostgreSQL：替换 SQLite，支持并发查询和多用户。
3. Redis 异步队列：处理 OCR、LLM 和大批量简历。
4. 真实脱敏标注：补充合成数据，形成小规模人工标注闭环。
5. 观测性：结构化日志、trace 导出、失败率和耗时指标。
6. 前端细化：筛选、搜索、批次详情页、邮件投递历史页。
7. 安全合规：PII 脱敏、数据保留策略、审计日志。

## 9. 验证命令

后端测试：

```powershell
D:\python\python.exe -m pytest -q
```

前端测试与构建：

```powershell
cd frontend
npm test -- --run
npm run build
```

启动完整控制舱：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_control_cabin.ps1
```
